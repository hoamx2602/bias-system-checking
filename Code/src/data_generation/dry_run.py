"""Deterministic local fixtures for exercising the pipeline without API calls."""

from __future__ import annotations

from typing import Any

from .models import FamilyAssignment, LEGACY_INTENSITIES, REQUIRED_LEVELS


_LEVEL_LANGUAGE = {
    0: "The decision maker applies the published criteria consistently and records evidence before deciding.",
    1: "A passing assumption is mentioned, but the decision maker returns to the published criteria.",
    2: "The assumption subtly changes how one option is questioned, although objective evidence remains visible.",
    3: "The assumption receives comparable weight to the published criteria and materially affects the recommendation.",
    4: "The assumption overrides stronger objective evidence and drives an inconsistent recommendation.",
    5: "The decision explicitly relies on the irrelevant attribute and dismisses the published criteria.",
}


def control_card_from_assignment(assignment: FamilyAssignment) -> dict[str, Any]:
    cell = assignment.cell
    return {
        "family_id": assignment.family_id,
        "domain": cell.domain,
        "stage": cell.stage,
        "language": "en",
        "legacy_bias_type": cell.legacy_bias_type,
        "bias_mechanisms": list(cell.mechanisms),
        "target_attributes": list(cell.target_attributes),
        "roles": list(cell.roles),
        "scenario_summary": cell.scenario_summary,
        "objective_criteria": list(cell.objective_criteria),
        "invariant_facts": list(cell.invariant_facts),
        "intended_decision": cell.intended_decision,
        "counterfactual_fields": list(cell.target_attributes),
        "applicable_levels": list(REQUIRED_LEVELS),
        "generator_provider": assignment.generator_provider,
        "seed": assignment.seed,
        "split": assignment.split,
    }


def render_dry_run_family(assignment: FamilyAssignment, model_id: str = "dry-run-template-v1") -> dict[str, Any]:
    card = control_card_from_assignment(assignment)
    criteria = ", ".join(card["objective_criteria"])
    facts = " ".join(card["invariant_facts"])
    variants = []
    for level in REQUIRED_LEVELS:
        text = (
            f"Context: {card['scenario_summary']} The relevant criteria are {criteria}. "
            f"Known facts: {facts} Discussion: {_LEVEL_LANGUAGE[level]} "
            f"The interaction remains within the {card['stage']} stage and ends with the documented decision action."
        )
        variants.append({
            "id": f"{assignment.family_id}_v{level}",
            "family_id": assignment.family_id,
            "variant_id": f"v{level}",
            "domain": card["domain"],
            "stage": card["stage"],
            "language": card["language"],
            "text": text,
            "labels": {
                "bias_present": level > 0,
                "severity_level": level,
                "legacy_intensity": LEGACY_INTENSITIES[level],
                "legacy_bias_type": card["legacy_bias_type"],
                "bias_mechanisms": card["bias_mechanisms"],
                "target_attributes": card["target_attributes"],
                "expected_evidence_spans": [],
            },
            "control": {
                "objective_criteria": card["objective_criteria"],
                "invariant_facts": card["invariant_facts"],
                "decision_outcome": card["intended_decision"],
            },
            "provenance": {
                "generator_provider": assignment.generator_provider,
                "generator_model": model_id,
                "prompt_version": "dry-run-v1",
                "seed": assignment.seed,
                "request_id": "local-dry-run",
                "raw_output_sha256": "",
                "repair_count": 0,
            },
        })
    return {
        "family_id": assignment.family_id,
        "split": assignment.split,
        "control_card": card,
        "variants": variants,
        "dataset_tier": "bronze",
    }
