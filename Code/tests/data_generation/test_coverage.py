from collections import Counter

from src.data_generation.coverage import build_assignments, load_coverage_cells


def test_assignments_are_unique_balanced_and_leakage_safe():
    cells = load_coverage_cells()
    assignments = build_assignments(cells, 120, seed=7)

    family_ids = [assignment.family_id for assignment in assignments]
    assert len(family_ids) == len(set(family_ids))
    assert {assignment.split for assignment in assignments} <= {"train", "validation", "test"}

    provider_counts = Counter(assignment.generator_provider for assignment in assignments)
    assert max(provider_counts.values()) - min(provider_counts.values()) <= len(cells)
    assert {assignment.cell.domain for assignment in assignments} == {"hr", "procurement"}


def test_assignment_is_deterministic():
    cells = load_coverage_cells()
    first = build_assignments(cells, 20, seed=42)
    second = build_assignments(cells, 20, seed=42)
    assert first == second
