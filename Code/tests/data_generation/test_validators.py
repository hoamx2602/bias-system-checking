from copy import deepcopy

from src.data_generation.coverage import build_assignments, load_coverage_cells
from src.data_generation.dry_run import render_dry_run_family
from src.data_generation.validators import validate_family


def _fixture_family():
    assignment = build_assignments(load_coverage_cells(), 1, seed=42)[0]
    return render_dry_run_family(assignment)


def test_dry_run_family_passes_automated_gates():
    report = validate_family(_fixture_family())
    assert report.valid, [issue.to_dict() for issue in report.issues]


def test_label_leakage_is_rejected():
    family = _fixture_family()
    family["variants"][2]["text"] += " This is 30% bias."
    report = validate_family(family)
    assert not report.valid
    assert "LABEL_LEAKAGE" in {issue.code for issue in report.issues}


def test_changed_control_fact_is_rejected():
    family = deepcopy(_fixture_family())
    family["variants"][4]["control"]["invariant_facts"] = ["A changed fact"]
    report = validate_family(family)
    assert not report.valid
    assert "INVARIANT_FACT_CHANGED" in {issue.code for issue in report.issues}
