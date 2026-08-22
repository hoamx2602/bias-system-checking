"""Shared, provider-neutral data structures for generation runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


REQUIRED_LEVELS = (0, 1, 2, 3, 4, 5)
LEGACY_INTENSITIES = {
    0: 0.0,
    1: 0.1,
    2: 0.3,
    3: 0.5,
    4: 0.7,
    5: 1.0,
}


@dataclass(frozen=True)
class CoverageCell:
    cell_id: str
    domain: str
    stage: str
    legacy_bias_type: str
    mechanisms: tuple[str, ...]
    target_attributes: tuple[str, ...]
    roles: tuple[str, ...]
    scenario_summary: str
    objective_criteria: tuple[str, ...]
    invariant_facts: tuple[str, ...]
    intended_decision: str
    priority: str = "normal"
    weight: int = 1
    human_review_priority: bool = False


@dataclass(frozen=True)
class FamilyAssignment:
    family_id: str
    cell: CoverageCell
    generator_provider: str
    seed: int
    split: str


@dataclass
class ValidationIssue:
    code: str
    message: str
    path: str = ""
    severity: str = "error"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationReport:
    record_id: str
    valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "valid": self.valid,
            "issues": [issue.to_dict() for issue in self.issues],
        }
