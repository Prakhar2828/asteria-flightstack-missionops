#!/usr/bin/env python3
"""Reproducible local benchmarks. Reports measured results, never design targets."""
import datetime,hashlib,json,pathlib,platform,resource,statistics,sys,tempfile,time,uuid
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from ground.core import FlightProcess,Journal,Mission

def mission_trace(seed=42):
    f=FlightProcess(seed);trace=[]
    try:
        trace.append(f.exchange('BOOT'))
        for second in range(1,1801):
            if second==100:trace.append(f.exchange('PAYLOAD_ON'))
            if second==300:trace.append(f.exchange('INJECT_FAULT',2))
            if second==320:trace.append(f.exchange('CLEAR_FAULTS'))
            if second==340:trace.append(f.exchange('RECOVER'));trace.append(f.exchange('RESUME'))
            trace.append(f.exchange('STEP',1))
    finally:f.close()
    return trace

def main():
    start=time.perf_counter();hashes=[];trace=None
    for i in range(20):
        trace=mission_trace();hashes.append(hashlib.sha256(json.dumps(trace,sort_keys=True,separators=(',',':')).encode()).hexdigest())
    evidence=ROOT/'evidence';(evidence/'mission-trace.jsonl').write_text(''.join(json.dumps(x,separators=(',',':'))+'\n' for x in trace))
    with tempfile.TemporaryDirectory() as tmp:
        journal=Journal(pathlib.Path(tmp)/'bench.db');m=Mission(journal);m.command({'id':'boot','command':'BOOT'})
        samples=[]
        for i in range(100):
            r=m.command({'id':'bench-%d'%i,'command':'POINT','value':i-50});samples.append({'index':i,'latency_ms':r['latency_ms'],'status':r['status']})
        rows=journal.read(m.id);req={r['data']['id'] for r in rows if r['kind']=='command_requested'};ack={r['data']['id'] for r in rows if r['kind']=='command_terminal'}
        m.close();journal.close()
    values=sorted(r['latency_ms'] for r in samples)
    report={'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'environment':platform.platform(),'processor':platform.machine(),'seed':42,'repeated_runs':20,'simulated_seconds_per_run':1800,'trace_hashes':hashes,'identical_runs':len(set(hashes))==1,'command_samples':100,'acknowledged':sum(x['status']=='acknowledged' for x in samples),'reconciled_requests':len(req&ack),'total_requests_including_boot':len(req),'gateway_latency_ms':{'minimum':min(values),'median':statistics.median(values),'p95_nearest_rank':values[94],'maximum':max(values)},'benchmark_wall_seconds':time.perf_counter()-start,'limits':['Gateway latency includes SQLite audit writes and C++ process exchange. Excludes HTTP, UI display and RF latency.','CPU, peak memory and host scheduling deadlines not instrumented in this report.','20 traces repeat one scripted 30-minute scenario; this is not exhaustive verification.']}
    (evidence/'benchmark.json').write_text(json.dumps(report,indent=2)+'\n');(evidence/'latency-samples.json').write_text(json.dumps(samples,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
