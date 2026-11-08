#!/usr/bin/env python3
"""Derive the human-readable report and metric ledger from recorded evidence."""
import collections,csv,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
    v=json.loads((ROOT/'evidence/verification.json').read_text());b=json.loads((ROOT/'evidence/benchmark.json').read_text());h=json.loads((ROOT/'evidence/http-smoke.json').read_text());s=json.loads((ROOT/'evidence/sanitizers.json').read_text())
    count=collections.Counter(c['id'].split('.')[0] for c in v['cases']);p95=b['gateway_latency_ms']['p95_nearest_rank']
    text=f'''# Local verification report — release 0.1

Generated from machine-readable evidence. Values are actual observations on one local machine, not targets.

| Measure | Observed result | Evidence |
|---|---|---|
| Test cases | {v['tests_run']} run; {v['failures']} failures; {v['errors']} errors | `evidence/verification.json`, `test-output.txt` |
| Flight process cases | {count['test_flight']} | Names begin `test_flight` |
| Ground cases | {count['test_ground']} | Names begin `test_ground` |
| HTTP acceptance checks | {sum(x['passed'] for x in h['checks'])}/{len(h['checks'])} | `evidence/http-smoke.json` |
| Sanitizer exercise | {'Passed' if s['passed'] else 'FAILED'}, {s['frames']} input/response frames | `evidence/sanitizers.json` |
| Repeated scenario | {b['repeated_runs']} runs × {b['simulated_seconds_per_run']} simulated seconds | `evidence/benchmark.json` |
| Repeat trace equality | {b['identical_runs']} | 20 complete trace SHA-256 hashes |
| Scripted pointing commands | {b['acknowledged']}/{b['command_samples']} acknowledged | `evidence/latency-samples.json` |
| Reconciliation including BOOT | {b['reconciled_requests']}/{b['total_requests_including_boot']} request IDs have terminal records | `evidence/benchmark.json` |
| Local gateway latency p95 | {p95:.4f} ms, nearest rank, n=100 | Raw latency samples |
| Channels | 26, shared once across both projects | `docs/telemetry-dictionary.json` |
| Flight / lab commands | 12 / 2 | `ground/core.py`, ICD |

Environment: `{v['environment']}`. Python: `{v['python'].splitlines()[0]}`. Test timestamp: `{v['timestamp_utc']}`.

Verified source SHA-256: `{v['source_sha256']}`. The digest covers sorted paths and contents under flight, ground, web, tests, and scripts, excluding Python caches. It is not a Git commit SHA: no repository has been initialized or pushed. Benchmark and HTTP timestamps are stored in their own reports.

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
'''
    (ROOT/'docs/technical-report.md').write_text(text)
    metrics=[('AFS-TESTS',count['test_flight'],'cases','evidence/verification.json'),('MODT-TESTS',count['test_ground'],'cases','evidence/verification.json'),('HTTP-CHECKS',sum(x['passed'] for x in h['checks']),'passed / '+str(len(h['checks'])),'evidence/http-smoke.json'),('AFS-DETERMINISM',b['repeated_runs'],'same-seed runs, all equal='+str(b['identical_runs']),'evidence/benchmark.json'),('SHARED-LATENCY-P95',p95,'ms; local gateway; n=100','evidence/latency-samples.json')]
    with (ROOT/'evidence/metrics-ledger.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['metric_id','actual','units_and_scope','evidence','status','source_sha256']);w.writerows([(*row,'V',v['source_sha256']) for row in metrics])
    print('Wrote technical report and metrics ledger')
if __name__=='__main__':main()
