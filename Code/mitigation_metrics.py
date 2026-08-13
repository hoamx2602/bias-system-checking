"""Mitigation-quality metrics: does the pipeline actually remove the bias, and does
it keep talking about the same thing?

BLEU/ROUGE in app.py answer "how close is the output to one hand-written reference
answer". That needs a reference, so it only ever runs over the 8 questions in
config.EVALUATION_QUESTIONS. The metrics here need no reference at all: the trained
intensity regressor and type classifier score the generated mitigation directly, so
any dialogue in dataset/ can be used as an evaluation item.

Three signals, and they only mean something together:

  Bias Reduction (delta)   intensity(input) - intensity(mitigation)
  Content Preservation     cosine(input, mitigation) on the retrieval encoder
  Type Consistency         does the predicted bias type change after rewriting

A high delta on its own is not success. The generator can drive the intensity to
zero by quietly writing about something else, and the low content similarity is
what exposes it — see the "gamed" rate in the aggregate.

Caveat worth remembering when reading per-sample verdicts: the intensity regressor's
own validation MAE is ~0.126, so a single delta is noisy. The aggregate rates over
many samples are the trustworthy part; BIAS_REDUCTION_FLOOR below is set near that
error band so borderline pairs land in "unchanged" rather than being counted as wins.

Usage:
    # end-to-end: runs the real pipeline (one Gemma generation per sample)
    python mitigation_metrics.py --limit 12

    # cheap: re-score (input, mitigation) pairs that were already generated
    python mitigation_metrics.py --score-file evaluation_results/pairs.json
"""

import os
import re
import json
import random

import numpy as np

import config

# --- Verdict thresholds ---
# The intensity must move at least this much to count as a real change. Kept near the
# regressor's validation MAE (0.126) so noise does not get reported as mitigation.
BIAS_REDUCTION_FLOOR = 0.10
# Below this cosine similarity the mitigation is no longer about the same situation:
# the bias was removed by changing the subject, not by neutralising the language.
CONTENT_SIMILARITY_FLOOR = 0.55
# Inputs already this clean have no bias left to remove. They are reported separately
# so they cannot drag the reduction averages toward zero, and they double as controls:
# a clean input that comes back rewritten beyond recognition is a bug.
NEUTRAL_INPUT_CEILING = 0.15

# Bands for the per-band breakdown. Deliberately keyed on the *predicted* input
# intensity, not the dataset's version string: parse_bias_percentage() in train.py
# assigns a default 50% to ~30% of the corpus, so the ground-truth level labels are
# too noisy to bucket by.
INTENSITY_BANDS = [
    ("00-20", 0.0, 0.20),
    ("20-40", 0.20, 0.40),
    ("40-60", 0.40, 0.60),
    ("60-80", 0.60, 0.80),
    ("80-100", 0.80, 1.01),
]


def extract_mitigation(text):
    """Robustly extracts the Reframed Neutral Mitigation section from the full response."""
    if not text:
        return ""
    # 1. Try to split by markdown headers ###
    sections = re.split(r'###\s*', text)
    for section in sections:
        if not section.strip():
            continue
        lines = section.strip().split('\n')
        header = lines[0].lower()
        content = '\n'.join(lines[1:]).strip()
        if any(h in header for h in ['mitig', 'refram', 'neutral', '🩹', '🤝', 'reframed']):
            # Strip outer quotes if any
            content = re.sub(r'^["\'“’]|["\'”’]$', '', content).strip()
            return content

    # 2. Try line by line matching if no ### split succeeded
    lines = text.split('\n')
    mitigation_lines = []
    found = False
    for line in lines:
        if not found:
            # Check if line looks like a header for mitigation
            if any(h in line.lower() for h in ['mitig', 'refram', 'neutral', '🩹', '🤝', 'reframed']) and any(x in line for x in ['#', ':', 'Verdict', 'Analysis', 'Mitigation', 'Response']):
                found = True
                continue
        else:
            # If we already found the header, collect content until another header starts
            if line.strip().startswith('###') or (any(h in line.lower() for h in ['verdict', 'severity', 'analysis', 'contrast', '🚨', '🔍']) and len(line) < 50):
                break
            mitigation_lines.append(line)

    if found and mitigation_lines:
        content = '\n'.join(mitigation_lines).strip()
        content = re.sub(r'^["\'“’]|["\'”’]$', '', content).strip()
        return content

    # 3. Fallback: If there are multiple sections split by ###, return the last one
    if len(sections) > 1:
        last_section = sections[-1].strip()
        lines = last_section.split('\n')
        content = '\n'.join(lines[1:]).strip()
        content = re.sub(r'^["\'“’]|["\'”’]$', '', content).strip()
        return content

    # 4. Ultimate fallback: return clean text itself
    content = text.strip()
    content = re.sub(r'^["\'“’]|["\'”’]$', '', content).strip()
    return content


