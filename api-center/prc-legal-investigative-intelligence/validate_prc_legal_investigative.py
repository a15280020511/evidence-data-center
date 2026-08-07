#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from prc_legal_investigative_task import CATALOG_PATH, execute

SAMPLES = {
    "catalog-capabilities": {},
    "source-catalog": {"topic": "electronic_evidence", "limit": 20},
    "source-route": {"source_id": "public-security-electronic-evidence-rules"},
    "joint-audit-plan": {"risk_topics": ["electronic_evidence", "personal_information", "geospatial"]},
}


def validate(operation: str) -> dict[str, object]:
    ticket = {
        "task_id": f"prc-legal-{operation}",
        "provider": "prc-legal-investigative-intelligence",
        "operation": operation,
        "objective": "zero-network catalog validation",
        "parameters": SAMPLES[operation],
        "data_policy": {"classification": "public", "contains_personal_data": False},
        "acceptance": {"timeout_seconds": 10, "max_response_bytes": 5000000},
    }
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        ticket_path = root / "ticket.json"
        output_dir = root / "output"
        ticket_path.write_text(json.dumps(ticket, ensure_ascii=False), encoding="utf-8")
        result = execute(ticket_path, output_dir)
        diagnostics = json.loads((output_dir / "diagnostics.json").read_text(encoding="utf-8"))
        if result != 0 or diagnostics["status"] != "INTEL_PRC_LEGAL_INVESTIGATIVE_COMPLETED":
            raise AssertionError(diagnostics)
        metadata = diagnostics["metadata"]
        assert metadata["network_used"] is False
        assert metadata["upstream_called"] is False
        assert metadata["request_count"] == 0
        assert metadata["automatic_login"] is False
        assert metadata["captcha_solving"] is False
        assert metadata["waf_bypass"] is False
        assert metadata["investigation_evasion"] is False
        assert diagnostics["secret_values_exposed"] is False
        assert diagnostics["model_calls"] == 0
        return {"status": "PASS", "operation": operation, "provider_catalog": CATALOG_PATH.name}


def main() -> int:
    receipts = [validate(operation) for operation in SAMPLES]
    print(json.dumps({"status": "PASS", "receipts": receipts}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
