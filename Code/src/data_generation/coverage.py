"""Coverage-matrix parsing and leakage-safe family assignment."""

from __future__ import annotations

import hashlib
import random
from collections import Counter
from pathlib import Path
from typing import Any

from .config import DEFAULT_COVERAGE_PATH, load_yaml
from .models import CoverageCell, FamilyAssignment


VALID_DOMAINS = {"hr", "procurement"}
VALID_PRIORITIES = {"high", "normal", "low"}


def _tuple_of_strings(value: Any, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{field_name} must be a non-empty list of strings")
    return tuple(value)


def load_coverage_cells(path: str | Path = DEFAULT_COVERAGE_PATH) -> list[CoverageCell]:
    payload = load_yaml(path)
    cells_raw = payload.get("cells", [])
    if not isinstance(cells_raw, list) or not cells_raw:
        raise ValueError("coverage.yaml must contain a non-empty cells list")

    cells: list[CoverageCell] = []
    seen: set[str] = set()
    for item in cells_raw:
        if not isinstance(item, dict):
            raise ValueError("Each coverage cell must be an object")
        cell_id = str(item["cell_id"])
        if cell_id in seen:
            raise ValueError(f"Duplicate coverage cell: {cell_id}")
        seen.add(cell_id)
        domain = str(item["domain"]).lower()
        priority = str(item.get("priority", "normal")).lower()
        if domain not in VALID_DOMAINS:
            raise ValueError(f"Unsupported domain in {cell_id}: {domain}")
        if priority not in VALID_PRIORITIES:
            raise ValueError(f"Unsupported priority in {cell_id}: {priority}")

        cells.append(CoverageCell(
            cell_id=cell_id,
            domain=domain,
            stage=str(item["stage"]),
            legacy_bias_type=str(item["legacy_bias_type"]),
            mechanisms=_tuple_of_strings(item["mechanisms"], "mechanisms"),
            target_attributes=_tuple_of_strings(item["target_attributes"], "target_attributes"),
            roles=_tuple_of_strings(item["roles"], "roles"),
            scenario_summary=str(item["scenario_summary"]),
            objective_criteria=_tuple_of_strings(item["objective_criteria"], "objective_criteria"),
            invariant_facts=_tuple_of_strings(item["invariant_facts"], "invariant_facts"),
            intended_decision=str(item["intended_decision"]),
            priority=priority,
            weight=max(1, int(item.get("weight", 1))),
            human_review_priority=bool(item.get("human_review_priority", False)),
        ))
    return cells


def _stable_split(family_id: str) -> str:
    bucket = int(hashlib.sha256(family_id.encode("utf-8")).hexdigest()[:8], 16) % 100
    if bucket < 70:
        return "train"
    if bucket < 85:
        return "validation"
    return "test"


def build_assignments(
    cells: list[CoverageCell],
    total_families: int,
    providers: tuple[str, ...] = ("gemini", "openai", "anthropic"),
    seed: int = 42,
) -> list[FamilyAssignment]:
    if total_families < 1:
        raise ValueError("total_families must be positive")
    if not providers:
        raise ValueError("At least one provider is required")

    weighted_cells = [cell for cell in cells for _ in range(cell.weight)]
    rng = random.Random(seed)
    rng.shuffle(weighted_cells)
    counters: Counter[str] = Counter()
    provider_counts: Counter[str] = Counter()
    cell_provider_counts: dict[str, Counter[str]] = {}
    assignments: list[FamilyAssignment] = []

    for index in range(total_families):
        cell = weighted_cells[index % len(weighted_cells)]
        counters[cell.cell_id] += 1
        family_id = f"{cell.cell_id}_{counters[cell.cell_id]:05d}"
        # Balance inside each cell and globally so provider identity cannot become a label proxy.
        provider_offset = int(hashlib.sha256(cell.cell_id.encode()).hexdigest()[:4], 16)
        per_cell = cell_provider_counts.setdefault(cell.cell_id, Counter())
        tie_order = {
            provider: (position - provider_offset) % len(providers)
            for position, provider in enumerate(providers)
        }
        provider = min(
            providers,
            key=lambda name: (per_cell[name], provider_counts[name], tie_order[name]),
        )
        per_cell[provider] += 1
        provider_counts[provider] += 1
        assignments.append(FamilyAssignment(
            family_id=family_id,
            cell=cell,
            generator_provider=provider,
            seed=seed + index,
            split=_stable_split(family_id),
        ))
    return assignments