# --- Single-pair scoring ---

class JudgeModels:
    """A pinned pair of supervised heads used purely as a measuring instrument.

    Delta is the intensity model's *opinion* of a text, so retraining that model changes
    every delta even when the generator is untouched. Comparing "+33 pts before" with
    "+41 pts after" across a retrain therefore measures nothing: the ruler moved, not the
    generator. Pinning a judge keeps the ruler fixed so numbers stay comparable across
    dataset versions — including when a new domain such as Procurement is added.

    Expects the same layout as config.TRAINED_MODEL_DIR_*: <judge_dir>/intensity and
    <judge_dir>/type. Create a snapshot with pin_judge().
    """

    def __init__(self, judge_dir, device=None):
        # Imported lazily so this module stays importable (and unit-testable) in an
        # environment without transformers installed.
        import torch
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        from models import REVERSE_BIAS_TYPE_MAPPING

        self.judge_dir = judge_dir
        self._reverse_type_mapping = REVERSE_BIAS_TYPE_MAPPING
        self.device = device or getattr(config, "DEVICE", "cpu")

        intensity_dir = os.path.join(judge_dir, "intensity")
        type_dir = os.path.join(judge_dir, "type")
        for path in (intensity_dir, type_dir):
            if not os.path.isdir(path):
                raise RuntimeError(
                    f"Judge model not found at {path}. Snapshot the current production "
                    f"heads first:  python mitigation_metrics.py --pin-judge {judge_dir}"
                )

        if self.device in ("cuda", "mps"):
            load_kwargs = {"dtype": torch.float16, "device_map": "auto"}
        else:
            load_kwargs = {"dtype": torch.float32, "device_map": {"": "cpu"}}

        print(f"Loading pinned judge models from {judge_dir}...")
        self.intensity_tokenizer = AutoTokenizer.from_pretrained(intensity_dir)
        self.intensity_model = AutoModelForSequenceClassification.from_pretrained(
            intensity_dir, **load_kwargs)
        self.intensity_model.to(self.device)
        self.intensity_model.eval()

        self.type_tokenizer = AutoTokenizer.from_pretrained(type_dir)
        self.type_model = AutoModelForSequenceClassification.from_pretrained(
            type_dir, **load_kwargs)
        self.type_model.to(self.device)
        self.type_model.eval()

    def predict_bias(self, text):
        """Same contract as BiasAnalysisPipeline.predict_bias, so it drops in as a scorer."""
        import torch
        import torch.nn.functional as F

        inputs_int = self.intensity_tokenizer(
            text, padding=True, truncation=True, max_length=512, return_tensors="pt"
        ).to(self.device)
        with torch.no_grad():
            intensity = self.intensity_model(**inputs_int).logits.squeeze().item()
        predicted_intensity = max(0.0, min(1.0, float(intensity)))

        inputs_type = self.type_tokenizer(
            text, padding=True, truncation=True, max_length=512, return_tensors="pt"
        ).to(self.device)
        with torch.no_grad():
            logits = self.type_model(**inputs_type).logits
            pred_idx = torch.argmax(logits, dim=1).item()
            predicted_type_str = self._reverse_type_mapping.get(pred_idx, "11_misc")
            raw_probs = F.softmax(logits, dim=1).squeeze()
            type_probs = raw_probs.tolist() if raw_probs.dim() > 0 else [raw_probs.item()]

        return predicted_intensity, predicted_type_str, type_probs


