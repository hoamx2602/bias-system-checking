"""Controlled ablation: did fixing the bias-level labels make the level model better?

The honest comparison is not "old MAE 0.126 vs new MAE", because the label fix changes the
*test set* as well as the training set. A model scored against noisy labels and a model
scored against clean labels are measured with different rulers, and the numbers do not
compare. Neither does reusing the existing production model: it was trained on a superset
that includes most of any new validation split, so its score would be inflated by having
seen the answers.

So both arms are trained here, from the same base checkpoint, with identical
hyperparameters, and evaluated on one shared validation set that neither arm trained on:

  val_clean      20% of the 1019 conversations that carry a real level annotation,
                 labelled with the corrected parser. Used to score BOTH arms.

  arm "legacy"   trains on the remaining 80% under the pre-fix labelling: 12 conversations
                 mislabelled by the parenthesis-only regex, plus the 423 unannotated
                 conversations glued to 50%, added to training exactly as before.

  arm "fixed"    trains on the same 80% with corrected labels and the unannotated
                 conversations dropped.

The only difference between the arms is label quality, so the delta is attributable to the
fix rather than to a different split, a different sample count in validation, or luck.

Because train.py's loader is shared, dropping the unannotated conversations also shrinks the
*type* classifier's training data by 29%. --stage type checks whether that costs accuracy.

Usage:
    python evaluate_level_labels.py --stage level    # the question that was asked
    python evaluate_level_labels.py --stage type     # side effect on the type head
    python evaluate_level_labels.py --stage all
"""

import os
import re
import json
import shutil

import numpy as np

from src import config
# train.py configures HF_HUB_OFFLINE and owns the dataset/metric helpers. Importing it
# keeps the label parser and metric definitions single-sourced with production training.
from src.training.train import (
    BIAS_TYPE_MAPPING,
    BiasMultiDataset,
    parse_bias_percentage,
    compute_level_metrics,
    compute_regression_metrics,
    compute_classification_metrics,
    WeightedTrainer,
)

from sklearn.model_selection import train_test_split
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
    EarlyStoppingCallback,
)

ABLATION_DIR = os.path.join(config.RESULTS_DIR, "label_ablation")
REPORT_PATH = os.path.join(config.EVALUATION_RESULTS_DIR, "level_label_ablation.json")


def legacy_parse_bias_percentage(version_string):
    """Frozen copy of the pre-fix parser, kept only so the ablation has a baseline.

    Do not use for training: the parenthesis-only regex mislabels "Version 6: 100% Bias"
    as 50%, and the final `return 50` invents a level for conversations that never had one.
    """
    percentage_match = re.search(r'\((\d+)%\)', version_string)
    if percentage_match:
        return int(percentage_match.group(1))
    if "Mixed Bias" in version_string:
        return 50
    if "No Bias" in version_string:
        return 0
    if any(indicator in version_string.lower() for indicator in ["extreme", "severe", "high"]):
        return 100
    return 50


def load_conversations(data_dir=config.DATA_DIR):
    """Every conversation with both labellings attached, so the arms share one corpus."""
    rows = []
    for filename in sorted(os.listdir(data_dir)):
        if not (filename.startswith("bias_data_for_type_") and filename.endswith(".json")):
            continue
        bias_type = filename.split("bias_data_for_type_")[1].split(".json")[0]
        type_label = BIAS_TYPE_MAPPING.get(bias_type, 10)
        with open(os.path.join(data_dir, filename), 'r', encoding='utf-8') as f:
            data = json.load(f)
        for item in data:
            for conversation in item["parameters"]["conversations"]:
                version = conversation["version"]
                fixed = parse_bias_percentage(version)
                rows.append({
                    "text": " ".join(conversation["dialogues"]),
                    "version": version,
                    "type_label": type_label,
                    "fixed_pct": fixed,
                    "legacy_pct": legacy_parse_bias_percentage(version),
                })
    return rows


def build_splits(rows, seed=42):
    """Split only the properly annotated rows; unannotated ones can never be validation.

    An unannotated conversation has no true level, so scoring against it would measure
    agreement with an invented number. They are available to the legacy arm's *training*
    set only, which is exactly how the pre-fix pipeline used them.
    """
    annotated = [r for r in rows if r["fixed_pct"] is not None]
    unannotated = [r for r in rows if r["fixed_pct"] is None]

    train_rows, val_rows = train_test_split(
        annotated, test_size=config.TEST_SPLIT_SIZE, random_state=seed
    )
    return train_rows, val_rows, unannotated


