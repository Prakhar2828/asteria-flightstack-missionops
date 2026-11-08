#!/usr/bin/env python3
"""Exercise the running localhost application through HTTP; close test sessions."""
import datetime,json,pathlib,sys,time,urllib.request,urllib.error,uuid
BASE=sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8080'
ROOT=pathlib.Path(__file__).resolve().parents[1]
results=[]
def request(path,body=None,token=None,origin=None):
    headers={'Content-Type':'application/json'}
    if token:headers['Authorization']='Bearer '+token
    if origin:headers['Origin']=origin
    r=urllib.request.Request(BASE+path,headers=headers,data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(r,timeout=5) as response:return response.status,response.read(),dict(response.headers)
    except urllib.error.HTTPError as response:return response.code,response.read(),dict(response.headers)
def check(name,condition):
    results.append({'name':name,'passed':bool(condition)})
    if not condition:raise AssertionError(name)
def main():
    tokens=[]
    for attempt in range(40):
        try:
            request('/api/catalog');break
        except urllib.error.URLError:
            if attempt==39:raise
            time.sleep(.1)
    try:
        for path,mime in [('/','text/html'),('/app.js','text/javascript'),('/style.css','text/css')]:
            code,data,headers=request(path);check('asset '+path,code==200 and mime in headers['Content-Type'] and len(data)>100)
        code,_,headers=request('/');check('security headers',"frame-ancestors 'none'" in headers['Content-Security-Policy'])
        check('unauthenticated status',request('/api/status')[0]==401)
        check('path traversal denied',request('/../ground/core.py')[0]==404)
        check('cross-origin mutation denied',request('/api/session',{},origin='https://untrusted.example')[0]==403)
        check('invalid seed',request('/api/session',{'seed':-1})[0]==400)
        check('invalid role',request('/api/session',{'role':'root'})[0]==400)
        for role in ('observer','operator','administrator'):
            code,data,_=request('/api/session',{'role':role,'seed':42});s=json.loads(data);token=s['token'];tokens.append(token);check('session '+role,code==201 and s['state']['mode']=='BOOT')
            command=lambda c,v=0:json.loads(request('/api/command',{'id':str(uuid.uuid4()),'command':c,'value':v},token)[1])
            r=command('BOOT');check('BOOT role '+role,(r['status']=='acknowledged')==(role!='observer'))
            check('control role '+role,(request('/api/control',{'action':'step','value':10},token)[0]==200)==(role!='observer'))
            r=command('INJECT_FAULT',2);check('fault role '+role,(r['status']=='acknowledged')==(role=='administrator'))
            if role=='administrator':
                command('CLEAR_FAULTS');request('/api/control',{'action':'step','value':10},token);check('recover',command('RECOVER')['status']=='acknowledged');check('resume',command('RESUME')['status']=='acknowledged')
                command('INJECT_FAULT',3);request('/api/control',{'action':'step','value':20},token);state=json.loads(request('/api/status',token=token)[1]);check('stale quality',state['quality']=='STALE' and state['age']==20);command('CLEAR_FAULTS')
                check('negative step',request('/api/control',{'action':'step','value':-1},token)[0]==400)
                request('/api/procedure',{'key':'shutdown'},token)
                for _ in range(3):code,data,_=request('/api/procedure',{'action':'advance'},token)
                check('shutdown procedure',json.loads(data)['complete'])
            data=json.loads(request('/api/export',token=token)[1]);check('journal export '+role,data['schema']=='asteria-journal-v1' and len(data['records'])>1)
        check('missing page',request('/unknown')[0]==404)
    finally:
        for token in tokens:request('/api/close',{},token)
        (ROOT/'evidence/http-smoke.json').write_text(json.dumps({'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'base_url':BASE,'checks':results,'note':'HTTP acceptance checks; not browser rendering or interaction tests.'},indent=2)+'\n')
    print('%d/%d HTTP checks passed'%(sum(r['passed'] for r in results),len(results)))
if __name__=='__main__':main()