def pin_judge(target_dir, force=False):
    """Snapshot the current production heads so they can keep serving as a fixed ruler.

    Run this *before* retraining on expanded data — once the production heads are
    overwritten the old ruler is gone and past baselines become uncomparable.
    """
    import shutil

    pairs = [
        (config.TRAINED_MODEL_DIR_INTENSITY, os.path.join(target_dir, "intensity")),
        (config.TRAINED_MODEL_DIR_TYPE, os.path.join(target_dir, "type")),
    ]
    for source, _ in pairs:
        if not os.path.isdir(source):
            raise RuntimeError(f"No trained model to pin at {source}. Run train.py first.")
    # Refuse to clobber an existing judge by accident: overwriting it silently would
    # invalidate every baseline already measured against it.
    for _, destination in pairs:
        if os.path.isdir(destination) and not force:
            raise RuntimeError(
                f"{destination} already exists. Pass force=True (--force) only if you are "
                f"certain no existing baseline depends on this judge."
            )
    for source, destination in pairs:
        if os.path.isdir(destination):
            shutil.rmtree(destination)
        shutil.copytree(source, destination)
        print(f"Pinned {source} -> {destination}")
    print(f"\nJudge snapshot ready. Score against it with:\n"
          f"  python mitigation_metrics.py --judge-dir {target_dir} --limit 50")
    return target_dir


def resolve_encoder(pipeline):
    """Return the retrieval encoder, forcing the lazy load.

    BiasVectorStore.load() leaves .model as None (vector_store.py:396); only
    _ensure_model() builds it, and that is normally triggered by search(). A code path
    that scores texts without ever searching — evaluate_pairs() — would otherwise find
    no encoder, score every similarity as 0.0, and report a 100% "gamed" rate off the
    back of it. Fail loudly instead: a missing encoder kills half the metric.
    """
    store = getattr(pipeline, "vector_store", None)
    if store is None:
        raise RuntimeError("Pipeline has no vector store; cannot measure content preservation.")
    if getattr(store, "model", None) is None and hasattr(store, "_ensure_model"):
        store._ensure_model()
    encoder = getattr(store, "model", None)
    if encoder is None:
        raise RuntimeError("Retrieval encoder unavailable; cannot measure content preservation.")
    return encoder


def cosine_similarity_texts(encoder, text_a, text_b):
    """Cosine similarity between two texts under the retrieval encoder.

    Zero is returned only for genuinely empty text — encode failures propagate, because
    a silent 0.0 here is indistinguishable from "the rewrite changed the subject".
    """
    if not text_a.strip() or not text_b.strip():
        return 0.0
    from sklearn.metrics.pairwise import cosine_similarity
    vec_a = encoder.encode(text_a)
    vec_b = encoder.encode(text_b)
    return float(cosine_similarity([vec_a], [vec_b])[0][0])


def classify_reduction(input_intensity, reduction):
    """Label how the intensity moved. 'neutral_input' means there was nothing to remove."""
    if input_intensity <= NEUTRAL_INPUT_CEILING:
        return "neutral_input"
    if reduction >= BIAS_REDUCTION_FLOOR:
        return "mitigated"
    if reduction <= -BIAS_REDUCTION_FLOOR:
        return "amplified"
    return "unchanged"


