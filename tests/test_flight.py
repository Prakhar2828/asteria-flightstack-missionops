import json, pathlib, subprocess, sys, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from ground.core import FlightProcess
class FlightTests(unittest.TestCase):
    def setUp(self):self.f=FlightProcess()
    def tearDown(self):self.f.close()
    def cmd(self,c,v=0):return self.f.exchange(c,v)
    def test_boot(self):self.assertEqual(self.cmd('BOOT')['mode'],'NOMINAL')
    def test_boot_twice(self):self.cmd('BOOT');self.assertFalse(self.cmd('BOOT')['ok'])
    def test_safe_sheds_payload(self):self.cmd('BOOT');self.cmd('PAYLOAD_ON');s=self.cmd('SAFE');self.assertEqual(s['telemetry']['payload_enabled'],0)
    def test_payload_accumulates(self):self.cmd('BOOT');self.cmd('PAYLOAD_ON');self.assertEqual(self.cmd('STEP',10)['telemetry']['payload_data'],2.5)
    def test_safe_no_payload(self):self.cmd('SAFE');self.assertFalse(self.cmd('PAYLOAD_ON')['ok'])
    def test_point_valid(self):self.cmd('BOOT');self.assertEqual(self.cmd('POINT',90)['telemetry']['target_angle'],90)
    def test_point_adcs_off(self):self.cmd('BOOT');self.cmd('ADCS_OFF');self.assertFalse(self.cmd('POINT',20)['ok'])
    def test_adcs_off_payload(self):self.cmd('BOOT');self.cmd('PAYLOAD_ON');self.assertFalse(self.cmd('ADCS_OFF')['ok'])
    def test_sensor_blocks_point(self):self.cmd('BOOT');self.cmd('INJECT_FAULT',2);self.assertFalse(self.cmd('POINT',20)['ok'])
    def test_heater_hot_rejected(self):self.cmd('BOOT');self.assertFalse(self.cmd('HEATER_ON')['ok'])
    def test_fault_clearing_keeps_physics(self):self.cmd('INJECT_FAULT',0);s=self.cmd('CLEAR_FAULTS');self.assertEqual(s['telemetry']['battery_soc'],15)
    def test_thermal_clear_keeps_physics(self):self.cmd('INJECT_FAULT',1);self.assertEqual(self.cmd('CLEAR_FAULTS')['telemetry']['temperature'],55)
    def test_power_recovery(self):
        self.cmd('BOOT');self.cmd('INJECT_FAULT',0);self.cmd('CLEAR_FAULTS');self.assertFalse(self.cmd('RECOVER')['ok']);self.cmd('STEP',1850);self.assertTrue(self.cmd('RECOVER')['ok']);self.assertEqual(self.cmd('RESUME')['mode'],'NOMINAL')
    def test_thermal_recovery(self):self.cmd('INJECT_FAULT',1);self.cmd('CLEAR_FAULTS');self.cmd('STEP',300);self.assertTrue(self.cmd('RECOVER')['ok'])
    def test_sensor_recovery_dwell(self):self.cmd('INJECT_FAULT',2);self.cmd('CLEAR_FAULTS');self.cmd('STEP',9);self.assertFalse(self.cmd('RECOVER')['ok']);self.cmd('STEP',1);self.assertTrue(self.cmd('RECOVER')['ok'])
    def test_wheel_recovery_requires_desat(self):self.cmd('INJECT_FAULT',5);self.assertFalse(self.cmd('DESATURATE')['ok']);self.cmd('CLEAR_FAULTS');self.cmd('DESATURATE');self.cmd('STEP',10);self.assertTrue(self.cmd('RECOVER')['ok'])
    def test_link_loss_15s(self):self.cmd('BOOT');self.cmd('INJECT_FAULT',3);self.assertEqual(self.cmd('STEP',14)['mode'],'NOMINAL');self.assertEqual(self.cmd('STEP',1)['mode'],'SAFE')
    def test_link_blocks_commands(self):self.cmd('INJECT_FAULT',3);self.assertEqual(self.cmd('BOOT')['reason'],'LINK_UNAVAILABLE')
    def test_watchdog_count(self):self.cmd('INJECT_FAULT',4);self.assertEqual(self.cmd('STEP',11)['telemetry']['missed_deadlines'],11)
    def test_telemetry_dictionary(self):
        from ground.core import CHANNELS
        self.assertEqual(set(self.cmd('SNAPSHOT')['telemetry']),set(CHANNELS))
    def test_seed_reproducibility(self):
        self.cmd('BOOT');a=self.cmd('STEP',1800)
        with self.subTest('independent process'):
            f=FlightProcess();f.exchange('BOOT');b=f.exchange('STEP',1800);f.close();self.assertEqual(a,b)
    def test_different_seed_changes_noise(self):
        self.cmd('BOOT');a=self.cmd('STEP',100)
        f=FlightProcess(43);f.exchange('BOOT');b=f.exchange('STEP',100);f.close();self.assertNotEqual(a['telemetry']['attitude'],b['telemetry']['attitude'])
    def test_nominal_30_minutes(self):self.cmd('BOOT');s=self.cmd('STEP',1800);self.assertEqual(s['mode'],'NOMINAL');self.assertEqual(s['telemetry']['time'],1800);self.assertEqual(s['telemetry']['missed_deadlines'],0)
    def test_sunlight_boundary(self):self.cmd('STEP',3499);self.assertEqual(self.cmd('STEP',1)['telemetry']['sunlight'],0)
    def test_orbit_wrap(self):self.cmd('STEP',3600);self.assertEqual(self.cmd('STEP',1800)['telemetry']['orbit_phase'],0)
    def test_battery_bounded(self):self.cmd('INJECT_FAULT',0);s=self.cmd('STEP',3600);self.assertGreaterEqual(s['telemetry']['battery_soc'],0)
    def test_event_retention(self):
        for _ in range(300):self.cmd('PAYLOAD_OFF')
        self.assertEqual(len(self.cmd('SNAPSHOT')['events']),256)
    def test_invalid_frame(self):
        p=subprocess.run([str(ROOT/'build/flight')],input='\nBOOT\nBOOT 0 extra\nboot 0\nBOOT nan\n',text=True,capture_output=True,check=True)
        self.assertEqual([json.loads(l)['reason'] for l in p.stdout.splitlines()],['MALFORMED_FRAME']*5)
    def test_frame_limit(self):
        p=subprocess.run([str(ROOT/'build/flight')],input='X'*300+' 0\n',text=True,capture_output=True,check=True);self.assertEqual(json.loads(p.stdout)['reason'],'FRAME_TOO_LARGE')
    def test_nonzero_unused_parameter(self):self.assertEqual(self.cmd('BOOT',1)['reason'],'UNEXPECTED_PARAMETER')
    def test_oversized_frame_resynchronizes(self):
        p=subprocess.run([str(ROOT/'build/flight')],input='X'*300+' 0\nBOOT 0\n',text=True,capture_output=True,check=True);rows=[json.loads(l) for l in p.stdout.splitlines()];self.assertEqual(rows[0]['reason'],'FRAME_TOO_LARGE');self.assertEqual(rows[1]['mode'],'NOMINAL')
    def test_embedded_null_rejected(self):
        p=subprocess.run([str(ROOT/'build/flight')],input='BOOT 0\0ignored\n',text=True,capture_output=True,check=True);self.assertFalse(json.loads(p.stdout)['ok'])
    def test_invalid_seed(self):self.assertEqual(subprocess.run([str(ROOT/'build/flight'),'4294967296'],capture_output=True).returncode,2)
