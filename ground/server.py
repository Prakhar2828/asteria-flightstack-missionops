#!/usr/bin/env python3
"""Loopback-only training console. Each browser session gets its own spacecraft."""
import argparse, atexit, hashlib, json, os, pathlib, secrets, sys, threading, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse,parse_qs
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from ground.core import ROOT,Journal,Mission,CHANNELS,COMMANDS,RULES,PROCEDURES
MAX_BODY=8192
class App:
    def __init__(self,path):self.journal=Journal(path);self.sessions={};self.lock=threading.RLock();self.stop=threading.Event()
    def new(self,role,seed):
        with self.lock:
            for token,m in list(self.sessions.items()):
                if time.monotonic()-m.last_access>3600:
                    with m.lock:m.running=False;m.close();del self.sessions[token]
            if len(self.sessions)>=8:raise ValueError('Eight session limit; restart server to clear sessions')
            token=secrets.token_urlsafe(32);m=Mission(self.journal,seed,role);self.sessions[token]=m;return token,m
    def tick(self):
        while not self.stop.wait(1):
            with self.lock:missions=list(self.sessions.values())
            for m in missions:
                with m.lock:
                    if m.running:
                        try:m.step(m.speed)
                        except Exception:m.running=False;m.failed=True
    def close(self):
        self.stop.set()
        with self.lock:
            for m in self.sessions.values():
                with m.lock:m.running=False;m.close()
            self.sessions.clear()
        self.journal.close()
class Handler(BaseHTTPRequestHandler):
    server_version='AsteriaLab/0.1'
    def log_message(self,*args):pass
    def respond(self,status,data,kind='application/json'):
        raw=json.dumps(data,allow_nan=False).encode() if kind=='application/json' else data
        self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(raw)))
        self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers();self.wfile.write(raw)
    def valid_host(self):return self.headers.get('Host') in ('127.0.0.1:'+str(self.server.server_port),'localhost:'+str(self.server.server_port))
    def mission(self):
        auth=self.headers.get('Authorization','');token=auth.removeprefix('Bearer ')
        with self.server.app.lock:m=self.server.app.sessions.get(token)
        if not m:raise PermissionError('Session expired; reconnect')
        m.last_access=time.monotonic();return m
    def do_GET(self):
        if not self.valid_host():return self.respond(403,{'error':'INVALID_HOST'})
        path=urlparse(self.path).path
        try:
            if path=='/api/catalog':return self.respond(200,{'channels':CHANNELS,'commands':COMMANDS,'rules':RULES,'procedures':PROCEDURES})
            if path=='/api/status':return self.respond(200,self.mission().status())
            if path in ('/api/records','/api/export'):
                m=self.mission();after=int(parse_qs(urlparse(self.path).query).get('after',['0'])[0]);records=self.server.app.journal.read(m.id,after)
                return self.respond(200,{'schema':'asteria-journal-v1','run':m.id,'seed':m.seed,'records':records})
            assets={'/':'index.html','/index.html':'index.html','/app.js':'app.js','/style.css':'style.css'}
            if path not in assets:return self.respond(404,{'error':'NOT_FOUND'})
            file=ROOT/'web'/assets[path];mime={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8'}[file.suffix]
            return self.respond(200,file.read_bytes(),mime)
        except PermissionError as exc:self.respond(401,{'error':str(exc)})
        except (ValueError,KeyError):self.respond(400,{'error':'INVALID_QUERY'})
    def do_POST(self):
        if not self.valid_host():return self.respond(403,{'error':'INVALID_HOST'})
        origin=self.headers.get('Origin')
        if origin and origin not in ('http://127.0.0.1:'+str(self.server.server_port),'http://localhost:'+str(self.server.server_port)):return self.respond(403,{'error':'ORIGIN_DENIED'})
        try:
            n=int(self.headers.get('Content-Length','0'))
            if not 0<n<=MAX_BODY:return self.respond(413,{'error':'BODY_SIZE'})
            if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.respond(415,{'error':'JSON_REQUIRED'})
            def invalid_constant(value):raise ValueError('Non-finite number')
            body=json.loads(self.rfile.read(n),parse_constant=invalid_constant)
            if not isinstance(body,dict):raise ValueError('JSON object required')
            path=urlparse(self.path).path
            if path=='/api/session':
                role=body.get('role','administrator');seed=body.get('seed',42)
                if role not in ('observer','operator','administrator') or type(seed)!=int or not 0<=seed<=4294967295:raise ValueError('Invalid role or seed')
                token,m=self.server.app.new(role,seed);return self.respond(201,{'token':token,**m.status()})
            m=self.mission()
            if path=='/api/command':return self.respond(200,m.command(body))
            if path=='/api/control':
                if m.role=='observer':return self.respond(403,{'error':'ROLE_DENIED'})
                action=body.get('action')
                with m.lock:
                    if action=='run':m.running=True
                    elif action=='pause':m.running=False
                    elif action=='speed':
                        speed=body.get('value')
                        if type(speed)!=int or speed not in (1,10,60):raise ValueError('Invalid speed')
                        m.speed=speed
                    elif action=='step':
                        sec=body.get('value',1)
                        if type(sec)!=int or not 1<=sec<=3600:raise ValueError('Invalid step')
                        m.step(sec)
                    else:raise ValueError('Unknown control')
                    m.record('simulation_control',body)
                return self.respond(200,m.status())
            if path=='/api/procedure':
                result=m.advance_procedure() if body.get('action')=='advance' else m.start_procedure(body.get('key'))
                return self.respond(400 if 'error' in result else 200,result)
            if path=='/api/close':
                token=self.headers.get('Authorization','').removeprefix('Bearer ')
                with self.server.app.lock:
                    with m.lock:m.running=False;m.close();del self.server.app.sessions[token]
                return self.respond(200,{'closed':True})
            return self.respond(404,{'error':'NOT_FOUND'})
        except PermissionError as exc:self.respond(401,{'error':str(exc)})
        except (ValueError,TypeError,KeyError) as exc:self.respond(400,{'error':str(exc)})
        except (RuntimeError,TimeoutError,OSError) as exc:self.respond(503,{'error':str(exc)})
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8080);parser.add_argument('--database',default=str(ROOT/'data/missions.sqlite3'));args=parser.parse_args()
    if not (ROOT/'build/flight').exists():
        from scripts.build import build
        build()
    pathlib.Path(args.database).parent.mkdir(parents=True,exist_ok=True)
    app=App(args.database);server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler);server.app=app
    worker=threading.Thread(target=app.tick,daemon=True);worker.start()
    print('Asteria MissionOps: http://127.0.0.1:%s'%args.port,flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:app.stop.set();worker.join(timeout=5);server.server_close();app.close()
if __name__=='__main__':main()
