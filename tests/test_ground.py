import copy,json,pathlib,sys,tempfile,unittest,uuid
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from ground.core import Mission,Journal,COMMANDS,PROCEDURES,guard
class GroundTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.journal=Journal(pathlib.Path(self.tmp.name)/'test.db');self.m=Mission(self.journal)
    def tearDown(self):self.m.close();self.journal.close();self.tmp.cleanup()
    def send(self,c,v=0,cid=None):return self.m.command({'id':cid or str(uuid.uuid4()),'command':c,'value':v})
    def test_independent_guard(self):self.assertEqual(self.send('PAYLOAD_ON')['reason'],'FR-05_MODE')
    def test_rejection_not_transmitted(self):self.send('PAYLOAD_ON');self.assertNotIn('command_transmitted',[r['kind'] for r in self.journal.read(self.m.id)])
    def test_lifecycle(self):self.send('BOOT');k=[r['kind'] for r in self.journal.read(self.m.id)];self.assertEqual(k,['run','telemetry','command_requested','command_transmitted','telemetry','command_terminal'])
    def test_duplicate_idempotent(self):a=self.send('BOOT',cid='same');b=self.send('BOOT',cid='same');self.assertEqual(a['status'],b['status']);self.assertTrue(b['duplicate']);self.assertEqual(self.m.truth['telemetry']['commands_accepted'],1)
    def test_duplicate_conflict(self):self.send('BOOT',cid='same');self.assertEqual(self.send('SAFE',cid='same')['reason'],'FR-03_ID_CONFLICT')
    def test_duplicate_parameter_conflict(self):self.send('BOOT');self.send('POINT',1,'same');self.assertEqual(self.send('POINT',2,'same')['reason'],'FR-03_ID_CONFLICT')
    def test_stale_keeps_last_value(self):self.send('BOOT');before=self.m.received;self.send('INJECT_FAULT',3);self.m.step(10);self.assertEqual(self.m.received,before);self.assertEqual(self.m.status()['quality'],'STALE');self.assertEqual(self.m.status()['age'],10)
    def test_downlink_restore(self):self.send('INJECT_FAULT',3);self.m.step(20);self.send('CLEAR_FAULTS');s=self.m.status();self.assertEqual(s['quality'],'LIVE');self.assertEqual(s['state']['mode'],'SAFE')
    def test_stale_boundary(self):self.send('INJECT_FAULT',3);self.m.step(2);self.assertEqual(self.m.status()['quality'],'DISCONNECTED');self.m.step(1);self.assertEqual(self.m.status()['quality'],'STALE')
    def test_isolated_runs(self):m=Mission(self.journal);self.send('BOOT');self.assertEqual(m.truth['mode'],'BOOT');self.assertNotEqual(self.m.id,m.id);m.close()
    def test_procedure_commission(self):self.m.start_procedure('commission');[self.m.advance_procedure() for _ in range(3)];self.assertTrue(self.m.procedure['complete']);self.assertEqual(self.m.truth['telemetry']['payload_enabled'],1)
    def test_procedure_stays_pending(self):self.m.start_procedure('power');self.m.advance_procedure();self.m.advance_procedure();self.assertEqual(self.m.procedure['index'],1)
    def test_observer_procedure_denied(self):self.m.role='observer';self.assertIn('error',self.m.start_procedure('commission'))
    def test_unknown_procedure(self):self.assertIn('error',self.m.start_procedure('bogus'))
    def test_no_active_procedure(self):self.assertIn('error',self.m.advance_procedure())
    def test_journal_roundtrip(self):self.send('BOOT');records=self.journal.read(self.m.id);self.assertEqual(json.loads(json.dumps(records)),records)
    def test_journal_cursor(self):r=self.journal.read(self.m.id);self.assertEqual(self.journal.read(self.m.id,r[-1]['id']),[])
    def test_journal_survives_reopen(self):self.send('BOOT');r=self.journal.read(self.m.id);other=Journal(pathlib.Path(self.tmp.name)/'test.db');self.assertEqual(r,other.read(self.m.id));other.close()
    def test_unknown_command(self):self.assertEqual(self.send('NOPE')['reason'],'UNKNOWN_COMMAND')
    def test_extra_parameter(self):self.assertEqual(self.send('BOOT',5)['reason'],'UNEXPECTED_PARAMETER')
    def test_fault_fraction(self):self.assertEqual(self.send('INJECT_FAULT',1.5)['reason'],'FAULT_INTEGER_REQUIRED')
    def test_boolean_not_number(self):self.assertEqual(self.send('POINT',True)['reason'],'INVALID_PARAMETER')
    def test_string_not_number(self):self.assertEqual(self.send('POINT','0')['reason'],'INVALID_PARAMETER')
    def test_failure_terminal(self):self.m.flight.close();r=self.send('BOOT');self.assertEqual(r['status'],'failed');self.assertEqual(self.journal.read(self.m.id)[-1]['kind'],'command_terminal')
    def test_timeout_terminal(self):
        def timeout(*args):raise TimeoutError()
        self.m.flight.exchange=timeout;self.assertEqual(self.send('BOOT')['status'],'timed-out');self.assertTrue(self.m.failed)
    def test_100_command_reconciliation(self):
        self.send('BOOT')
        for i in range(100):self.send('POINT',i%180,'cmd-%d'%i)
        r=self.journal.read(self.m.id);req={x['data']['id'] for x in r if x['kind']=='command_requested'};terminal={x['data']['id'] for x in r if x['kind']=='command_terminal'};self.assertEqual(req,terminal);self.assertEqual(len(terminal),101)
for role in ['observer','operator','administrator']:
    for command in COMMANDS:
        def test(self,role=role,command=command):
            self.m.role=role;r=self.send(command)
            if role=='observer':self.assertEqual(r['reason'],'FR-01_ROLE_DENIED')
            elif role=='operator' and COMMANDS[command][0]=='administrator':self.assertEqual(r['reason'],'FR-02_ADMIN_REQUIRED')
            else:self.assertNotIn(r['reason'],['FR-01_ROLE_DENIED','FR-02_ADMIN_REQUIRED'])
        setattr(GroundTests,'test_permission_%s_%s'%(role,command.lower()),test)
for i,cid in enumerate(['',None,123,'a'*81,'with space','bad\nframe','<script>']):
    def test(self,cid=cid):self.assertEqual(self.m.command({'id':cid,'command':'BOOT'})['reason'],'INVALID_COMMAND_ID')
    setattr(GroundTests,'test_invalid_id_%d'%i,test)
for key,value,cmd,reason in [('battery_soc',39.9,'PAYLOAD_ON','FR-06_RESOURCES'),('temperature',40,'PAYLOAD_ON','FR-06_RESOURCES'),('sensor_age',1,'PAYLOAD_ON','FR-06_RESOURCES'),('angular_rate',.501,'PAYLOAD_ON','FR-06_RESOURCES'),('link_connected',0,'POINT','FR-04_LINK_UNAVAILABLE'),('adcs_enabled',0,'POINT','FR-10_POINTING'),('temperature',15,'HEATER_ON','FR-07_HEATER')]:
    def test(self,key=key,value=value,cmd=cmd,reason=reason):
        state=copy.deepcopy(self.m.truth);state['mode']='NOMINAL';state['telemetry'][key]=value;self.assertEqual(guard('operator',cmd,0,state),reason)
    setattr(GroundTests,'test_rule_boundary_'+cmd.lower()+'_'+key,test)