def score_pair(pipeline, input_text, mitigation_text, judge=None):
    """Score one (input, mitigation) pair. No reference answer required.

    Runs the supervised heads twice — once on the original text, once on the rewrite —
    and compares. Returns the three signals plus the derived verdicts.

    judge: a pinned JudgeModels to score with instead of the pipeline's own heads. The
    encoder for content similarity always comes from the pipeline, because it is frozen
    and never retrained — only the bias heads need pinning.
    """
    scorer = judge or pipeline
    input_intensity, input_type, _ = scorer.predict_bias(input_text)

    if not mitigation_text.strip():
        # The generator produced nothing extractable. Recording it as a zero-intensity
        # win would be flattering nonsense, so flag it instead.
        return {
            "input_intensity": float(input_intensity),
            "mitigation_intensity": None,
            "bias_reduction": None,
            "bias_reduction_relative": None,
            "content_similarity": 0.0,
            "content_preserved": False,
            "input_type": input_type,
            "mitigation_type": None,
            "type_changed": None,
            "reduction_verdict": "empty_mitigation",
        }

    mitigation_intensity, mitigation_type, _ = scorer.predict_bias(mitigation_text)

    reduction = input_intensity - mitigation_intensity
    relative = reduction / input_intensity if input_intensity > 0 else 0.0

    similarity = cosine_similarity_texts(resolve_encoder(pipeline), input_text, mitigation_text)

    return {
        "input_intensity": float(input_intensity),
        "mitigation_intensity": float(mitigation_intensity),
        "bias_reduction": float(reduction),
        "bias_reduction_relative": float(relative),
        "content_similarity": float(similarity),
        "content_preserved": bool(similarity >= CONTENT_SIMILARITY_FLOOR),
        "input_type": input_type,
        "mitigation_type": mitigation_type,
        "type_changed": bool(input_type != mitigation_type),
        "reduction_verdict": classify_reduction(input_intensity, reduction),
    }


# --- Aggregation ---

def _mean(values):
    return float(np.mean(values)) if len(values) else 0.0


def _median(values):
    return float(np.median(values)) if len(values) else 0.0


def _summarize(scores):
    """Core aggregate shared by the overall report and every breakdown slice."""
    # Pairs where the generator produced nothing are counted but cannot be averaged.
    usable = [s for s in scores if s["bias_reduction"] is not None]
    # Reduction only means something where there was bias to begin with.
    biased = [s for s in usable if s["reduction_verdict"] != "neutral_input"]
    neutral = [s for s in usable if s["reduction_verdict"] == "neutral_input"]

    verdict_counts = {"mitigated": 0, "unchanged": 0, "amplified": 0}
    for s in biased:
        verdict_counts[s["reduction_verdict"]] += 1

    summary = {
        "sample_count": len(scores),
        "empty_mitigation_count": len(scores) - len(usable),
        "biased_input_count": len(biased),
        "neutral_input_count": len(neutral),
        "reduction": {
            "mean_absolute": _mean([s["bias_reduction"] for s in biased]),
            "median_absolute": _median([s["bias_reduction"] for s in biased]),
            "mean_relative": _mean([s["bias_reduction_relative"] for s in biased]),
            "mean_input_intensity": _mean([s["input_intensity"] for s in biased]),
            "mean_mitigation_intensity": _mean([s["mitigation_intensity"] for s in biased]),
        },
        "content": {
            "mean_similarity": _mean([s["content_similarity"] for s in usable]),
            "median_similarity": _median([s["content_similarity"] for s in usable]),
            # Includes neutral inputs on purpose: a clean input that comes back
            # unrecognisable is as much a failure as a biased one.
            "preserved_rate": _mean([1.0 if s["content_preserved"] else 0.0 for s in usable]),
        },
        "reduction_verdicts": {
            "counts": verdict_counts,
            "denominator": "biased_input_count",
            "rates": {k: (v / len(biased) if biased else 0.0) for k, v in verdict_counts.items()},
        },
    }

    # The cross-check that gives the whole thing teeth: separate the pairs that lost
    # their bias while staying on topic from the ones that only looked successful.
    clean = [s for s in biased if s["reduction_verdict"] == "mitigated" and s["content_preserved"]]
    gamed = [s for s in biased if s["reduction_verdict"] == "mitigated" and not s["content_preserved"]]
    summary["cross_checks"] = {
        "clean_mitigation_count": len(clean),
        "clean_mitigation_rate": len(clean) / len(biased) if biased else 0.0,
        "gamed_count": len(gamed),
        "gamed_rate": len(gamed) / len(biased) if biased else 0.0,
        # Predicted on the rewrite. Note the type head has no "neutral" class, so on a
        # successfully neutralised text its output is close to arbitrary — read this as
        # a diagnostic, not a pass/fail.
        "type_changed_rate": _mean([1.0 if s["type_changed"] else 0.0 for s in biased]),
    }
    return summary


