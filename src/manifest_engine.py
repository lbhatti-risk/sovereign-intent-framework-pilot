"""Manifest creation, canonicalisation, and SHA-256 hashing for the Sovereign Intent Framework."""

from __future__ import annotations

import dataclasses
import hashlib
import json
from typing import Optional


@dataclasses.dataclass
class IntentManifest:
    """Declares the authorised scope, constraints, and identity of an agentic action."""

    task_id: str
    authorised_objective: str
    business_justification: str
    environment: str
    prohibited_environment: str
    data_classification: str
    allowed_actions: list[str]
    prohibited_actions: list[str]
    requires_human_approval_before: list[str]
    maximum_blast_radius: str
    rollback_requirement: str
    expiry: str  # ISO 8601 UTC
    authorised_by: str
    manifest_version: str = "1.0"
    parent_intent_hash: Optional[str] = None


def canonicalise(manifest: IntentManifest) -> str:
    """Serialise manifest to JSON with sorted keys and no whitespace.

    Produces identical bytes for identical manifest content (RFC 8785 equivalent).
    """
    return json.dumps(dataclasses.asdict(manifest), sort_keys=True, separators=(",", ":"))


def compute_hash(manifest: IntentManifest) -> str:
    """Return the SHA-256 hex digest of the canonicalised manifest."""
    canonical = canonicalise(manifest)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    sample = IntentManifest(
        task_id="TASK-001",
        authorised_objective="Export Q1 sales report to secure S3 bucket",
        business_justification="Monthly finance close — CFO approval on record",
        environment="production",
        prohibited_environment="development",
        data_classification="CONFIDENTIAL",
        allowed_actions=["s3:PutObject", "rds:Select"],
        prohibited_actions=["rds:DeleteTable", "iam:CreateUser", "s3:DeleteBucket"],
        requires_human_approval_before=["s3:PutObject"],
        maximum_blast_radius="single-bucket",
        rollback_requirement="delete-on-failure",
        expiry="2026-05-09T23:59:59Z",
        authorised_by="cfo@example.com",
        manifest_version="1.0",
        parent_intent_hash=None,
    )

    canonical = canonicalise(sample)
    digest = compute_hash(sample)

    print("=== Canonical JSON ===")
    print(canonical)
    print()
    print("=== SHA-256 Hash ===")
    print(digest)
    print()
    print("=== Tamper check: change one field and recompute ===")
    tampered = dataclasses.replace(sample, environment="staging")
    print(f"Original : {digest}")
    print(f"Tampered : {compute_hash(tampered)}")
    print(f"Match    : {digest == compute_hash(tampered)}")
