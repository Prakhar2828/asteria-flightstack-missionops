'use strict';
// Asteria's provider implements the public Open MCT object, composition and telemetry APIs.
(async function () {
  const message = document.getElementById('stream-status');
  const token = sessionStorage.getItem('asteria-token');
  if (!token) { message.textContent = 'Initialize a mission in the console first.'; return; }
  const headers = {Authorization: 'Bearer ' + token};
  async function get(path) {
    const response = await fetch(path, {headers});
    if (!response.ok) throw new Error('Session unavailable: ' + response.status);
    return response.json();
  }
  try {
    const catalog = await get('/api/catalog');
    const initial = await get('/api/status');
    const namespace = 'asteria';
    const groups = {
      power: ['battery_soc','bus_voltage','solar_power','load_power','sunlight'],
      thermal: ['temperature','heater'],
      attitude: ['attitude','angular_rate','wheel_rpm','target_angle','sensor_age','adcs_enabled'],
      communications: ['link_connected','link_age','packets'],
      payload: ['payload_enabled','payload_data'],
      events: ['time','ticks','missed_deadlines','commands_accepted','commands_rejected','healthy','healthy_dwell','orbit_phase']
    };
    const listeners = new Map();
    let lastTime = -1;
    openmct.setAssetPath('/vendor/openmct');
    openmct.install(openmct.plugins.LocalStorage());
    openmct.install(openmct.plugins.MyItems());
    openmct.install(openmct.plugins.UTCTimeSystem());
    openmct.install(openmct.plugins.Espresso());
    openmct.time.timeSystem('utc', {start:initial.epoch_ms, end:initial.epoch_ms+Math.max(initial.sim_time,60)*1000});
    openmct.types.addType('asteria.channel', {name:'Asteria telemetry',cssClass:'icon-telemetry',description:'Synthetic spacecraft telemetry from the authoritative C++ process.'});
    openmct.objects.addRoot({namespace,key:'spacecraft'});
    openmct.objects.addProvider(namespace, {
      get(identifier) {
        const key = identifier.key;
        if (key === 'spacecraft') return Promise.resolve({identifier,name:'ASTERIA-01 · synthetic',type:'folder',location:'ROOT'});
        if (groups[key]) return Promise.resolve({identifier,name:key.toUpperCase(),type:'folder',location:namespace+':spacecraft'});
        const channel = catalog.channels[key];
        if (!channel) return Promise.reject(new Error('Unknown Asteria channel'));
        const group = Object.keys(groups).find(g=>groups[g].includes(key));
        return Promise.resolve({identifier,name:channel[0],type:'asteria.channel',location:namespace+':'+group,
          telemetry:{values:[
            {key:'value',name:channel[0],units:channel[1],format:'float',hints:{range:1}},
            {key:'utc',name:'Simulation UTC projection',format:'utc',hints:{domain:1}}
          ]}});
      }
    });
    openmct.composition.addProvider({
      appliesTo:object=>object.identifier.namespace===namespace && object.type==='folder',
      load:object=>Promise.resolve((object.identifier.key==='spacecraft'?Object.keys(groups):groups[object.identifier.key]).map(key=>({namespace,key})))
    });
    openmct.telemetry.addProvider({
      supportsRequest:object=>object.type==='asteria.channel',
      request:(object,options)=>get('/api/history/'+encodeURIComponent(object.identifier.key)+'?start='+options.start+'&end='+options.end).then(rows=>rows.map(row=>({...row,utc:row.timestamp}))),
      supportsSubscribe:object=>object.type==='asteria.channel',
      subscribe(object, callback) {
        const key=object.identifier.key;
        if (!listeners.has(key)) listeners.set(key,new Set());
        listeners.get(key).add(callback);
        return ()=>{listeners.get(key)?.delete(callback);if(!listeners.get(key)?.size)listeners.delete(key);};
      }
    });
    openmct.start(document.getElementById('openmct-app'));
    function connect() {
      const socket=new WebSocket(location.origin.replace(/^http/,'ws')+'/api/stream');
      socket.onopen=()=>socket.send(JSON.stringify({token}));
      socket.onmessage=event=>{
        const {status}=JSON.parse(event.data);
        const telemetry=status.state.telemetry;
        message.textContent='SYNTHETIC · '+status.quality+' · MET '+status.sim_time+' s';
        if(status.quality!=='LIVE')return;
        const timestamp=status.epoch_ms+telemetry.time*1000;
        if(document.getElementById('follow').checked)openmct.time.bounds({start:Math.max(status.epoch_ms,timestamp-900000),end:Math.max(status.epoch_ms+1000,timestamp)});
        if(timestamp===lastTime)return;
        lastTime=timestamp;
        for(const [key,callbacks]of listeners)for(const callback of callbacks)callback({utc:timestamp,value:telemetry[key],quality:'LIVE'});
      };
      socket.onclose=()=>{message.textContent='Stream disconnected. Return to the console to reconnect.';};
      socket.onerror=()=>{message.textContent='Stream error; no fresh telemetry is being displayed.';};
      window.addEventListener('pagehide',()=>socket.close(),{once:true});
    }
    connect();
  } catch(error) {message.textContent=error.message;console.error(error);}
})();
