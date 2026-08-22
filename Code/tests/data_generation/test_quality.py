from src.data_generation.quality import evaluate_acceptance_gate


def test_prejudge_gate_requires_ninety_percent_and_minimum_sample():
    records = [{"valid": index < 90} for index in range(100)]
    summary = evaluate_acceptance_gate(
        records, stage="prejudge", minimum_rate=0.90, minimum_records=100
    )
    assert summary.gate_passed
    assert summary.acceptance_rate == 0.9


def test_silver_gate_stops_below_eighty_five_percent():
    records = [{"verdict": "accept" if index < 84 else "repair"} for index in range(100)]
    summary = evaluate_acceptance_gate(
        records, stage="silver", minimum_rate=0.85, minimum_records=100
    )
    assert not summary.gate_passed


def test_gate_fails_when_pilot_is_too_small():
    summary = evaluate_acceptance_gate(
        [{"verdict": "accept"}] * 99,
        stage="silver",
        minimum_rate=0.85,
        minimum_records=100,
    )
    assert not summary.gate_passed