def _training_args(output_subdir, metric_for_best, greater_is_better):
    """Identical settings for both arms — the only variable under test is the labels."""
    return TrainingArguments(
        output_dir=os.path.join(ABLATION_DIR, output_subdir),
        num_train_epochs=config.TRAIN_EPOCHS,
        learning_rate=config.LEARNING_RATE,
        per_device_train_batch_size=config.TRAIN_BATCH_SIZE,
        per_device_eval_batch_size=config.EVAL_BATCH_SIZE,
        warmup_ratio=0.1,
        weight_decay=config.WEIGHT_DECAY,
        logging_dir=os.path.join(config.LOGS_DIR, "label_ablation", output_subdir),
        logging_steps=config.LOGGING_STEPS,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model=metric_for_best,
        greater_is_better=greater_is_better,
        save_total_limit=1,
        bf16=(config.DEVICE == "cuda"),
        dataloader_pin_memory=False,
        remove_unused_columns=False,
        dataloader_num_workers=2,
        report_to="none",
        seed=42,
    )


def run_level_arm(name, tokenizer, train_texts, train_labels, val_texts, val_labels):
    """Train one intensity regressor and score it on the shared clean validation set."""
    print("\n" + "=" * 70)
    print(f"LEVEL ARM '{name}': {len(train_texts)} train / {len(val_texts)} val")
    print("=" * 70)

    train_dataset = BiasMultiDataset(train_texts, train_labels, tokenizer, is_regression=True)
    val_dataset = BiasMultiDataset(val_texts, val_labels, tokenizer, is_regression=True)

    model = AutoModelForSequenceClassification.from_pretrained(
        config.CLASSIFIER_MODEL, num_labels=1, cache_dir=os.environ.get("HF_HOME")
    )
    if config.DEVICE != "cpu":
        model.to(config.DEVICE)

    trainer = Trainer(
        model=model,
        args=_training_args(f"level_{name}", "mse", False),
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_regression_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=5)],
    )
    trainer.train()

    output = trainer.predict(val_dataset)
    predictions = np.asarray(output.predictions).squeeze()
    labels = np.asarray(output.label_ids).squeeze()

    metrics = compute_regression_metrics((predictions, labels))
    metrics.update(compute_level_metrics(labels, predictions))
    metrics["train_size"] = len(train_texts)
    metrics["epochs_run"] = float(trainer.state.epoch or 0)
    return metrics


def run_type_arm(name, tokenizer, train_texts, train_labels, val_texts, val_labels):
    """Train one type classifier — checks what shrinking the corpus costs the type head."""
    print("\n" + "=" * 70)
    print(f"TYPE ARM '{name}': {len(train_texts)} train / {len(val_texts)} val")
    print("=" * 70)

    train_dataset = BiasMultiDataset(train_texts, train_labels, tokenizer, is_regression=False)
    val_dataset = BiasMultiDataset(val_texts, val_labels, tokenizer, is_regression=False)

    model = AutoModelForSequenceClassification.from_pretrained(
        config.CLASSIFIER_MODEL, num_labels=11, cache_dir=os.environ.get("HF_HOME")
    )
    if config.DEVICE != "cpu":
        model.to(config.DEVICE)

    from sklearn.utils.class_weight import compute_class_weight
    class_weights = compute_class_weight(
        class_weight="balanced", classes=np.array(range(11)), y=train_labels
    )

    trainer = WeightedTrainer(
        class_weights=class_weights,
        model=model,
        args=_training_args(f"type_{name}", "accuracy", True),
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_classification_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=5)],
    )
    trainer.train()

    output = trainer.predict(val_dataset)
    metrics = compute_classification_metrics((output.predictions, output.label_ids))
    metrics["train_size"] = len(train_texts)
    metrics["epochs_run"] = float(trainer.state.epoch or 0)
    return metrics


