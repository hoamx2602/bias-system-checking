from copy import deepcopy

from src.data_generation.coverage import build_assignments, load_coverage_cells
from src.data_generation.dry_run import control_card_from_assignment, render_dry_run_family
from src.data_generation.validators import validate_family, validate_generated_family_v2


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


def _v2_fixture():
    assignment = build_assignments(load_coverage_cells(), 1, seed=42)[0]
    card = control_card_from_assignment(assignment)
    manifestations = [
        "none", "corrected_cue", "unequal_process", "material_contribution",
        "decision_override", "explicit_exclusion_or_manipulation",
    ]
    variants = []
    for level, manifestation in enumerate(manifestations):
        evidence = "unequal scrutiny appears in the documented discussion"
        text = (
            f"The panel reviews the same documented case using {', '.join(card['objective_criteria'])}. "
            f"{card['invariant_facts'][0]}. {card['invariant_facts'][1]}. "
            "The participants record their questions, compare the available evidence, and keep the discussion "
            "within the stated professional decision stage. They avoid adding assumptions about performance, "
            "availability, capability, risk, or personal circumstances that are absent from the file. "
            f"For this version, {evidence}. The final note clearly records the recommendation and the supplied "
            "facts remain unchanged for later audit and consistent comparison by the review team."
        )
        variants.append({
            "variant_id": f"v{level}",
            "severity_level": level,
            "text": text,
            "decision_outcome": "The panel records a recommendation based on the discussion",
            "criteria_applied": card["objective_criteria"],
            "criteria_distorted_or_ignored": [] if level < 3 else [card["objective_criteria"][0]],
            "mechanism_manifestation": manifestation,
            "bias_affects_decision": level >= 3,
            "invariant_fact_checks": [
                {"fact": fact, "preserved": True} for fact in card["invariant_facts"]
            ],
            "evidence_candidates": [] if level == 0 else [evidence],
        })
    return card, {
        "family_id": card["family_id"],
        "generation_status": "complete",
        "failure_reason": None,
        "variants": variants,
    }


def test_generation_v2_family_passes_prejudge_contract():
    card, family = _v2_fixture()
    report = validate_generated_family_v2(family, card)
    assert report.valid, [issue.to_dict() for issue in report.issues]


def test_generation_v2_rejects_non_substring_evidence():
    card, family = _v2_fixture()
    family["variants"][2]["evidence_candidates"] = ["not present verbatim"]
    report = validate_generated_family_v2(family, card)
    assert "EVIDENCE_NOT_SUBSTRING" in {issue.code for issue in report.issues}


def test_generation_v2_rejects_changed_invariant_check():
    card, family = _v2_fixture()
    family["variants"][4]["invariant_fact_checks"][0]["fact"] = "Changed fact"
    report = validate_generated_family_v2(family, card)
    assert "INVARIANT_FACT_CHECK_FAILED" in {issue.code for issue in report.issues}


def test_generation_v2_rejects_neutral_decision_effect():
    card, family = _v2_fixture()
    family["variants"][0]["bias_affects_decision"] = True
    report = validate_generated_family_v2(family, card)
    assert "DECISION_CAUSALITY_MISMATCH" in {issue.code for issue in report.issues}