def aggregate(scores):
    """Overall report plus breakdowns by predicted input intensity and by bias type."""
    report = _summarize(scores)
    report["thresholds"] = {
        "bias_reduction_floor": BIAS_REDUCTION_FLOOR,
        "content_similarity_floor": CONTENT_SIMILARITY_FLOOR,
        "neutral_input_ceiling": NEUTRAL_INPUT_CEILING,
    }

    by_band = {}
    for name, low, high in INTENSITY_BANDS:
        slice_ = [s for s in scores if low <= s["input_intensity"] < high]
        if slice_:
            by_band[name] = _summarize(slice_)
    report["by_input_intensity_band"] = by_band

    by_type = {}
    for bias_type in sorted({s["input_type"] for s in scores if s.get("input_type")}):
        slice_ = [s for s in scores if s.get("input_type") == bias_type]
        by_type[bias_type] = _summarize(slice_)
    report["by_predicted_input_type"] = by_type

    return report


# --- Evaluation corpus ---

def load_dataset_dialogues(data_dir=config.DATA_DIR, limit=None, seed=42):
    """Sample dialogues from dataset/, stratified round-robin across the 11 type files.

    Only the dialogue text and its source are taken. The version string is carried
    along for traceability but is *not* used as a label — see INTENSITY_BANDS.
    """
    per_type = {}
    for filename in sorted(os.listdir(data_dir)):
        if not (filename.startswith("bias_data_for_type_") and filename.endswith(".json")):
            continue
        bias_type = filename.split("bias_data_for_type_")[1].split(".json")[0]
        with open(os.path.join(data_dir, filename), 'r', encoding='utf-8') as f:
            data = json.load(f)

        items = []
        for item in data:
            scenario = item["parameters"].get("scenario", "")
            for conversation in item["parameters"]["conversations"]:
                text = " ".join(conversation["dialogues"]).strip()
                if not text:
                    continue
                items.append({
                    "source_file": filename,
                    "dataset_bias_type": bias_type,
                    "scenario": scenario,
                    "version": conversation["version"],
                    "text": text,
                })
        per_type[bias_type] = items

    rng = random.Random(seed)
    for items in per_type.values():
        rng.shuffle(items)

    # Round-robin so a small --limit still covers every type instead of exhausting the
    # first file alphabetically.
    samples = []
    keys = sorted(per_type.keys())
    index = 0
    while any(index < len(per_type[k]) for k in keys):
        for k in keys:
            if index < len(per_type[k]):
                samples.append(per_type[k][index])
                if limit is not None and len(samples) >= limit:
                    return samples
        index += 1
    return samples


# --- Batch runners ---

def evaluate_pipeline(pipeline, samples, out_path=None, judge=None):
    """Run the real pipeline over samples and score each generated mitigation.

    One Gemma generation per sample, so this is the expensive path. Results are written
    after every item when out_path is given, so an interrupted run is not lost.
    """
    # Resolved up front so a missing encoder fails before spending generations, rather
    # than degrading every sample's similarity to zero.
    resolve_encoder(pipeline)
    meta = _scorer_meta(judge)

    scores = []
    records = []
    skipped = []

    for i, sample in enumerate(samples, start=1):
        label = f"[{i}/{len(samples)}] {sample['dataset_bias_type']} / {sample['version']}"
        print(f"\n=== {label} ===")
        try:
            result = pipeline.analyze(sample["text"])
            mitigation = extract_mitigation(result["answer"])
            score = score_pair(pipeline, sample["text"], mitigation, judge=judge)
        except Exception as e:
            # Recorded rather than swallowed: a run that quietly drops half its samples
            # would otherwise report averages that look like full coverage.
            print(f"Skipping sample due to: {e}")
            skipped.append({"version": sample["version"],
                            "dataset_bias_type": sample["dataset_bias_type"],
                            "error": str(e)})
            continue

        scores.append(score)
        records.append({
            "source_file": sample["source_file"],
            "dataset_bias_type": sample["dataset_bias_type"],
            "version": sample["version"],
            "input_text": sample["text"],
            "mitigation_text": mitigation,
            "metrics": score,
        })

        print(
            f"-> input {score['input_intensity']*100:.1f}% "
            f"-> mitigation {(score['mitigation_intensity'] or 0)*100:.1f}% "
            f"| delta {(score['bias_reduction'] or 0)*100:+.1f} pts "
            f"| similarity {score['content_similarity']:.3f} "
            f"| {score['reduction_verdict']}"
        )

        if out_path:
            _write_report(out_path, records, scores, skipped, meta)

    payload = {
        "scored_by": meta,
        "results": records,
        "skipped": skipped,
        "aggregate": aggregate(scores) if scores else {},
    }
    if out_path:
        _write_report(out_path, records, scores, skipped, meta)
    return payload


