"""Measured release gates for generation and judging runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class AcceptanceSummary:
    stage: str
    total: int
    accepted: int
    rejected: int
    acceptance_rate: float
    minimum_rate: float
    minimum_records: int
    gate_passed: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_acceptance_gate(
    records: Iterable[dict[str, Any]],
    *,
    stage: str,
    minimum_rate: float,
    minimum_records: int,
) -> AcceptanceSummary:
    """Calculate a fail-closed acceptance gate from validation or judge records."""
    if stage not in {"prejudge", "silver"}:
        raise ValueError("stage must be 'prejudge' or 'silver'")
    if not 0 <= minimum_rate <= 1:
        raise ValueError("minimum_rate must be between 0 and 1")
    if minimum_records < 1:
        raise ValueError("minimum_records must be at least 1")

    materialized = list(records)
    if stage == "prejudge":
        accepted = sum(record.get("valid") is True for record in materialized)
    else:
        accepted = sum(record.get("verdict") == "accept" for record in materialized)
    total = len(materialized)
    rate = accepted / total if total else 0.0
    passed = total >= minimum_records and rate >= minimum_rate
    return AcceptanceSummary(
        stage=stage,
        total=total,
        accepted=accepted,
        rejected=total - accepted,
        acceptance_rate=rate,
        minimum_rate=minimum_rate,
        minimum_records=minimum_records,
        gate_passed=passed,
    )
