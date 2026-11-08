# Local verification report — release 0.1

Generated from machine-readable evidence. Values are actual observations on one local machine, not targets.

| Measure | Observed result | Evidence |
|---|---|---|
| Test cases | 165 run; 0 failures; 0 errors | `evidence/verification.json`, `test-output.txt` |
| Flight process cases | 83 | Names begin `test_flight` |
| Ground cases | 82 | Names begin `test_ground` |
| HTTP acceptance checks | 30/30 | `evidence/http-smoke.json` |
| Sanitizer exercise | Passed, 47 input/response frames | `evidence/sanitizers.json` |
| Repeated scenario | 20 runs × 1800 simulated seconds | `evidence/benchmark.json` |
| Repeat trace equality | True | 20 complete trace SHA-256 hashes |
| Scripted pointing commands | 100/100 acknowledged | `evidence/latency-samples.json` |
| Reconciliation including BOOT | 101/101 request IDs have terminal records | `evidence/benchmark.json` |
| Local gateway latency p95 | 0.1417 ms, nearest rank, n=100 | Raw latency samples |
| Channels | 26, shared once across both projects | `docs/telemetry-dictionary.json` |
| Flight / lab commands | 12 / 2 | `ground/core.py`, ICD |

Environment: `macOS-26.6-arm64-arm-64bit`. Python: `3.9.6 (default, May 22 2026, 11:13:45) `. Test timestamp: `2026-11-08T16:41:06.856716+00:00`.

Verified source SHA-256: `b8c9f966d63d56854a2f5c780d886e404e2f5e45e3725912383e944db9a2abaa`. The digest covers sorted paths and contents under flight, ground, web, tests, and scripts, excluding Python caches. It is not a Git commit SHA: no repository has been initialized or pushed. Benchmark and HTTP timestamps are stored in their own reports.

## What the tests establish

The enumerated suite checks protocol parsing/bounds, all selected transition pairs, six fault categories, protection and recovery, seeded traces, command/resource guards, the role-by-command permission matrix, command ID reconciliation, timeout/failure handling, procedure progression, and journal round trips. Parameterized cases are reported individually. Counts do not mean unique requirements, full branch coverage, or exhaustive safety verification.

The independent benchmark repeats one fixed-seed 30-minute scenario with sensor injection and recovery. Identical hashes establish repeatability for that configuration on the measured environment. Cross-platform bitwise determinism is not claimed.

## Verification limits

- Browser automation failed before the page could be inspected. **Visual layout, actual browser interactions, mobile layout, keyboard accessibility, and browser display latency remain unverified.** HTTP checks establish API behavior and asset delivery only. JavaScript parsing was checked separately.
- The C++ binary was compiled with strict warnings; the sanitizer run exercises 47 frames and six faults, not the entire exhaustive input space.
- Latency is local Python-to-C++ gateway acknowledgment latency including SQLite writes. It excludes HTTP/browser time and radio propagation. It is not a real-time guarantee or a flight performance claim.
- Coverage, CPU, peak memory and actual host scheduling deadlines were not measured.
- The GitHub Actions workflow is prepared but has not run. Linux support is intended, not verified here.
- F Prime, Open MCT and the other gaps in `scope-and-gaps.md` remain unimplemented.
- This is self-verification of an AI-assisted prototype, not an independent review or certification.