def evaluate_pairs(pipeline, pairs, out_path=None, judge=None):
    """Score pre-generated pairs — no text generation, so this runs in seconds.

    Each pair needs "input_text" and "mitigation_text"; anything else is passed through.
    Cheap enough to re-score an existing report under a different judge.
    """
    resolve_encoder(pipeline)
    meta = _scorer_meta(judge)

    scores = []
    records = []
    for i, pair in enumerate(pairs, start=1):
        input_text = pair.get("input_text") or pair.get("question") or ""
        mitigation = pair.get("mitigation_text")
        if mitigation is None:
            mitigation = extract_mitigation(pair.get("answer", ""))
        if not input_text.strip():
            continue

        score = score_pair(pipeline, input_text, mitigation, judge=judge)
        scores.append(score)
        records.append({**{k: v for k, v in pair.items() if k not in ("metrics",)},
                        "input_text": input_text,
                        "mitigation_text": mitigation,
                        "metrics": score})
        print(f"[{i}/{len(pairs)}] delta {(score['bias_reduction'] or 0)*100:+.1f} pts | "
              f"similarity {score['content_similarity']:.3f} | {score['reduction_verdict']}")

    payload = {
        "scored_by": meta,
        "results": records,
        "aggregate": aggregate(scores) if scores else {},
    }
    if out_path:
        _write_report(out_path, records, scores, meta=meta)
    return payload


def _scorer_meta(judge):
    """Provenance for the report: which heads produced these deltas.

    Recorded on every report because a delta is only comparable against another delta
    from the same scorer. Without this stamp a file of numbers is unattributable.
    """
    if judge is None:
        return {
            "scorer": "production",
            "intensity_model": config.TRAINED_MODEL_DIR_INTENSITY,
            "type_model": config.TRAINED_MODEL_DIR_TYPE,
            "comparable_across_retrains": False,
        }
    return {
        "scorer": "pinned_judge",
        "judge_dir": judge.judge_dir,
        "intensity_model": os.path.join(judge.judge_dir, "intensity"),
        "type_model": os.path.join(judge.judge_dir, "type"),
        "comparable_across_retrains": True,
    }


def _write_report(out_path, records, scores, skipped=None, meta=None):
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    payload = {
        "scored_by": meta or {},
        "results": records,
        "skipped": skipped or [],
        "aggregate": aggregate(scores) if scores else {},
    }
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=4, ensure_ascii=False)


