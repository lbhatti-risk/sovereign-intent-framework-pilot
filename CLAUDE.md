# CLAUDE.md — Sovereign Intent Framework Pilot

## What This Project Is

This is a local proof-of-concept for the Sovereign Intent Framework (SIF), a runtime
governance architecture for agentic AI. The framework's central claim: once AI agents
can take actions (call APIs, modify databases, provision access), the unit of governance
is the action, not the model.

This pilot tests that claim. It simulates an autonomous agent submitting action requests
to a deterministic Gateway, and validates whether the Gateway correctly allows, denies,
or escalates those requests based on a signed Intent Manifest.

This is NOT a real AI agent deployment. The "agent" is a parameterised simulator.
The "enterprise systems" are mocked. The purpose is to validate the control logic.

## Project Structure

- src/manifest_engine.py  -> Manifest creation, canonicalisation, SHA-256 hashing
- src/gateway.py          -> Deterministic policy engine (allow/deny/escalate)
- src/agent_simulator.py  -> Parameterised action request generator
- src/audit_trail.py      -> Structured JSON audit log writer
- src/run_pilot.py        -> Entry point; runs all test cases; produces pilot report
- tests/test_suite.py     -> Seeded test scenarios (happy path + adversarial)
- evidence/               -> JSON audit logs (one file per test run)
- reports/                -> Markdown pilot report (summary of all test outcomes)

## Core Concepts

Intent Manifest: A JSON object defining the authorised task, scope, environment,
allowed actions, prohibited actions, data classification, expiry, owner, and rollback
requirement.

Sovereign Intent Hash: A SHA-256 cryptographic digest of the canonicalised Intent
Manifest. Computed using sorted-key JSON serialisation (RFC 8785 equivalent).
This is the tamper-detection mechanism.

Sovereign Gateway: A deterministic policy engine. It takes an action request plus a
manifest hash, verifies the hash against the stored manifest, checks policy rules, and
returns allow / deny / escalate plus a reason code.

Audit Trail: Every Gateway decision produces a structured JSON log entry with:
manifest_id, hash, action_requested, environment, decision, rule_fired, reason,
timestamp_utc, and latency_ms.

## Coding Conventions

- Python 3.11+. No external AI or LLM libraries.
- Only stdlib plus these allowed packages: pytest, freezegun
- Type hints on all function signatures
- Docstrings on all public functions
- All Gateway decisions must be deterministic — no randomness, no LLM calls
- The Gateway must never approve a destructive action if the manifest is tampered,
  expired, mismatched to the environment, or exceeds the declared blast radius
- Evidence files go in /evidence/, never committed to git
- Reports go in /reports/

## What Success Looks Like

The pilot is successful if:
- 100% of tampered manifest scenarios are denied
- 100% of expired manifest scenarios are denied
- 100% of environment mismatch scenarios are denied
- 0% of safe, in-scope, valid-manifest actions are incorrectly blocked
- 100% of Gateway decisions produce a complete audit log entry
- All test cases run inside Docker with a single command

## What This Pilot Is NOT

- Not a real AI agent
- Not a real enterprise system integration
- Not a compliance framework
- Not a replacement for PAM, IAM, or cloud security controls
- Not production-ready software