def print_level_comparison(legacy, fixed):
    """Side-by-side on the metrics that answer the question."""
    rows = [
        ("Level exact accuracy", "level_exact_accuracy", "pct", True),
        ("Level adjacent accuracy", "level_adjacent_accuracy", "pct", True),
        ("Level QWK", "level_qwk", "raw", True),
        ("Mean level distance", "level_mean_distance", "raw", False),
        ("MAE", "mae", "raw", False),
        ("RMSE", "rmse", "raw", False),
        ("R2", "r2", "raw", True),
        ("Pearson r", "pearson_r", "raw", True),
        ("Spearman rho", "spearman_rho", "raw", True),
    ]
    print("\n" + "=" * 78)
    print("LEVEL MODEL — same clean validation set, only the training labels differ")
    print("=" * 78)
    print(f"{'Metric':<26}{'legacy labels':>16}{'fixed labels':>16}{'change':>16}")
    print("-" * 78)
    for title, key, fmt, higher_better in rows:
        a, b = legacy.get(key, 0.0), fixed.get(key, 0.0)
        if fmt == "pct":
            a_s, b_s, d_s = f"{a*100:.1f}%", f"{b*100:.1f}%", f"{(b-a)*100:+.1f} pts"
        else:
            a_s, b_s, d_s = f"{a:.4f}", f"{b:.4f}", f"{b-a:+.4f}"
        verdict = "better" if ((b > a) == higher_better) and abs(b - a) > 1e-9 else (
            "worse" if abs(b - a) > 1e-9 else "same")
        print(f"{title:<26}{a_s:>16}{b_s:>16}{d_s:>16}   {verdict}")
    print("-" * 78)
    print(f"{'train size':<26}{legacy.get('train_size',0):>16}{fixed.get('train_size',0):>16}")

    print("\nPer-level recall (fraction of each true level placed on that exact level):")
    print(f"{'level':<10}{'support':>9}{'legacy':>12}{'fixed':>12}{'change':>12}")
    legacy_levels = legacy.get("level_per_level", {})
    fixed_levels = fixed.get("level_per_level", {})
    for key in fixed_levels:
        support = fixed_levels[key]["support"]
        a = legacy_levels.get(key, {}).get("recall", 0.0)
        b = fixed_levels[key]["recall"]
        print(f"{key:<10}{support:>9}{a*100:>11.1f}%{b*100:>11.1f}%{(b-a)*100:>+11.1f}p")
    print("=" * 78 + "\n")


def print_type_comparison(legacy, fixed):
    print("\n" + "=" * 78)
    print("TYPE MODEL — side effect of dropping the unannotated conversations")
    print("=" * 78)
    print(f"{'Metric':<26}{'full corpus':>16}{'reduced corpus':>16}{'change':>16}")
    print("-" * 78)
    for title, key in [("Accuracy", "accuracy"), ("F1 macro", "f1_macro"),
                       ("F1 weighted", "f1_weighted"), ("Balanced accuracy", "balanced_accuracy"),
                       ("MCC", "mcc")]:
        a, b = legacy.get(key, 0.0), fixed.get(key, 0.0)
        print(f"{title:<26}{a*100:>15.1f}%{b*100:>15.1f}%{(b-a)*100:>+15.1f}p")
    print("-" * 78)
    print(f"{'train size':<26}{legacy.get('train_size',0):>16}{fixed.get('train_size',0):>16}")
    print("=" * 78 + "\n")


LEVEL_REPORT_KEYS = [
    ("Level exact accuracy", "level_exact_accuracy", True),
    ("Level adjacent accuracy", "level_adjacent_accuracy", True),
    ("Level QWK", "level_qwk", True),
    ("Mean level distance", "level_mean_distance", False),
    ("MAE", "mae", False),
    ("RMSE", "rmse", False),
    ("R2", "r2", True),
    ("Spearman rho", "spearman_rho", True),
]

TYPE_REPORT_KEYS = [
    ("Accuracy", "accuracy", True),
    ("F1 macro", "f1_macro", True),
    ("Balanced accuracy", "balanced_accuracy", True),
    ("MCC", "mcc", True),
]


