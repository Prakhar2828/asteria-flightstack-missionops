// Browser ground adapter. Physics and onboard authority remain in the compiled C++ core.
export function guard(role, command, value, state, commands) {
  if (!Object.hasOwn(commands, command)) return 'UNKNOWN_COMMAND';
  if (!['operator', 'administrator'].includes(role)) return 'FR-01_ROLE_DENIED';
  if (commands[command][0] === 'administrator' && role !== 'administrator') return 'FR-02_ADMIN_REQUIRED';
  if (typeof value !== 'number' || !Number.isFinite(value)) return 'INVALID_PARAMETER';
  const bounds = commands[command][1];
  if (bounds && (value < bounds[0] || value > bounds[1])) return 'PARAMETER_RANGE';
  if (command === 'INJECT_FAULT' && !Number.isInteger(value)) return 'FAULT_INTEGER_REQUIRED';
  if (!bounds && value !== 0) return 'UNEXPECTED_PARAMETER';
  const t = state.telemetry, mode = state.mode;
  if (['INJECT_FAULT', 'CLEAR_FAULTS'].includes(command)) return null;
  if (!t.link_connected) return 'FR-04_LINK_UNAVAILABLE';
  if (command === 'PAYLOAD_ON') {
    if (mode !== 'NOMINAL') return 'FR-05_MODE';
    if (t.battery_soc < 40 || t.temperature >= 40 || t.sensor_age > 0 || Math.abs(t.angular_rate) > .5) return 'FR-06_RESOURCES';
  }
  if (command === 'HEATER_ON' && (mode !== 'NOMINAL' || t.battery_soc < 30 || t.temperature >= 15)) return 'FR-07_HEATER';
  if (command === 'RECOVER' && (mode !== 'SAFE' || !t.healthy || t.healthy_dwell < 10)) return 'FR-08_RECOVERY';
  if (command === 'RESUME' && (mode !== 'RECOVERY' || !t.healthy)) return 'FR-09_RESUME';
  if (command === 'POINT' && (mode !== 'NOMINAL' || !t.adcs_enabled || t.sensor_age > 0)) return 'FR-10_POINTING';
  return null;
}

