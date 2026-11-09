# Local verification report

These are observed results on `macOS-26.6-arm64-arm-64bit`. They are not design targets, flight guarantees or independent certification.

| Check | Observed result | Raw evidence |
|---|---|---|
| Automated suite | 199 cases; 0 failures; 0 errors | verification.json, test-output.txt |
| Flight / ground / API cases | 83 / 82 / 34 | Individually named cases |
| Scoped requirements | 40 flight + 20 ground, mapped to actual results | docs/verification-matrix.csv |
| HTTP acceptance | 30/30 | http-smoke.json |
| F Prime command parity | 171 frames across 3 seeds and all 6 faults | fprime.json |
| Typed-port harness | 48708 channel samples; malformed/terminal-response checks passed | fprime.json |
| Real scheduled deployment | 4 ticks in a five-second launch, clean shutdown | fprime-deployment-log.txt |
| Deterministic flight runs | 20 × 1800 simulated seconds; identical hashes: True | benchmark.json, mission-trace.jsonl |
| Ground replay | 10 identical reads of 1826 complete journal rows over 1,800 simulated seconds | mission-acceptance.json, ground-mission.jsonl |
| Scenario acceptance | 4 nominal/anomaly workflows passed | scenario-*.json |
| Command reconciliation | 101/101 requests including BOOT have terminal records | benchmark.json |
| Gateway acknowledgment p95 | 0.506 ms, n=100 | latency-samples.json |
| Browser receipt-to-animation p95 | 247.82 ms, n=45 fresh receipts | browser-display-timing.json |
| Sanitizers | Passed: True; 47 frames | sanitizers.json |
| Isolated flight peak resident memory | 1840 KiB | runtime-profile.json |
| Isolated flight CPU | 0.0904 s user + 0.0070 s system for 20,000 logical steps | runtime-profile.json |
| Ground scheduling | 6 samples with 8 active sessions; 0 work-budget overruns | runtime-profile.json |
| PostgreSQL | Six adapter/durability/mission checks passed on local PostgreSQL 17 | postgresql.json |
| Browser checks | Six dashboards, Open MCT plot, procedure acknowledgments, replay/debrief, stale-link recovery, 390px layout | browser-acceptance.json, screenshots/ |

## Instrumented core coverage

- `flight/flight.hpp`: 228/232 instrumented lines; 191/210 branches (90.95%).
- `flight/main.cpp`: 37/42 instrumented lines; 22/26 branches (84.62%).

Coverage excludes generated F Prime code, its framework, Python and browser code. It is not MC/DC or exhaustive input-space coverage. HTML source reports are in `evidence/coverage-html/`.

## Measurement boundaries

Gateway latency includes local process exchange and journal writes. Browser timing uses the same host wall clock from fresh gateway telemetry receipt to a requestAnimationFrame callback; it includes stream scheduling, but is not physical pixel presentation or RF latency. The first sample can include initialization/navigation time. Samples are retained without deleting outliers. The browser test used a single active mission at 1× with a 4 Hz stream.

Paced load profiles at 1, 10 and 100 commands/second are in mission-acceptance.json, including every latency and sampled memory observation. Isolated CPU/peak RSS is measured separately. The short eight-session scheduler run cannot establish hard real-time behavior. Injected watchdog telemetry is logical fault behavior, distinct from host scheduling measurements.

Twenty identical traces cover one deterministic scenario on one host. Ten replay passes reconstruct all saved records; they do not prove that every possible mission is deterministic. All four stored scenario traces passed their defined expected outcomes. The database journal is not tamper-proof.

GitHub Actions is prepared but has not been run by this local task. Linux, public hosting, physical hardware, production authentication, independent review and flight qualification are not claimed. The console exercises the F Prime bridge; the scheduled deployment's TCP/CCSDS path is not part of this evidence.

Verification source digest: `784b25307f18c652419b5a0be6a155b527ef58285f2749e586802e557685bb3d`. It covers source under flight, ground, web, tests, scripts and integrations, excluding caches, external framework source and generated builds. Evidence scripts may have their own run timestamps.
