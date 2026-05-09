# Sovereign Intent Framework — Pilot

A local proof-of-concept implementing the Sovereign Intent Framework (SIF),
a runtime governance architecture for agentic AI.

The framework's central claim: once AI agents can take actions — calling APIs,
modifying databases, provisioning access — the unit of governance is the action,
not the model. This pilot tests that claim using a deterministic policy engine,
cryptographic manifest hashing, and structured audit trail generation.

## What This Is

This is not a production system. The agent is a parameterised simulator and the
enterprise systems are mocked. The purpose is to validate the core control logic:
does a deterministic Gateway correctly enforce an Intent Manifest across a range
of safe and adversarial scenarios?

## Results

| Metric | Result |
|--------|--------|
| Pilot scenarios | 10/10 passed |
| Block rate (adversarial) | 100% (7/7) |
| False positive rate | 0% (0/3) |
| Audit trace completeness | 100% (10/10) |
| Unit tests | 10/10 passed |

Validated locally and inside Docker.

## How to Run

**Prerequisites:** Docker Desktop installed and running.

```bash
git clone https://github.com/lbhatti-risk/sovereign-intent-framework-pilot.git
cd sovereign-intent-framework-pilot
docker compose build
docker compose up
```

The pilot report is written to `reports/pilot_report.md`.
The audit log is written to `evidence/audit_log.jsonl`.

To run the unit tests:

```bash
pip install pytest freezegun
python3 -m pytest tests/test_suite.py -v
```

## Project Structure

| File | Purpose |
|------|---------|
| `src/manifest_engine.py` | Intent Manifest dataclass, canonicalisation, SHA-256 hashing |
| `src/gateway.py` | Deterministic seven-rule policy engine |
| `src/agent_simulator.py` | Parameterised action request generator and test scenarios |
| `src/audit_trail.py` | Structured JSON audit log writer |
| `src/run_pilot.py` | Pilot entry point and report generator |
| `tests/test_suite.py` | Ten independent unit tests |

## Background

This pilot was built to validate the Sovereign Intent Framework white paper.
The white paper and full governance framework are available at:
[github.com/lbhatti-risk/A-GRC](https://github.com/lbhatti-risk/A-GRC)

## Note on Scope

This pilot validates the control logic in a simulated environment. It does not
test real IAM or PAM integration, concurrent requests, replay attacks, or
adversarial manifest construction. It is not a penetration test or compliance
certification.

---

*Prepared by Layla Bhatti, Digital Auditor.*
