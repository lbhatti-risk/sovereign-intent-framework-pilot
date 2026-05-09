import sys
import dataclasses
import json
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

import pytest
from freezegun import freeze_time

from agent_simulator import BASE_MANIFEST
from manifest_engine import IntentManifest, canonicalise, compute_hash
from gateway import evaluate


@pytest.fixture()
def base_manifest() -> IntentManifest:
    """TASK-1842 manifest with a far-future expiry so it never expires during tests."""
    return dataclasses.replace(BASE_MANIFEST, expiry="2099-12-31T23:59:59Z")


# ---------------------------------------------------------------------------
# manifest_engine
# ---------------------------------------------------------------------------

def test_hash_is_deterministic(base_manifest):
    assert compute_hash(base_manifest) == compute_hash(base_manifest)


def test_hash_changes_on_mutation(base_manifest):
    mutated = dataclasses.replace(base_manifest, authorised_objective="DROP ALL TABLES")
    assert compute_hash(mutated) != compute_hash(base_manifest)


def test_canonicalisation_is_sorted(base_manifest):
    keys = list(json.loads(canonicalise(base_manifest)).keys())
    assert keys == sorted(keys)


# ---------------------------------------------------------------------------
# gateway — allow
# ---------------------------------------------------------------------------

def test_gateway_allows_valid_request(base_manifest):
    stored_hash = compute_hash(base_manifest)
    request = {
        "action": "read",
        "target_environment": "staging",
        "target_resource": "test-records-table",
        "requested_by": "sif-agent-v1",
    }
    result = evaluate(request, base_manifest, stored_hash)
    assert result["decision"] == "allow"


# ---------------------------------------------------------------------------
# gateway — deny paths
# ---------------------------------------------------------------------------

def test_gateway_denies_tampered_manifest(base_manifest):
    stored_hash = compute_hash(base_manifest)          # hash of original
    tampered = dataclasses.replace(
        base_manifest, authorised_objective="DROP ALL TABLES"
    )
    request = {
        "action": "read",
        "target_environment": "staging",
        "target_resource": "test-records-table",
        "requested_by": "sif-agent-v1",
    }
    result = evaluate(request, tampered, stored_hash)
    assert result["decision"] == "deny"
    assert result["reason"] == "manifest_tampered"


@freeze_time("2026-01-01T12:00:00Z")
def test_gateway_denies_expired_manifest(base_manifest):
    expired = dataclasses.replace(base_manifest, expiry="2000-01-01T00:00:00Z")
    stored_hash = compute_hash(expired)                # legitimately signed when expired
    request = {
        "action": "read",
        "target_environment": "staging",
        "target_resource": "test-records-table",
        "requested_by": "sif-agent-v1",
    }
    result = evaluate(request, expired, stored_hash)
    assert result["decision"] == "deny"
    assert result["reason"] == "manifest_expired"


def test_gateway_denies_environment_mismatch(base_manifest):
    stored_hash = compute_hash(base_manifest)
    request = {
        "action": "read",
        "target_environment": "production",   # manifest scoped to staging
        "target_resource": "prod-table",
        "requested_by": "sif-agent-v1",
    }
    result = evaluate(request, base_manifest, stored_hash)
    assert result["decision"] == "deny"
    assert result["reason"] == "environment_mismatch"


def test_gateway_denies_prohibited_action(base_manifest):
    stored_hash = compute_hash(base_manifest)
    request = {
        "action": "drop_table",              # in prohibited_actions
        "target_environment": "staging",
        "target_resource": "test-records-table",
        "requested_by": "sif-agent-v1",
    }
    result = evaluate(request, base_manifest, stored_hash)
    assert result["decision"] == "deny"
    assert result["reason"] == "action_prohibited"


def test_gateway_denies_out_of_scope(base_manifest):
    stored_hash = compute_hash(base_manifest)
    request = {
        "action": "deploy",                  # not in allowed or prohibited
        "target_environment": "staging",
        "target_resource": "test-records-table",
        "requested_by": "sif-agent-v1",
    }
    result = evaluate(request, base_manifest, stored_hash)
    assert result["decision"] == "deny"
    assert result["reason"] == "action_not_allowed"


# ---------------------------------------------------------------------------
# gateway — escalate
# ---------------------------------------------------------------------------

def test_gateway_escalates_approval_required(base_manifest):
    stored_hash = compute_hash(base_manifest)
    request = {
        "action": "delete",                  # in requires_human_approval_before
        "target_environment": "staging",
        "target_resource": "test-records-table",
        "requested_by": "sif-agent-v1",
    }
    result = evaluate(request, base_manifest, stored_hash)
    assert result["decision"] == "escalate"
    assert result["reason"] == "human_approval_required"
