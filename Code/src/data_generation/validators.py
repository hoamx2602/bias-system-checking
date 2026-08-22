"""Offline quality gates applied before expensive AI judging."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .providers.base import load_json
from .models import LEGACY_INTENSITIES, REQUIRED_LEVELS, ValidationIssue, ValidationReport


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
