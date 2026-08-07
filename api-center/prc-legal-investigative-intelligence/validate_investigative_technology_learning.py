#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
MATRIX_PATH = HERE / "investigative-technology-intelligence-matrix.json"
LEDGER_PATH = HERE / "case-derived-investigative-capability-ledger.json"

VALID_LEVELS = {
    "CLAIM_ONLY",
    "PRIMARY_OBSERVED",
    "CORROBORATED_PRACTICE",
    "STRONGLY_CORROBORATED",
    "CONTESTED",
    "STALE_REVIEW_REQUIRED",
}
PRIMARY_HOST_SUFFIXES = (
    "spp.gov.cn",
    "court.gov.cn",
    "mps.gov.cn",
    "gov.cn",
    "ccdi.gov.cn",
    "moj.gov.cn",
    "npc.gov.cn",
    "ccg.gov.cn",
    "customs.gov.cn",
    "nia.gov.cn",
)
FORBIDDEN_KEYS = {
    "secret_tool_or_internal_system_name",
    "covert_collection_parameter",
    "surveillance_blind_spot",
    "target_selection_method",
    "investigation_evasion_method",
    "anti_forensics_method",
    "credential",
    "private_endpoint",
    "operational_tactical_playbook",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def expected_rollup_level(count: int) -> str:
    if count >= 2:
        return "CORROBORATED_PRACTICE"
    if count == 1:
        return "PRIMARY_OBSERVED"
    return "CLAIM_ONLY"


def main() -> int:
    matrix = load(MATRIX_PATH)
    ledger = load(LEDGER_PATH)

    assert matrix["schema_version"] == "prc-investigative-technology-intelligence-matrix-v1"
    assert ledger["schema_version"] == "prc-case-derived-investigative-capability-ledger-v1"
    assert matrix["safety_boundary"]["investigation_evasion"] is False
    assert matrix["safety_boundary"]["anti_forensics"] is False
    assert matrix["safety_boundary"]["covert_surveillance_implementation_details"] is False
    assert matrix["iteration_governance"]["single_case_cannot_establish_general_capability"] is True
    assert matrix["iteration_governance"]["contradictions_are_preserved"] is True
    assert matrix["iteration_governance"]["case_outcome_can_downgrade_prior_inference"] is True

    capabilities = matrix["technology_domains"]
    capability_ids = [row["capability_id"] for row in capabilities]
    assert len(capability_ids) >= 18
    assert len(capability_ids) == len(set(capability_ids))
    required = {
        "network-crime-investigation",
        "electronic-data-forensics",
        "network-log-and-connection-evidence",
        "online-cloud-platform-evidence",
        "data-intelligence-and-correlation",
        "video-image-investigation",
        "audio-voice-evidence",
        "forensic-medicine-and-dna",
        "technical-evidence-specialist-review",
        "technical-investigation-legal-category",
    }
    assert required <= set(capability_ids)

    observations = ledger["observations"]
    observation_ids = [row["observation_id"] for row in observations]
    fingerprints = [row["source_fingerprint"] for row in observations]
    assert len(observations) >= 4
    assert len(observation_ids) == len(set(observation_ids))
    assert len(fingerprints) == len(set(fingerprints))

    support_counts = {capability_id: 0 for capability_id in capability_ids}
    for row in observations:
        assert row["verification_status"] in VALID_LEVELS
        assert row["verification_status"] == "PRIMARY_OBSERVED"
        parsed = urlparse(row["primary_source_url"])
        assert parsed.scheme == "https"
        assert parsed.hostname
        assert any(parsed.hostname == suffix or parsed.hostname.endswith("." + suffix) for suffix in PRIMARY_HOST_SUFFIXES)
        assert row["capability_ids"]
        assert set(row["capability_ids"]) <= set(capability_ids)
        assert row["public_evidence_chain"]
        serialized = json.dumps(row, ensure_ascii=False).lower()
        for forbidden in FORBIDDEN_KEYS:
            assert forbidden not in serialized
        for capability_id in row["capability_ids"]:
            support_counts[capability_id] += 1
        for linked in row.get("corroborates_observation_ids") or []:
            assert linked in observation_ids
        for linked in row.get("conflicts_with_observation_ids") or []:
            assert linked in observation_ids

    rollups = ledger["capability_rollup"]
    rollup_ids = set()
    for row in rollups:
        capability_id = row["capability_id"]
        rollup_ids.add(capability_id)
        assert capability_id in capability_ids
        assert row["verification_level"] in VALID_LEVELS
        assert set(row["supporting_observation_ids"]) <= set(observation_ids)
        expected = expected_rollup_level(support_counts[capability_id])
        assert row["verification_level"] == expected
    for capability_id, count in support_counts.items():
        if count:
            assert capability_id in rollup_ids

    assert ledger["iteration_rules"]["append_only_observation_history"] is True
    assert ledger["iteration_rules"]["contradiction_creates_contested_state_not_deletion"] is True
    assert ledger["iteration_rules"]["law_or_standard_change_triggers_revalidation"] is True
    assert ledger["iteration_rules"]["single_case_never_equals_nationwide_generalization"] is True

    print(json.dumps({
        "status": "PASS",
        "capability_count": len(capability_ids),
        "observation_count": len(observations),
        "rollup_count": len(rollups),
        "network_investigation_present": "network-crime-investigation" in capability_ids,
        "case_learning_present": True,
        "reviewable": True,
        "verifiable": True,
        "absorbable": True,
        "iterable": True,
        "secret_operational_details": False
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
