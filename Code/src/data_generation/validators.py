"""Offline quality gates applied before expensive AI judging."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .providers.base import load_json
from .models import LEGACY_INTENSITIES, REQUIRED_LEVELS, ValidationIssue, ValidationReport
from .config import GENERATION_ROOT


_LABEL_LEAKAGE = re.compile(
    r"\b(?:0|10|30|50|70|100)\s*%\s*(?:bias)?\b|\bbias\s*level\s*[0-5]\b",
    re.IGNORECASE,
)
_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE = re.compile(r"(?<!\d)(?:\+?\d[\d ()-]{7,}\d)(?!\d)")
_SECRET = re.compile(r"\b(?:sk-[A-Za-z0-9_-]{16,}|AIza[A-Za-z0-9_-]{20,})\b")


def _issue(issues: list[ValidationIssue], code: str, message: str, path: str = "") -> None:
    issues.append(ValidationIssue(code=code, message=message, path=path))


def validate_against_schema(
    instance: dict[str, Any],
    schema_path: str | Path,
    record_id: str,
) -> ValidationReport:
    schema = load_json(schema_path)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    issues = []
    for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.path)):
        path = ".".join(str(part) for part in error.path)
        issues.append(ValidationIssue(
            code="SCHEMA_VALIDATION_FAILED",
            message=error.message,
            path=path,
        ))
    return ValidationReport(record_id=record_id, valid=not issues, issues=issues)


def validate_family(family: dict[str, Any]) -> ValidationReport:
    family_id = str(family.get("family_id", "unknown"))
    issues: list[ValidationIssue] = []
    card = family.get("control_card")
    variants = family.get("variants")

    if not isinstance(card, dict):
        _issue(issues, "MISSING_CONTROL_CARD", "control_card must be an object", "control_card")
        card = {}
    if not isinstance(variants, list):
        _issue(issues, "MISSING_VARIANTS", "variants must be a list", "variants")
        variants = []
    if len(variants) != len(REQUIRED_LEVELS):
        _issue(issues, "INVALID_VARIANT_COUNT", "A family must contain exactly six variants", "variants")

    seen_ids: set[str] = set()
    levels: list[int] = []
    normalized_texts: set[str] = set()
    expected_criteria = card.get("objective_criteria", [])
    expected_facts = card.get("invariant_facts", [])
    expected_mechanisms = card.get("bias_mechanisms", [])

    for index, variant in enumerate(variants):
        path = f"variants[{index}]"
        if not isinstance(variant, dict):
            _issue(issues, "INVALID_VARIANT", "Variant must be an object", path)
            continue
        variant_id = str(variant.get("id", ""))
        if not variant_id or variant_id in seen_ids:
            _issue(issues, "DUPLICATE_VARIANT_ID", "Variant IDs must be non-empty and unique", f"{path}.id")
        seen_ids.add(variant_id)
        if variant.get("family_id") != family_id:
            _issue(issues, "FAMILY_ID_MISMATCH", "Variant family_id differs from the family", f"{path}.family_id")

        labels = variant.get("labels", {})
        level = labels.get("severity_level")
        if isinstance(level, int):
            levels.append(level)
            if labels.get("legacy_intensity") != LEGACY_INTENSITIES.get(level):
                _issue(issues, "INTENSITY_MISMATCH", "legacy_intensity does not match severity_level", f"{path}.labels")
            if labels.get("bias_present") != (level > 0):
                _issue(issues, "PRESENCE_MISMATCH", "bias_present does not match severity_level", f"{path}.labels")
        else:
            _issue(issues, "INVALID_SEVERITY", "severity_level must be an integer", f"{path}.labels.severity_level")
        if labels.get("bias_mechanisms") != expected_mechanisms:
            _issue(issues, "MECHANISM_MISMATCH", "Mechanisms must match the control card", f"{path}.labels.bias_mechanisms")

        control = variant.get("control", {})
        if control.get("objective_criteria") != expected_criteria:
            _issue(issues, "OBJECTIVE_FACT_CHANGED", "Objective criteria changed inside the family", f"{path}.control")
        if control.get("invariant_facts") != expected_facts:
            _issue(issues, "INVARIANT_FACT_CHANGED", "Invariant facts changed inside the family", f"{path}.control")

        text = str(variant.get("text", "")).strip()
        if len(text.split()) < 25:
            _issue(issues, "TEXT_TOO_SHORT", "Variant text must contain at least 25 words", f"{path}.text")
        if _LABEL_LEAKAGE.search(text):
            _issue(issues, "LABEL_LEAKAGE", "Variant text exposes a target bias label", f"{path}.text")
        if _EMAIL.search(text) or _PHONE.search(text) or _SECRET.search(text):
            _issue(issues, "POSSIBLE_PII_OR_SECRET", "Variant contains possible PII or a secret", f"{path}.text")
        normalized = " ".join(re.sub(r"[^a-z0-9 ]", " ", text.lower()).split())
        if normalized in normalized_texts:
            _issue(issues, "EXACT_TEXT_DUPLICATE", "Two variants normalize to the same text", f"{path}.text")
        normalized_texts.add(normalized)

    if sorted(levels) != list(REQUIRED_LEVELS):
        _issue(issues, "INVALID_LEVEL_SET", "Severity levels must be exactly 0 through 5", "variants")

    return ValidationReport(record_id=family_id, valid=not issues, issues=issues)


_V2_MANIFESTATION = {
    0: "none",
    1: "corrected_cue",
    2: "unequal_process",
    3: "material_contribution",
    4: "decision_override",
    5: "explicit_exclusion_or_manipulation",
}


def validate_generated_family_v2(
    family: dict[str, Any],
    control_card: dict[str, Any],
) -> ValidationReport:
    """Validate raw generation-v2 output before any model judge sees it."""
    family_id = str(family.get("family_id", "unknown"))
    schema_report = validate_against_schema(
        family,
        GENERATION_ROOT / "schemas" / "generated_family_v2.schema.json",
        family_id,
    )
    issues = list(schema_report.issues)
    variants = family.get("variants", [])
    status = family.get("generation_status")

    if family_id != control_card.get("family_id"):
        _issue(issues, "FAMILY_ID_MISMATCH", "Output family_id differs from the control card", "family_id")
    if status == "invalid_control_card":
        if variants:
            _issue(issues, "INVALID_FAILURE_PAYLOAD", "An invalid control card must return no variants", "variants")
        if not str(family.get("failure_reason") or "").strip():
            _issue(issues, "MISSING_FAILURE_REASON", "A failed generation needs a concise reason", "failure_reason")
        _issue(issues, "CONTROL_CARD_UNUSABLE", "Structured abstention is safe but is not usable generated data")
        return ValidationReport(record_id=family_id, valid=not issues, issues=issues)
    if status != "complete":
        _issue(issues, "INVALID_GENERATION_STATUS", "generation_status must be complete or invalid_control_card")
    if family.get("failure_reason") is not None:
        _issue(issues, "UNEXPECTED_FAILURE_REASON", "A complete family must have failure_reason=null", "failure_reason")
    if not isinstance(variants, list) or len(variants) != 6:
        _issue(issues, "INVALID_VARIANT_COUNT", "A complete family must contain exactly six variants", "variants")
        variants = variants if isinstance(variants, list) else []

    expected_facts = list(control_card.get("invariant_facts", []))
    allowed_criteria = set(control_card.get("objective_criteria", []))
    seen_levels: list[int] = []
    seen_ids: set[str] = set()

    for index, variant in enumerate(variants):
        path = f"variants[{index}]"
        if not isinstance(variant, dict):
            continue
        level = variant.get("severity_level")
        variant_id = variant.get("variant_id")
        if isinstance(level, int):
            seen_levels.append(level)
            if variant_id != f"v{level}":
                _issue(issues, "LEVEL_ID_MISMATCH", "variant_id must match severity_level", f"{path}.variant_id")
            if variant.get("mechanism_manifestation") != _V2_MANIFESTATION.get(level):
                _issue(issues, "MANIFESTATION_MISMATCH", "Manifestation does not match the level anchor", f"{path}.mechanism_manifestation")
            expected_effect = level >= 3
            if variant.get("bias_affects_decision") is not expected_effect:
                _issue(issues, "DECISION_CAUSALITY_MISMATCH", "Decision effect does not match the level anchor", f"{path}.bias_affects_decision")
        if not isinstance(variant_id, str) or variant_id in seen_ids:
            _issue(issues, "DUPLICATE_VARIANT_ID", "Variant IDs must be unique", f"{path}.variant_id")
        seen_ids.add(str(variant_id))

        text = str(variant.get("text", ""))
        word_count = len(text.split())
        if not 80 <= word_count <= 250:
            _issue(issues, "TEXT_LENGTH_OUT_OF_RANGE", "Variant must contain 80-250 words", f"{path}.text")
        if _LABEL_LEAKAGE.search(text):
            _issue(issues, "LABEL_LEAKAGE", "Variant text exposes a target bias label", f"{path}.text")
        if _EMAIL.search(text) or _PHONE.search(text) or _SECRET.search(text):
            _issue(issues, "POSSIBLE_PII_OR_SECRET", "Variant contains possible PII or a secret", f"{path}.text")

        applied = variant.get("criteria_applied", [])
        distorted = variant.get("criteria_distorted_or_ignored", [])
        for field, values in (("criteria_applied", applied), ("criteria_distorted_or_ignored", distorted)):
            if isinstance(values, list) and any(value not in allowed_criteria for value in values):
                _issue(issues, "UNKNOWN_OBJECTIVE_CRITERION", "Criterion was not supplied by the control card", f"{path}.{field}")
        if level == 0 and distorted:
            _issue(issues, "NEUTRAL_CRITERIA_DISTORTED", "Level 0 cannot distort or ignore objective criteria", f"{path}.criteria_distorted_or_ignored")

        checks = variant.get("invariant_fact_checks", [])
        checked_facts = [item.get("fact") for item in checks if isinstance(item, dict)] if isinstance(checks, list) else []
        if Counter(checked_facts) != Counter(expected_facts) or any(item.get("preserved") is not True for item in checks if isinstance(item, dict)):
            _issue(issues, "INVARIANT_FACT_CHECK_FAILED", "Every invariant fact must be copied exactly once and marked preserved", f"{path}.invariant_fact_checks")

        evidence = variant.get("evidence_candidates", [])
        if level == 0 and evidence:
            _issue(issues, "NEUTRAL_HAS_BIAS_EVIDENCE", "Level 0 evidence_candidates must be empty", f"{path}.evidence_candidates")
        if isinstance(level, int) and level > 0 and not evidence:
            _issue(issues, "MISSING_EVIDENCE", "Biased levels need at least one exact evidence span", f"{path}.evidence_candidates")
        if isinstance(evidence, list) and any(not isinstance(span, str) or span not in text for span in evidence):
            _issue(issues, "EVIDENCE_NOT_SUBSTRING", "Every evidence candidate must be an exact text substring", f"{path}.evidence_candidates")

    if sorted(seen_levels) != list(REQUIRED_LEVELS):
        _issue(issues, "INVALID_LEVEL_SET", "Severity levels must be exactly 0 through 5", "variants")
    return ValidationReport(record_id=family_id, valid=not issues, issues=issues)
