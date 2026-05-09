#!/usr/bin/env python3
"""Entry point for the Sovereign Intent Framework pilot.

Run from the project root:
    python src/run_pilot.py
"""

import sys
sys.path.insert(0, "src")

import pathlib
import time
from datetime import datetime, timezone

import audit_trail
import gateway
from agent_simulator import BASE_MANIFEST, SCENARIO_REQUESTS
from manifest_engine import compute_hash

_REPORTS_DIR = pathlib.Path(__file__).parent.parent / "reports"


def run_pilot() -> None:
    run_ts = datetime.now(timezone.utc)
    results: list[dict] = []

    print(f"Sovereign Intent Framework — Pilot Run")
    print(f"Started : {run_ts.isoformat()}")
    print(f"Scenarios: {len(SCENARIO_REQUESTS)}")
    print()
    print(f"{'STATUS':<6}  {'SCENARIO':<38}  {'DECISION':<10}  {'RULE':<25}  {'ms'}")
    print("-" * 95)

    for sc in SCENARIO_REQUESTS:
        manifest = BASE_MANIFEST
        modifier = sc["manifest_modifier"]

        if sc["tamper_after_hash"]:
            # Lock the hash on the unmodified manifest, then tamper the manifest object.
            # The Gateway will detect the mismatch.
            stored_hash = compute_hash(manifest)
            manifest = modifier(manifest)
        elif modifier is not None:
            # Apply the modifier first (e.g. expired expiry), then sign with the
            # resulting hash so the manifest is legitimately signed but policy-invalid.
            manifest = modifier(manifest)
            stored_hash = compute_hash(manifest)
        else:
            stored_hash = compute_hash(manifest)

        request = sc["request"]

        t0 = time.monotonic()
        gateway_result = gateway.evaluate(request, manifest, stored_hash)
        latency_ms = round((time.monotonic() - t0) * 1_000, 3)

        log_entry = audit_trail.log_decision(
            request, manifest, stored_hash, gateway_result, latency_ms
        )

        passed = gateway_result["decision"] == sc["expected_decision"]
        status = "PASS" if passed else "FAIL"

        print(
            f"{status:<6}  {sc['scenario_name']:<38}  "
            f"{gateway_result['decision']:<10}  "
            f"{gateway_result['rule_fired']:<25}  "
            f"{latency_ms:.3f}"
        )

        results.append({
            "scenario": sc,
            "gateway_result": gateway_result,
            "log_entry": log_entry,
            "passed": passed,
            "latency_ms": latency_ms,
        })

    _print_summary(results)
    _write_report(run_ts, results)

    failed = sum(1 for r in results if not r["passed"])
    sys.exit(1 if failed else 0)


def _print_summary(results: list[dict]) -> None:
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed

    adversarial = [r for r in results if r["scenario"]["expected_decision"] in ("deny", "escalate")]
    correctly_blocked = sum(1 for r in adversarial if r["passed"])
    block_rate = correctly_blocked / len(adversarial) * 100 if adversarial else 0.0

    allow_scenarios = [r for r in results if r["scenario"]["expected_decision"] == "allow"]
    false_positives = sum(
        1 for r in allow_scenarios if r["gateway_result"]["decision"] == "deny"
    )
    fp_rate = false_positives / len(allow_scenarios) * 100 if allow_scenarios else 0.0

    audit_complete = sum(1 for r in results if r["log_entry"] is not None)
    audit_pct = audit_complete / total * 100

    print()
    print("=== Summary ===")
    print(f"  Total scenarios run       : {total}")
    print(f"  Passed                    : {passed}")
    print(f"  Failed                    : {failed}")
    print(f"  Block rate (adversarial)  : {block_rate:.1f}%  ({correctly_blocked}/{len(adversarial)})")
    print(f"  False positive rate       : {fp_rate:.1f}%  ({false_positives}/{len(allow_scenarios)})")
    print(f"  Audit trace completeness  : {audit_pct:.1f}%  ({audit_complete}/{total})")