def paired_summary(runs, keys, baseline_name, variant_name):
    """Per-seed paired differences, which is what actually answers "did it improve?".

    Pairing matters: each seed changes the split as well as the training run, so comparing
    two independent means conflates split variance with the effect. Differencing within a
    seed cancels the split, leaving the label change. The spread of those differences is
    the honest error bar — a single run cannot produce one, which is why one seed gave
    "worse" and a rerun of the same seed gave "better".
    """
    summary = {}
    for _, key, higher_better in keys:
        base = [r[baseline_name].get(key, 0.0) for r in runs]
        variant = [r[variant_name].get(key, 0.0) for r in runs]
        diffs = [v - b for v, b in zip(variant, base)]
        wins = sum(1 for d in diffs if (d > 0) == higher_better and d != 0)
        summary[key] = {
            "baseline_values": base,
            "variant_values": variant,
            "baseline_mean": float(np.mean(base)),
            "variant_mean": float(np.mean(variant)),
            "paired_diffs": diffs,
            "paired_diff_mean": float(np.mean(diffs)),
            "paired_diff_std": float(np.std(diffs, ddof=1)) if len(diffs) > 1 else None,
            "variant_wins": wins,
            "seeds": len(runs),
            "higher_is_better": higher_better,
        }
    return summary


def print_paired_summary(title, summary, keys, baseline_label, variant_label, pct_keys=()):
    n = next(iter(summary.values()))["seeds"] if summary else 0
    print("\n" + "=" * 92)
    print(f"{title} — paired over {n} seed(s)")
    print("=" * 92)
    print(f"{'Metric':<26}{baseline_label:>14}{variant_label:>14}"
          f"{'paired diff':>22}{'wins':>8}{'verdict':>10}")
    print("-" * 92)
    for title_text, key, higher_better in keys:
        s = summary.get(key)
        if not s:
            continue
        scale = 100.0 if key in pct_keys else 1.0
        unit = "p" if key in pct_keys else ""
        mean_d = s["paired_diff_mean"] * scale
        std_d = s["paired_diff_std"]
        std_s = f" ± {std_d * scale:.3f}" if std_d is not None else ""
        # Inconclusive whenever the spread of the differences covers zero: the effect is
        # smaller than the run-to-run noise and no direction can be claimed.
        if std_d is None:
            verdict = "1 seed"
        elif abs(s["paired_diff_mean"]) > std_d:
            verdict = "better" if (s["paired_diff_mean"] > 0) == higher_better else "worse"
        else:
            verdict = "noise"
        print(f"{title_text:<26}{s['baseline_mean']*scale:>13.4f}{s['variant_mean']*scale:>14.4f}"
              f"{mean_d:>+14.4f}{std_s:>8}{unit}"
              f"{s['variant_wins']}/{s['seeds']:<6}{verdict:>10}")
    print("=" * 92 + "\n")


