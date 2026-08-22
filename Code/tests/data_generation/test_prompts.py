from pathlib import Path


PROMPT_DIR = Path(__file__).resolve().parents[2] / "data_generation" / "prompts"


def test_generation_v2_has_all_behavioural_anchors_and_dynamic_card_last():
    prompt = (PROMPT_DIR / "generation_v2.txt").read_text(encoding="utf-8")
    for level in range(6):
        assert f"Level {level}" in prompt
    for concept in (
        "unequal scrutiny",
        "criteria",
        "decision",
        "legitimate",
        "invariant_fact_checks",
        "evidence_candidates",
        "invalid_control_card",
    ):
        assert concept in prompt
    assert prompt.rstrip().endswith("{{CONTROL_CARD_JSON}}")


def test_blind_judge_does_not_receive_generator_evidence_or_intended_level():
    prompt = (PROMPT_DIR / "judge_variant_v2.txt").read_text(encoding="utf-8")
    assert "do not know the generator, intended severity" in prompt
    assert "generator-proposed evidence" in prompt
    assert prompt.rstrip().endswith("{{BLIND_RECORD_JSON}}")


def test_arbiter_is_split_into_blind_assessment_and_decision_phases():
    assert (PROMPT_DIR / "arbiter_assessment_v2.txt").exists()
    assert (PROMPT_DIR / "arbiter_decision_v2.txt").exists()