export class BrowserMission {
  constructor(engine, catalog, seed = 42, role = 'administrator') {
    if (!Number.isInteger(seed) || seed < 0 || seed > 4294967295) throw Error('Invalid seed');
    if (!['observer', 'operator', 'administrator'].includes(role)) throw Error('Invalid training role');
    this.engine = engine; this.catalog = catalog; this.seed = seed; this.role = role;
    engine.reset(seed); this.id = crypto.randomUUID(); this.epoch_ms = Date.now();
    this.transcript = []; this.records = []; this.cache = new Map(); this.procedure = null;
    this.running = false; this.speed = 1; this.failed = false; this.last_received = 0;
    this.truth = engine.exchange('SNAPSHOT', 0); this.received = this.truth; this.received_at_ms = Date.now();
    this.record('run', {seed, role, protocol_version: 1, epoch_ms: this.epoch_ms, backend: 'cpp-webassembly'});
    this.record('telemetry', this.received);
  }
  record(kind, data) {
    this.records.push({id: this.records.length + 1, sim: this.truth.telemetry.time, wall: Date.now()/1000, kind, data: structuredClone(data)});
  }
  exchange(command, value = 0) {
    // Keep replay and browser memory bounded; never silently discard mission evidence.
    if (this.transcript.length >= 7200 || this.records.length >= 20000) {
      this.running = false; throw Error('Demo recording limit reached. Export this mission and start another.');
    }
    const response = this.engine.exchange(command, value);
    this.transcript.push([command, value]); this.truth = response;
    if (response.telemetry.link_connected) {
      this.received = response; this.last_received = response.telemetry.time; this.received_at_ms = Date.now();
      this.record('telemetry', response);
    }
    return response;
  }
  step(seconds) {
    if (!Number.isInteger(seconds) || seconds < 1 || seconds > 3600) throw Error('Step must be 1–3600 seconds');
    this.exchange('STEP', seconds);
  }
  command({id, command, value = 0}) {
    if (typeof id !== 'string' || !/^[a-zA-Z0-9_-]{1,80}$/.test(id)) return {status:'rejected',reason:'INVALID_COMMAND_ID'};
    if (this.cache.has(id)) {
      const old = this.cache.get(id);
      return old.command === command && old.value === value ? {...old.result, duplicate:true} : {id,status:'rejected',reason:'FR-03_ID_CONFLICT'};
    }
    if (typeof command !== 'string') return {id,status:'rejected',reason:'INVALID_COMMAND'};
    if (this.records.length >= 19990) throw Error('Export this mission and start a new session.');
    const start = performance.now(); this.record('command_requested', {id, command, value, role:this.role});
    const reason = guard(this.role,command,value,this.truth,this.catalog.commands);
    const result = {id,command,status:'rejected',reason};
    if (!reason) {
      this.record('command_transmitted',{id,command});
      try {const response = this.exchange(command,value);result.status = response.ok ? 'acknowledged' : 'rejected';result.reason = response.reason;}
      catch(error){result.status='failed';result.reason=error.message;this.running=false;}
    }
    result.latency_ms = performance.now()-start; this.record('command_terminal',result);
    this.cache.set(id,{command,value,result}); return result;
  }
  status() {
    const now=this.truth.telemetry.time, age=now-this.last_received, t=this.received.telemetry;
    const conditions = [
      [age>=3,'STALE','Downlink stale: do not treat last values as current.'],
      [t.battery_soc<20,'POWER','Battery below 20%; autonomous load shedding.'],
      [t.temperature>=50,'THERMAL','Bus temperature exceeds 50°C.'],
      [t.sensor_age>=3,'SENSOR','Attitude sensor stale.'],
      [Math.abs(t.wheel_rpm)>=6000,'WHEEL','Reaction wheel saturation.'],
      [t.missed_deadlines>0,'WATCHDOG','Injected missed deadlines recorded.']
    ];
    return structuredClone({epoch_ms:this.epoch_ms,received_at_ms:this.received_at_ms,run:this.id,role:this.role,state:this.received,sim_time:now,age,quality:age>=3?'STALE':!this.truth.telemetry.link_connected?'DISCONNECTED':'LIVE',running:this.running,speed:this.speed,failed:this.failed,procedure:this.procedure,alarms:conditions.filter(x=>x[0]).map(x=>({code:x[1],message:x[2],severity:'CRITICAL'}))});
  }
  startProcedure(key) {
    if (this.role==='observer') throw Error('ROLE_DENIED');
    if (!Object.hasOwn(this.catalog.procedures,key)) throw Error('UNKNOWN_PROCEDURE');
    this.procedure={key,index:0,complete:false,results:[]};this.record('procedure_start',this.procedure);return this.procedure;
  }
  advanceProcedure() {
    const p=this.procedure;
    if(!p||p.complete)throw Error('NO_ACTIVE_PROCEDURE');
    const result=this.command({id:crypto.randomUUID(),command:this.catalog.procedures[p.key].steps[p.index],value:0});
    p.results.push(result);if(result.status==='acknowledged')p.index++;
    p.complete=p.index===this.catalog.procedures[p.key].steps.length;this.record('procedure_step',p);return p;
  }
  export() {return {schema:'asteria-journal-v1',run:this.id,seed:this.seed,backend:'cpp-webassembly',records:structuredClone(this.records)};}
  save() {return {version:1,seed:this.seed,role:this.role,id:this.id,epoch_ms:this.epoch_ms,transcript:this.transcript,records:this.records,cache:[...this.cache],procedure:this.procedure,speed:this.speed};}
  static restore(engine,catalog,saved) {
    if(saved.version!==1 || !Array.isArray(saved.transcript) || saved.transcript.length>7200)throw Error('Unsupported saved mission');
    const m=new BrowserMission(engine,catalog,saved.seed,saved.role);
    for(const [command,value] of saved.transcript)m.exchange(command,value);
    m.id=saved.id;m.epoch_ms=saved.epoch_ms;m.records=saved.records;m.cache=new Map(saved.cache);m.procedure=saved.procedure;m.speed=saved.speed;m.running=false;
    return m;
  }
}