def main():
    import argparse
    import sys

    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--stage", choices=["level", "type", "all"], default="level")
    parser.add_argument("--seed", type=int, default=42, help="first seed")
    parser.add_argument("--seeds", type=int, default=1,
                        help="number of consecutive seeds to run per arm. One seed cannot "
                             "separate the effect from run-to-run noise; use 3 or more")
    parser.add_argument("--keep-checkpoints", action="store_true",
                        help="keep the ablation checkpoints instead of deleting them")
    args = parser.parse_args()

    rows = load_conversations()
    seeds = list(range(args.seed, args.seed + args.seeds))

    os.makedirs(config.EVALUATION_RESULTS_DIR, exist_ok=True)
    tokenizer = AutoTokenizer.from_pretrained(
        config.CLASSIFIER_MODEL, cache_dir=os.environ.get("HF_HOME"))

    # Merge into any existing report: the stages are run separately, and a fresh dict
    # would silently drop the other stage's results from the artifact.
    report = {}
    if os.path.exists(REPORT_PATH):
        try:
            with open(REPORT_PATH, 'r', encoding='utf-8') as f:
                report = json.load(f)
        except (ValueError, OSError):
            report = {}

    probe_train, probe_val, probe_unannotated = build_splits(rows, seed=args.seed)
    corrected = [r for r in rows
                 if r["fixed_pct"] is not None and r["legacy_pct"] != r["fixed_pct"]]
    print(f"Corpus: {len(rows)} conversations")
    print(f"  annotated   : {len(probe_train) + len(probe_val)}"
          f"  -> train {len(probe_train)} / val {len(probe_val)}")
    print(f"  unannotated : {len(probe_unannotated)}  (legacy arm trains on these as 50%)")
    print(f"  labels corrected by the regex fix: {len(corrected)}")
    print(f"  seeds       : {seeds}")

    report["design"] = {
        "validation_set": "20% of annotated conversations, corrected labels, "
                          "identical for both arms within a seed and unseen by both",
        "validation_size": len(probe_val),
        "annotated_total": len(probe_train) + len(probe_val),
        "unannotated_total": len(probe_unannotated),
        "labels_corrected_by_regex_fix": len(corrected),
        "seeds": seeds,
        "note": "Paired per-seed differences. A single seed cannot separate the label "
                "effect from run-to-run noise: seed 42 run twice moved level exact "
                "accuracy by 2.9 points and per-level recall by up to 42 points, both "
                "larger than the between-arm difference.",
    }

    def save():
        with open(REPORT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=4, ensure_ascii=False)

    level_runs = []
    type_runs = []

    for seed in seeds:
        train_rows, val_rows, unannotated = build_splits(rows, seed=seed)
        val_texts = [r["text"] for r in val_rows]
        print(f"\n########## SEED {seed} ##########")

        if args.stage in ("level", "all"):
            # Legacy arm reproduces the pre-fix training corpus: corrected rows reverted
            # to their old values, plus the unannotated rows pinned at 50%.
            legacy_texts = [r["text"] for r in train_rows] + [r["text"] for r in unannotated]
            legacy_labels = ([r["legacy_pct"] / 100.0 for r in train_rows] +
                             [r["legacy_pct"] / 100.0 for r in unannotated])
            fixed_texts = [r["text"] for r in train_rows]
            fixed_labels = [r["fixed_pct"] / 100.0 for r in train_rows]
            val_level_labels = [r["fixed_pct"] / 100.0 for r in val_rows]

            legacy_metrics = run_level_arm(f"legacy_s{seed}", tokenizer, legacy_texts,
                                           legacy_labels, val_texts, val_level_labels)
            fixed_metrics = run_level_arm(f"fixed_s{seed}", tokenizer, fixed_texts,
                                          fixed_labels, val_texts, val_level_labels)
            level_runs.append({"seed": seed,
                               "legacy_labels": legacy_metrics,
                               "fixed_labels": fixed_metrics})
            print_level_comparison(legacy_metrics, fixed_metrics)
            # Written after every seed so a multi-hour run is never lost.
            report["level"] = {
                "runs": level_runs,
                "paired": paired_summary(level_runs, LEVEL_REPORT_KEYS,
                                         "legacy_labels", "fixed_labels"),
            }
            save()

        if args.stage in ("type", "all"):
            # Type labels are unaffected by the fix; only the corpus size changes.
            full_texts = [r["text"] for r in train_rows] + [r["text"] for r in unannotated]
            full_labels = ([r["type_label"] for r in train_rows] +
                           [r["type_label"] for r in unannotated])
            reduced_texts = [r["text"] for r in train_rows]
            reduced_labels = [r["type_label"] for r in train_rows]
            val_type_labels = [r["type_label"] for r in val_rows]

            full_metrics = run_type_arm(f"full_s{seed}", tokenizer, full_texts, full_labels,
                                        val_texts, val_type_labels)
            reduced_metrics = run_type_arm(f"reduced_s{seed}", tokenizer, reduced_texts,
                                           reduced_labels, val_texts, val_type_labels)
            type_runs.append({"seed": seed,
                              "full_corpus": full_metrics,
                              "reduced_corpus": reduced_metrics})
            print_type_comparison(full_metrics, reduced_metrics)
            report["type"] = {
                "runs": type_runs,
                "paired": paired_summary(type_runs, TYPE_REPORT_KEYS,
                                         "full_corpus", "reduced_corpus"),
            }
            save()

    if level_runs:
        print_paired_summary("LEVEL MODEL", report["level"]["paired"], LEVEL_REPORT_KEYS,
                             "legacy", "fixed",
                             pct_keys={"level_exact_accuracy", "level_adjacent_accuracy"})
    if type_runs:
        print_paired_summary("TYPE MODEL", report["type"]["paired"], TYPE_REPORT_KEYS,
                             "full", "reduced",
                             pct_keys={"accuracy", "f1_macro", "balanced_accuracy", "mcc"})

    save()
    print(f"Ablation report saved to {REPORT_PATH}")

    if not args.keep_checkpoints and os.path.isdir(ABLATION_DIR):
        shutil.rmtree(ABLATION_DIR, ignore_errors=True)
        print(f"Removed ablation checkpoints in {ABLATION_DIR}")


if __name__ == "__main__":
    main()
