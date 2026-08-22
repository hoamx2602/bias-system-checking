from src.data_generation.blinding import build_blind_family_packet
from src.data_generation.coverage import build_assignments, load_coverage_cells
from src.data_generation.dry_run import control_card_from_assignment


def test_family_judge_packet_hides_generator_labels_and_evidence():
    assignment = build_assignments(load_coverage_cells(), 1, seed=7)[0]
    card = control_card_from_assignment(assignment)
    family = {
        "family_id": card["family_id"],
        "variants": [
            {
                "variant_id": f"v{level}",
                "severity_level": level,
                "text": f"Standalone professional record number {level}",
                "decision_outcome": "A documented decision is recorded",
                "evidence_candidates": ["generator hint"],
            }
            for level in range(6)
        ],
    }
    packet, private_mapping = build_blind_family_packet(family, card, seed=99)
    assert len(packet["records"]) == 6
    assert set(private_mapping.values()) == {f"v{level}" for level in range(6)}
    for record in packet["records"]:
        assert set(record) == {"record_id", "control_facts", "record_text"}
        assert record["record_id"].startswith("item_")
        assert "severity_level" not in record
        assert "evidence_candidates" not in record
