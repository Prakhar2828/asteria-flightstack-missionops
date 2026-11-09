#!/usr/bin/env python3
"""Generate a report from observed evidence, never from proposed targets."""

import collections, csv, json, math, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT / "evidence" / name).read_text())


def main():
    v = load("verification.json")
    b = load("benchmark.json")
    f = load("fprime.json")
    a = load("mission-acceptance.json")
    p = load("runtime-profile.json")
    c = load("coverage.json")
    h = load("http-smoke.json")
    s = load("sanitizers.json")
    d = load("browser-display-timing.json")
    u = load("browser-acceptance.json")
    count = collections.Counter(x["id"].split(".")[0] for x in v["cases"])
    samples = sorted(x["latency_ms"] for x in d["samples"])
    p95 = samples[math.ceil(0.95 * len(samples)) - 1]
    text = f"""# Local verification report

These are observed results on `{v['environment']}`. They are not design targets, flight guarantees or independent certification.

| Check | Observed result | Raw evidence |
|---|---|---|
| Automated suite | {v['tests_run']} cases; {v['failures']} failures; {v['errors']} errors | verification.json, test-output.txt |
| Flight / ground / API cases | {count['test_flight']} / {count['test_ground']} / {count['test_api']} | Individually named cases |
| Scoped requirements | 40 flight + 20 ground, mapped to actual results | docs/verification-matrix.csv |
| HTTP acceptance | {sum(x['passed'] for x in h['checks'])}/{len(h['checks'])} | http-smoke.json |
| F Prime command parity | 171 frames across 3 seeds and all 6 faults | fprime.json |
| Typed-port harness | {f['typed_port_harness']['telemetry_samples']} channel samples; malformed/terminal-response checks passed | fprime.json |
| Real scheduled deployment | {f['real_scheduler_ticks_in_five_seconds']} ticks in a five-second launch, clean shutdown | fprime-deployment-log.txt |
| Deterministic flight runs | {b['repeated_runs']} × {b['simulated_seconds_per_run']} simulated seconds; identical hashes: {b['identical_runs']} | benchmark.json, mission-trace.jsonl |
| Ground replay | {a['replay_runs']} identical reads of {a['records']} complete journal rows over 1,800 simulated seconds | mission-acceptance.json, ground-mission.jsonl |
| Scenario acceptance | {len(a['scenarios'])} nominal/anomaly workflows passed | scenario-*.json |
| Command reconciliation | {b['reconciled_requests']}/{b['total_requests_including_boot']} requests including BOOT have terminal records | benchmark.json |
| Gateway acknowledgment p95 | {b['gateway_latency_ms']['p95_nearest_rank']:.3f} ms, n=100 | latency-samples.json |
| Browser receipt-to-animation p95 | {p95:.2f} ms, n={len(samples)} fresh receipts | browser-display-timing.json |
| Sanitizers | Passed: {s['passed']}; {s['frames']} frames | sanitizers.json |
| Isolated flight peak resident memory | {p['isolated_child']['peak_resident_kib']:.0f} KiB | runtime-profile.json |
| Isolated flight CPU | {p['isolated_child']['user_cpu_seconds']:.4f} s user + {p['isolated_child']['system_cpu_seconds']:.4f} s system for 20,000 logical steps | runtime-profile.json |
| Ground scheduling | {len(p['scheduler']['samples'])} samples with 8 active sessions; {p['scheduler']['work_overruns']} work-budget overruns | runtime-profile.json |
| PostgreSQL | Six adapter/durability/mission checks passed on local PostgreSQL 17 | postgresql.json |
| Browser checks | Six dashboards, Open MCT plot, procedure acknowledgments, replay/debrief, stale-link recovery, 390px layout | browser-acceptance.json, screenshots/ |

## Instrumented core coverage

"""
    for file in c["files"]:
        text += f"- `{file['file']}`: {file['lines']['covered']}/{file['lines']['count']} instrumented lines; {file['branches']['covered']}/{file['branches']['count']} branches ({file['branches']['percent']:.2f}%).\n"
    text += """
Coverage excludes generated F Prime code, its framework, Python and browser code. It is not MC/DC or exhaustive input-space coverage. HTML source reports are in `evidence/coverage-html/`.

## Measurement boundaries

Gateway latency includes local process exchange and journal writes. Browser timing uses the same host wall clock from fresh gateway telemetry receipt to a requestAnimationFrame callback; it includes stream scheduling, but is not physical pixel presentation or RF latency. The first sample can include initialization/navigation time. Samples are retained without deleting outliers. The browser test used a single active mission at 1× with a 4 Hz stream.

Paced load profiles at 1, 10 and 100 commands/second are in mission-acceptance.json, including every latency and sampled memory observation. Isolated CPU/peak RSS is measured separately. The short eight-session scheduler run cannot establish hard real-time behavior. Injected watchdog telemetry is logical fault behavior, distinct from host scheduling measurements.

Twenty identical traces cover one deterministic scenario on one host. Ten replay passes reconstruct all saved records; they do not prove that every possible mission is deterministic. All four stored scenario traces passed their defined expected outcomes. The database journal is not tamper-proof.

GitHub Actions is prepared but has not been run by this local task. Linux, public hosting, physical hardware, production authentication, independent review and flight qualification are not claimed. The console exercises the F Prime bridge; the scheduled deployment's TCP/CCSDS path is not part of this evidence.
"""
    text += f"\nVerification source digest: `{v['source_sha256']}`. It covers source under flight, ground, web, tests, scripts and integrations, excluding caches, external framework source and generated builds. Evidence scripts may have their own run timestamps.\n"
    (ROOT / "docs/technical-report.md").write_text(text)
    (ROOT / "evidence/display-summary.json").write_text(
        json.dumps(
            {
                "samples": len(samples),
                "p95_ms": p95,
                "min_ms": min(samples),
                "max_ms": max(samples),
                "scope": d["scope"],
            },
            indent=2,
        )
        + "\n"
    )
    print("Generated technical report from recorded results.")


if __name__ == "__main__":
    main()
