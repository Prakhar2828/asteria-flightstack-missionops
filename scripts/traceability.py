#!/usr/bin/env python3
"""Join requirements to actual unittest results, rejecting missing test references."""
import csv,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
v=json.loads((ROOT/'evidence/verification.json').read_text());cases={c['id']:c['status'] for c in v['cases']}
with (ROOT/'docs/requirements.csv').open() as f:requirements=list(csv.DictReader(f))
assert len({r['requirement_id'] for r in requirements})==len(requirements),'Duplicate requirement IDs'
rows=[]
for r in requirements:
    assert r['test_id'] in cases,'Missing test: '+r['test_id']
    rows.append({**r,'observed_test_status':cases[r['test_id']],'source_sha256':v['source_sha256'],'evidence':'evidence/verification.json'})
with (ROOT/'docs/verification-matrix.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print('%d scoped requirements mapped; %d have passing referenced cases'%(len(rows),sum(r['observed_test_status']=='passed' for r in rows)))
print('Traceability is not proof of sufficient test coverage or complete master-spec implementation.')
