"""Build judge packets without leaking generator labels or proposed evidence."""

from __future__ import annotations

import hashlib
import random
from typing import Any


def _control_view(control_card: dict[str, Any]) -> dict[str, Any]:
    return {
        "domain": control_card["domain"],
        "stage": control_card["stage"],
        "roles": control_card["roles"],
        "scenario_summary": control_card["scenario_summary"],
        "objective_criteria": control_card["objective_criteria"],
        "invariant_facts": control_card["invariant_facts"],
        "intended_decision_action": control_card["intended_decision"],
    }


def build_blind_variant_packet(
    variant: dict[str, Any],
    control_card: dict[str, Any],
    *,
    opaque_id: str,
) -> dict[str, Any]:
    """Expose only evidence a blind variant judge is allowed to use."""
    return {
        "record_id": opaque_id,
        "control_facts": _control_view(control_card),
        "record_text": variant["text"],
    }


def build_blind_family_packet(
    family: dict[str, Any],
    control_card: dict[str, Any],
    *,
    seed: int,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Randomize variants and return a private opaque-ID-to-variant-ID mapping."""
    shuffled = list(family["variants"])
    random.Random(seed).shuffle(shuffled)
    records = []
    private_mapping: dict[str, str] = {}
    for index, variant in enumerate(shuffled):
        digest = hashlib.sha256(
            f"{family['family_id']}:{seed}:{index}".encode("utf-8")
        ).hexdigest()[:10]
        opaque_id = f"item_{digest}"
        private_mapping[opaque_id] = variant["variant_id"]
        records.append(build_blind_variant_packet(variant, control_card, opaque_id=opaque_id))
    return {
        "family_id": family["family_id"],
        "control_facts": _control_view(control_card),
        "records": records,
    }, private_mapping
