"""Structured JSON audit log writer for the Sovereign Intent Framework."""

from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone
from typing import Any

from manifest_engine import IntentManifest

# Resolved once at import time; works regardless of the caller's cwd.
_EVIDENCE_DIR = pathlib.Path(__file__).parent.parent / "evidence"
_LOG_FILE = _EVIDENCE_DIR / "audit_log.jsonl"


def log_decision(
    action_request: dict[str, Any],
    manifest: IntentManifest,
    stored_hash: str,
    gateway_result: dict[str, Any],
    latency_ms: float,
) -> dict[str, Any]:
    """Build an audit log entry, append it to evidence/audit_log.jsonl, and return it."""
    entry: dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "manifest_id": manifest.task_id,
        "manifest_hash": stored_hash,
        "action_requested": action_request["action"],
        "target_environment": action_request["target_environment"],
        "target_resource": action_request["target_resource"],
        "requested_by": action_request["requested_by"],
        "decision": gateway_result["decision"],
        "rule_fired": gateway_result["rule_fired"],
        "reason": gateway_result["reason"],
        "latency_ms": latency_ms,
    }

    _EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    with _LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")

    return entry