# Named parameter cases enumerate explicit protocol boundaries and transition pairs.
for command,values in {'POINT':[-181,-180,0,180,181], 'STEP':[-1,0,.5,1,3600,3601], 'INJECT_FAULT':[-1,0,1,2,3,4,5,6,.5]}.items():
    for i,value in enumerate(values):
        def test(self,c=command,v=value):
            self.cmd('BOOT');r=self.cmd(c,v)
            valid=(-180<=v<=180) if c=='POINT' else ((1<=v<=3600 and int(v)==v) if c=='STEP' else 0<=v<=5 and int(v)==v)
            self.assertEqual(r['ok'],valid)
        setattr(FlightTests,'test_boundary_%s_%02d'%(command.lower(),i),test)
for fault in range(6):
    def test(self,f=fault):
        self.cmd('BOOT');self.cmd('PAYLOAD_ON');self.cmd('INJECT_FAULT',f);s=self.cmd('STEP',15 if f==3 else 1);self.assertEqual(s['mode'],'SAFE');self.assertEqual(s['telemetry']['payload_enabled'],0)
    setattr(FlightTests,'test_fault_%d_protection'%fault,test)
for start in ['BOOT','NOMINAL','SAFE','RECOVERY']:
    for command in ['BOOT','RECOVER','RESUME']:
        def test(self,start=start,c=command):
            if start=='NOMINAL':self.cmd('BOOT')
            if start in ('SAFE','RECOVERY'):self.cmd('SAFE');self.cmd('STEP',10)
            if start=='RECOVERY':self.cmd('RECOVER')
            valid=(start,c) in [('BOOT','BOOT'),('SAFE','RECOVER'),('RECOVERY','RESUME')]
            self.assertEqual(self.cmd(c)['ok'],valid)
        setattr(FlightTests,'test_transition_%s_%s'%(start,command),test)
for command in ['UNKNOWN','RESET','NOMINAL','REBOOT','PAYLOAD_START','SET_BATTERY','SET_MODE','DELETE','AUTH','EXIT','DROP_DATABASE','POWER_ON']:
    def test(self,c=command):self.assertEqual(self.cmd(c)['reason'],'UNKNOWN_COMMAND')
    setattr(FlightTests,'test_unknown_'+command.lower(),test)
