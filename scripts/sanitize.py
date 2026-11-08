#!/usr/bin/env python3
import datetime,json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
commands=['BOOT 0','STEP 1800']
for i in range(6):commands+=['INJECT_FAULT '+str(i),'STEP 30','CLEAR_FAULTS 0','DESATURATE 0','STEP 1800','RECOVER 0','RESUME 0']
commands+=['BAD 0','BOOT nan','X'*300+' 0']
p=subprocess.run([str(ROOT/'build/flight-sanitized')],input='\n'.join(commands)+'\n',capture_output=True,text=True)
report={'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sanitizers':['AddressSanitizer','UndefinedBehaviorSanitizer'],'exit_code':p.returncode,'frames':len(p.stdout.splitlines()),'stderr':p.stderr,'passed':p.returncode==0 and not p.stderr}
(ROOT/'evidence/sanitizers.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(0 if report['passed'] else 1)
