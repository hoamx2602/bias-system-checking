"""Command-line setup and offline dry-run tools for data generation."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from .artifacts import file_sha256, read_jsonl, utc_run_id, write_json, write_jsonl, write_native_artifact
from .config import (
    DEFAULT_COVERAGE_PATH,
    DEFAULT_PROVIDER_PATH,
    DEFAULT_QUALITY_PATH,
    DEFAULT_RUNS_DIR,
    GENERATION_ROOT,
    load_yaml,
    load_provider_settings,
)
from .coverage import build_assignments, load_coverage_cells
from .dry_run import control_card_from_assignment, render_dry_run_family
from .providers import get_adapter
from .providers.base import load_json
from .quality import evaluate_acceptance_gate
from .validators import validate_against_schema, validate_family, validate_generated_family_v2


def _enabled_providers(settings: dict[str, Any]) -> tuple[str, ...]:
    providers = tuple(name for name, value in settings.items() if value.enabled)
    if not providers:
        raise RuntimeError("No generation provider is enabled")
    return providers


def _load_prompt(name: str = "generation_v2.txt") -> str:
    return (GENERATION_ROOT / "prompts" / name).read_text(encoding="utf-8")


def _load_generation_schema() -> dict[str, Any]:
    schema = load_json(GENERATION_ROOT / "schemas" / "generated_family_v2.schema.json")
    # Provider structured-output APIs need the schema object, not its documentation IDs.
    return {key: value for key, value in schema.items() if key not in ("$schema", "$id")}


def command_check_env(args: argparse.Namespace) -> int:
    settings = load_provider_settings(args.providers)
    print("Provider environment check (secret values are never displayed):")
    missing = 0
    for name, provider in settings.items():
        status = "ready" if provider.has_api_key else "missing-key"
        if provider.enabled and not provider.has_api_key:
            missing += 1
        print(
            f"- {name:10} enabled={str(provider.enabled).lower():5} "
            f"key={status:11} generator={provider.generator_model} judge={provider.judge_model}"
        )
    if missing:
        print(f"\n{missing} enabled provider(s) need API keys before a live smoke test.")
        return 2
    print("\nAll enabled providers have API keys configured.")
    return 0


def command_plan(args: argparse.Namespace) -> int:
    cells = load_coverage_cells(args.coverage)
    settings = load_provider_settings(args.providers)
    assignments = build_assignments(
        cells,
        total_families=args.families,
        providers=_enabled_providers(settings),
        seed=args.seed,
    )
    by_domain = Counter(item.cell.domain for item in assignments)
    by_provider = Counter(item.generator_provider for item in assignments)
    by_split = Counter(item.split for item in assignments)
    by_cell = Counter(item.cell.cell_id for item in assignments)
    payload = {
        "families": len(assignments),
        "dialogue_variants": len(assignments) * 6,
        "by_domain": dict(sorted(by_domain.items())),
        "by_provider": dict(sorted(by_provider.items())),
        "by_split": dict(sorted(by_split.items())),
        "by_cell": dict(sorted(by_cell.items())),
    }
    print(json.dumps(payload, indent=2))
    return 0


def _build_request_artifacts(
    cards: list[dict[str, Any]],
    settings: dict[str, Any],
    output_dir: Path,
) -> list[dict[str, Any]]:
    prompt = _load_prompt()
    schema = _load_generation_schema()
    artifacts = []
    for provider_name, provider in settings.items():
        provider_cards = [card for card in cards if card["generator_provider"] == provider_name]
        if not provider.enabled or not provider_cards:
            continue
        adapter = get_adapter(provider_name, provider.generator_model)
        artifact = adapter.build_artifact(provider_cards, prompt, schema)
        suffix = ".jsonl" if artifact.format == "jsonl" else ".json"
        path = write_native_artifact(output_dir / f"{provider_name}_generation_requests{suffix}", artifact)
        artifacts.append({
            "provider": provider_name,
            "model": provider.generator_model,
            "batch_endpoint": provider.batch_endpoint,
            "record_count": len(artifact.records),
            "path": str(path),
            "sha256": file_sha256(path),
        })
    return artifacts


def command_dry_run(args: argparse.Namespace) -> int:
    run_id = args.run_id or utc_run_id("dry-run")
    run_dir = Path(args.output_dir) / run_id
    if run_dir.exists():
        raise RuntimeError(f"Run directory already exists; choose another --run-id: {run_dir}")

    cells = load_coverage_cells(args.coverage)
    settings = load_provider_settings(args.providers)
    assignments = build_assignments(
        cells,
        total_families=args.families,
        providers=_enabled_providers(settings),
        seed=args.seed,
    )
    cards = [control_card_from_assignment(item) for item in assignments]
    families = [
        render_dry_run_family(item, settings[item.generator_provider].generator_model)
        for item in assignments
    ]
    card_schema_path = GENERATION_ROOT / "schemas" / "control_card.schema.json"
    card_reports = [
        validate_against_schema(card, card_schema_path, card["family_id"])
        for card in cards
    ]
    reports = [validate_family(family) for family in families]

    cards_path = write_jsonl(run_dir / "control_cards.jsonl", cards)
    bronze_path = write_jsonl(run_dir / "bronze.jsonl", families)
    validation_path = write_jsonl(run_dir / "validation.jsonl", (report.to_dict() for report in reports))
    request_artifacts = _build_request_artifacts(cards, settings, run_dir / "requests")
    invalid_card_count = sum(not report.valid for report in card_reports)
    invalid_count = sum(not report.valid for report in reports)
    manifest = {
        "run_id": run_id,
        "mode": "dry-run",
        "seed": args.seed,
        "family_count": len(families),
        "variant_count": len(families) * 6,
        "valid_family_count": len(families) - invalid_count,
        "invalid_family_count": invalid_count,
        "invalid_control_card_count": invalid_card_count,
        "provider_counts": dict(Counter(item.generator_provider for item in assignments)),
        "split_counts": dict(Counter(item.split for item in assignments)),
        "artifacts": {
            "control_cards": {"path": str(cards_path), "sha256": file_sha256(cards_path)},
            "bronze": {"path": str(bronze_path), "sha256": file_sha256(bronze_path)},
            "validation": {"path": str(validation_path), "sha256": file_sha256(validation_path)},
            "provider_requests": request_artifacts,
        },
        "live_api_calls": False,
    }
    manifest_path = write_json(run_dir / "manifest.json", manifest)
    print(f"Dry-run created: {run_dir}")
    print(f"Manifest: {manifest_path}")
    print(
        f"Families: {len(families)} | valid: {len(families) - invalid_count} "
        f"| invalid: {invalid_count} | invalid cards: {invalid_card_count}"
    )
    print("No external API calls were made.")
    return 1 if invalid_count or invalid_card_count else 0


def command_validate(args: argparse.Namespace) -> int:
    families = read_jsonl(args.input)
    reports = [validate_family(family) for family in families]
    invalid = [report for report in reports if not report.valid]
    if args.report:
        write_jsonl(args.report, (report.to_dict() for report in reports))
    print(f"Validated {len(reports)} families: {len(reports) - len(invalid)} valid, {len(invalid)} invalid")
    for report in invalid[:10]:
        codes = ", ".join(issue.code for issue in report.issues)
        print(f"- {report.record_id}: {codes}")
    return 1 if invalid else 0


def command_validate_v2(args: argparse.Namespace) -> int:
    families = read_jsonl(args.input)
    cards = {card["family_id"]: card for card in read_jsonl(args.control_cards)}
    reports = []
    for family in families:
        family_id = str(family.get("family_id", "unknown"))
        card = cards.get(family_id)
        if card is None:
            raise ValueError(f"No control card found for family_id={family_id}")
        reports.append(validate_generated_family_v2(family, card))
    invalid = [report for report in reports if not report.valid]
    if args.report:
        write_jsonl(args.report, (report.to_dict() for report in reports))
    print(f"Validated {len(reports)} v2 families: {len(reports) - len(invalid)} valid, {len(invalid)} invalid")
    return 1 if invalid else 0


def command_quality_report(args: argparse.Namespace) -> int:
    thresholds = load_yaml(args.thresholds)
    default_rate = (
        thresholds["prejudge_min_pass_rate"]
        if args.stage == "prejudge"
        else thresholds["silver_min_acceptance_rate"]
    )
    summary = evaluate_acceptance_gate(
        read_jsonl(args.input),
        stage=args.stage,
        minimum_rate=args.min_rate if args.min_rate is not None else float(default_rate),
        minimum_records=args.min_records if args.min_records is not None else int(thresholds["pilot_min_families"]),
    )
    payload = summary.to_dict()
    if args.output:
        write_json(args.output, payload)
    print(json.dumps(payload, indent=2))
    return 0 if summary.gate_passed else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.set_defaults(func=None)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--coverage", default=str(DEFAULT_COVERAGE_PATH))
    common.add_argument("--providers", default=str(DEFAULT_PROVIDER_PATH))

    subparsers = parser.add_subparsers(dest="command")
    check = subparsers.add_parser("check-env", parents=[common], help="Check provider config without showing secrets")
    check.set_defaults(func=command_check_env)

    plan = subparsers.add_parser("plan", parents=[common], help="Preview coverage, provider, and split allocation")
    plan.add_argument("--families", type=int, default=100)
    plan.add_argument("--seed", type=int, default=42)
    plan.set_defaults(func=command_plan)

    dry_run = subparsers.add_parser("dry-run", parents=[common], help="Create deterministic local fixtures and batch files")
    dry_run.add_argument("--families", type=int, default=6)
    dry_run.add_argument("--seed", type=int, default=42)
    dry_run.add_argument("--run-id")
    dry_run.add_argument("--output-dir", default=str(DEFAULT_RUNS_DIR))
    dry_run.set_defaults(func=command_dry_run)

    validate = subparsers.add_parser("validate", help="Validate generated-family JSONL")
    validate.add_argument("--input", required=True)
    validate.add_argument("--report")
    validate.set_defaults(func=command_validate)

    validate_v2 = subparsers.add_parser("validate-v2", help="Validate raw generation-v2 JSONL against control cards")
    validate_v2.add_argument("--input", required=True)
    validate_v2.add_argument("--control-cards", required=True)
    validate_v2.add_argument("--report")
    validate_v2.set_defaults(func=command_validate_v2)

    quality = subparsers.add_parser("quality-report", help="Enforce pre-judge or Silver acceptance gates")
    quality.add_argument("--input", required=True)
    quality.add_argument("--stage", required=True, choices=("prejudge", "silver"))
    quality.add_argument("--thresholds", default=str(DEFAULT_QUALITY_PATH))
    quality.add_argument("--min-rate", type=float)
    quality.add_argument("--min-records", type=int)
    quality.add_argument("--output")
    quality.set_defaults(func=command_quality_report)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.func is None:
        parser.print_help()
        return 2
    try:
        return int(args.func(args))
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
