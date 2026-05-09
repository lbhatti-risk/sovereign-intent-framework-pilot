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
| `sample_output/` | Reference audit log and pilot report from a real run |

## Sample Output

The `sample_output/` directory contains reference output from a complete pilot run, so you can inspect expected results without running Docker.

| File | Description |
|------|-------------|
| `sample_output/sample_audit_log.jsonl` | Structured JSON audit log with one entry per Gateway decision across all ten test scenarios |
| `sample_output/sample_pilot_report.md` | Human-readable pilot report summarising pass/fail outcomes, decision breakdown, and audit trace completeness |

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
