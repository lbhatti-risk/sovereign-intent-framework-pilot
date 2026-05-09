"""Deterministic policy engine for the Sovereign Intent Framework."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from manifest_engine import IntentManifest, compute_hash


def evaluate(
    action_request: dict[str, Any],
    manifest: IntentManifest,
    stored_hash: str,
) -> dict[str, Any]:
    """Evaluate an action request against a signed Intent Manifest.

    Rules are checked in order; the function returns on the first match.
    No LLM calls, no randomness — identical inputs always produce identical output.

    Returns keys: decision ("allow" | "deny" | "escalate"), rule_fired, reason,
    latency_ms.
    """
    start_ns = time.monotonic_ns()

    action = action_request["action"]
    target_env = action_request["target_environment"]

    # Rule 1 — hash mismatch
    if compute_hash(manifest) != stored_hash:
        result = ("deny", "HASH_MISMATCH", "manifest_tampered")

    # Rule 2 — expired
    elif _is_expired(manifest.expiry):
        result = ("deny", "EXPIRED", "manifest_expired")

    # Rule 3 — environment mismatch
    elif target_env != manifest.environment:
        result = ("deny", "ENVIRONMENT_MISMATCH", "environment_mismatch")

    # Rule 4 — prohibited action
    elif action in manifest.prohibited_actions:
        result = ("deny", "PROHIBITED_ACTION", "action_prohibited")

    # Rule 5 — requires human approval (checked before allowed_actions)
    elif action in manifest.requires_human_approval_before:
        result = ("escalate", "REQUIRES_HUMAN_APPROVAL", "human_approval_required")

    # Rule 6 — not in allowed actions
    elif action not in manifest.allowed_actions:
        result = ("deny", "NOT_IN_ALLOWED_ACTIONS", "action_not_allowed")

    # Rule 7 — all checks pass
    else:
        result = ("allow", "ALL_CHECKS_PASSED", "action_permitted")

    decision, rule_fired, reason = result
    latency_ms = round((time.monotonic_ns() - start_ns) / 1_000_000, 3)

    return {
        "decision": decision,
        "rule_fired": rule_fired,
        "reason": reason,
        "latency_ms": latency_ms,
    }


def _is_expired(expiry: str) -> bool:
    """Return True if expiry is strictly in the past relative to current UTC time."""
    expiry_dt = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
    return datetime.now(timezone.utc) > expiry_dt