def print_summary(aggregate_report, scored_by=None):
    """Human-readable digest of the aggregate."""
    if not aggregate_report:
        print("No samples scored.")
        return
    red = aggregate_report["reduction"]
    con = aggregate_report["content"]
    ver = aggregate_report["reduction_verdicts"]
    cro = aggregate_report["cross_checks"]

    print("\n" + "=" * 62)
    print("MITIGATION QUALITY SUMMARY")
    print("=" * 62)
    if scored_by:
        if scored_by.get("scorer") == "pinned_judge":
            print(f"Scored by               : pinned judge {scored_by['judge_dir']}"
                  f"  (comparable across retrains)")
        else:
            print("Scored by               : production heads"
                  "  (NOT comparable across retrains)")
    print(f"Samples scored          : {aggregate_report['sample_count']}"
          f"  (biased {aggregate_report['biased_input_count']},"
          f" neutral {aggregate_report['neutral_input_count']},"
          f" empty {aggregate_report['empty_mitigation_count']})")
    print("-- Bias Reduction (biased inputs only) --")
    print(f"  mean input intensity  : {red['mean_input_intensity']*100:.1f}%")
    print(f"  mean output intensity : {red['mean_mitigation_intensity']*100:.1f}%")
    print(f"  mean delta            : {red['mean_absolute']*100:+.1f} pts"
          f"  (median {red['median_absolute']*100:+.1f})")
    print(f"  mean relative         : {red['mean_relative']*100:+.1f}%")
    print(f"  mitigated / unchanged / amplified : "
          f"{ver['rates']['mitigated']*100:.0f}% / "
          f"{ver['rates']['unchanged']*100:.0f}% / "
          f"{ver['rates']['amplified']*100:.0f}%")
    print("-- Content Preservation --")
    print(f"  mean similarity       : {con['mean_similarity']:.3f}"
          f"  (median {con['median_similarity']:.3f})")
    print(f"  preserved rate        : {con['preserved_rate']*100:.0f}%")
    print("-- Cross-checks --")
    print(f"  clean mitigation rate : {cro['clean_mitigation_rate']*100:.0f}%"
          f"   (bias down AND on topic)")
    print(f"  gamed rate            : {cro['gamed_rate']*100:.0f}%"
          f"   (bias down BUT off topic)")
    print(f"  type changed rate     : {cro['type_changed_rate']*100:.0f}%")
    print("=" * 62 + "\n")


def main():
    import argparse
    import sys

    # pipeline.analyze() streams the generation to stdout, and the response opens with an
    # emoji heading. On Windows a redirected stdout defaults to cp1252, which cannot encode
    # it — every sample would die with a charmap error before it was ever scored.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--limit", type=int, default=12,
                        help="number of dataset dialogues to run end-to-end (default 12)")
    parser.add_argument("--seed", type=int, default=42, help="sampling seed")
    parser.add_argument("--score-file", default=None,
                        help="JSON file of pre-generated pairs to score instead of "
                             "running the pipeline (accepts rag_metrics.json shape)")
    parser.add_argument("--out", default=os.path.join(config.EVALUATION_RESULTS_DIR,
                                                      "mitigation_metrics.json"),
                        help="where to write the report")
    parser.add_argument("--judge-dir", default=None,
                        help="score with a pinned judge in this directory (expects "
                             "<dir>/intensity and <dir>/type) instead of the production "
                             "heads, keeping deltas comparable across retrains")
    parser.add_argument("--pin-judge", default=None, metavar="DIR",
                        help="snapshot the current production heads into DIR as a judge, "
                             "then exit. Do this BEFORE retraining on expanded data")
    parser.add_argument("--force", action="store_true",
                        help="allow --pin-judge to overwrite an existing judge")
    args = parser.parse_args()

    if args.pin_judge:
        pin_judge(args.pin_judge, force=args.force)
        return

    from models import get_analysis_pipeline
    pipeline = get_analysis_pipeline()
    judge = JudgeModels(args.judge_dir) if args.judge_dir else None

    if args.score_file:
        with open(args.score_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        pairs = data.get("results", data) if isinstance(data, dict) else data
        payload = evaluate_pairs(pipeline, pairs, out_path=args.out, judge=judge)
    else:
        samples = load_dataset_dialogues(limit=args.limit, seed=args.seed)
        print(f"Sampled {len(samples)} dialogues across "
              f"{len({s['dataset_bias_type'] for s in samples})} bias types.")
        print(f"Each sample requires one full generation on {config.DEVICE}.")
        payload = evaluate_pipeline(pipeline, samples, out_path=args.out, judge=judge)

    print_summary(payload["aggregate"], payload.get("scored_by"))
    print(f"Report saved to {args.out}")


if __name__ == "__main__":
    main()