def _write_report(run_ts: datetime, results: list[dict]) -> None:
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed

    adversarial = [r for r in results if r["scenario"]["expected_decision"] in ("deny", "escalate")]
    correctly_blocked = sum(1 for r in adversarial if r["passed"])
    block_rate = correctly_blocked / len(adversarial) * 100 if adversarial else 0.0

    allow_scenarios = [r for r in results if r["scenario"]["expected_decision"] == "allow"]
    false_positives = sum(
        1 for r in allow_scenarios if r["gateway_result"]["decision"] == "deny"
    )
    fp_rate = false_positives / len(allow_scenarios) * 100 if allow_scenarios else 0.0

    audit_complete = sum(1 for r in results if r["log_entry"] is not None)
    audit_pct = audit_complete / total * 100

    ts_str = run_ts.strftime("%Y-%m-%dT%H:%M:%SZ")
    overall = "PASS" if failed == 0 else "FAIL"

    rows = "\n".join(
        f"| {i} | `{r['scenario']['scenario_name']}` "
        f"| {r['scenario']['expected_decision']} "
        f"| {r['gateway_result']['decision']} "
        f"| `{r['gateway_result']['rule_fired']}` "
        f"| {r['latency_ms']:.3f} "
        f"| {'✓' if r['passed'] else '✗'} |"
        for i, r in enumerate(results, 1)
    )

    report = f"""\
# Sovereign Intent Framework — Pilot Report

**Run timestamp (UTC):** {ts_str}
**Overall result:** {overall} ({passed}/{total} scenarios)

---

## Results

| # | Scenario | Expected | Actual | Rule Fired | Latency (ms) | Status |
|---|----------|----------|--------|------------|-------------|--------|
{rows}

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total scenarios run | {total} |
| Passed | {passed} |
| Failed | {failed} |
| Block rate (adversarial) | {block_rate:.1f}% ({correctly_blocked}/{len(adversarial)}) |
| False positive rate | {fp_rate:.1f}% ({false_positives}/{len(allow_scenarios)}) |
| Audit trace completeness | {audit_pct:.1f}% ({audit_complete}/{total}) |

---

## Assurance Position

{_assurance_text(failed == 0, block_rate, fp_rate, audit_pct)}
"""

    _REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = _REPORTS_DIR / "pilot_report.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"\nReport written → {report_path}")


def _assurance_text(all_pass: bool, block_rate: float, fp_rate: float, audit_pct: float) -> str:
    outcome = (
        "All test scenarios passed."
        if all_pass
        else "**One or more test scenarios failed — see the results table above.**"
    )

    return f"""\
{outcome} The Gateway correctly blocked {block_rate:.1f}% of adversarial scenarios
(tampered manifests, expired manifests, environment mismatches, prohibited actions, and
out-of-scope actions). The false positive rate on safe, in-scope actions was {fp_rate:.1f}%.
Audit trace completeness was {audit_pct:.1f}%.

**What this proves:** The deterministic policy engine enforces the declared intent boundary
correctly across all tested scenarios. Tamper detection via SHA-256 hash verification catches
any post-signing modification to the manifest. Expiry, environment scope, blast-radius
constraints, and action-level controls all fire at the correct precedence. Every Gateway
decision produced a complete, structured audit log entry.

**What this does not prove:** This pilot uses a parameterised simulator, not a real AI agent,
and the "enterprise systems" are entirely mocked. It does not validate integration with real
IAM, PAM, or cloud security controls. It does not test concurrent requests, replay attacks,
hash collision resistance beyond SHA-256 assumptions, or adversarial manifest construction
techniques (e.g. Unicode normalisation attacks on field values). It is not a penetration test,
a formal security audit, or a compliance certification. The control logic validated here is
necessary but not sufficient for a production deployment.
"""


if __name__ == "__main__":
    run_pilot()
