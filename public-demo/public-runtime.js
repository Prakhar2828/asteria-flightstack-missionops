// Explicit local adapter: no hosted API, accounts or network command delivery.
(function(){
  let mission=null,engine,catalog,saveError='';
  const savedKey='asteria-public-mission-v1';
  const ready=(async()=>{
    const [{BrowserMission},data,module]=await Promise.all([import('./runtime-core.mjs'),fetch('./catalog.json').then(r=>{if(!r.ok)throw Error('Catalog unavailable');return r.json();}),createAsteria()]);
    catalog=data;
    engine={reset:module.cwrap('reset_flight',null,['number']),exchange:(command,value)=>JSON.parse(module.ccall('exchange_flight','string',['string','number'],[command,value]))};
    try{const raw=sessionStorage.getItem(savedKey);if(raw)mission=BrowserMission.restore(engine,catalog,JSON.parse(raw));}catch(error){sessionStorage.removeItem(savedKey);sessionStorage.removeItem('asteria-token');saveError='Previous browser session could not be restored. Start a new mission.';}
    return BrowserMission;
  })();
  function save(){if(mission)try{sessionStorage.setItem(savedKey,JSON.stringify(mission.save()));saveError='';}catch(error){saveError='Browser storage is full. Export the mission before leaving this page.';mission.running=false;sessionStorage.removeItem(savedKey);const n=document.getElementById('notice');if(n)n.textContent=saveError;}}
  function requireMission(){if(!mission)throw Error(saveError||'Initialize a mission first.');return mission;}
  async function api(path,body){
    const Mission=await ready;const url=new URL(path,'https://local.invalid');
    if(url.pathname==='/api/catalog')return catalog;
    if(url.pathname==='/api/session'){
      mission=new Mission(engine,catalog,body.seed,body.role);save();return {token:mission.id,...mission.status()};
    }
    const m=requireMission();let result;
    switch(url.pathname){
      case '/api/status':return m.status();
      case '/api/command':result=m.command(body);break;
      case '/api/control':
        if(m.role==='observer')throw Error('ROLE_DENIED');
        if(body.action==='run')m.running=true;
        else if(body.action==='pause')m.running=false;
        else if(body.action==='step')m.step(body.value);
        else if(body.action==='speed'){if(![1,10,60].includes(body.value))throw Error('Invalid speed');m.speed=body.value;}
        else throw Error('Unknown control');
        m.record('simulation_control',body);result=m.status();break;
      case '/api/procedure':result=body.action?m.advanceProcedure():m.startProcedure(body.key);break;
      case '/api/records':{
        const after=Number(url.searchParams.get('after')||0), rows=m.records.filter(r=>r.id>after).slice(0,2000);
        return {run:m.id,records:structuredClone(rows),next_cursor:rows.at(-1)?.id||after,has_more:rows.length===2000};
      }
      case '/api/export':return m.export();
      case '/api/close':mission=null;sessionStorage.removeItem(savedKey);return {closed:true};
      default:
        if(url.pathname.startsWith('/api/history/')){
          const key=url.pathname.split('/').pop(),start=Number(url.searchParams.get('start')||0),end=Number(url.searchParams.get('end')||1e16);
          if(!Object.hasOwn(catalog.channels,key))throw Error('Unknown channel');
          return m.records.filter(r=>r.kind==='telemetry'&&m.epoch_ms+r.sim*1000>=start&&m.epoch_ms+r.sim*1000<=end).map(r=>({timestamp:m.epoch_ms+r.sim*1000,value:r.data.telemetry[key],id:r.id,quality:'RECEIVED'}));
        }
        throw Error('Unsupported demo operation');
    }
    save();return structuredClone(result);
  }
  function socket(){
    let interval=null,sequence=0,closed=false;
    const connection={send:()=>{if(closed)return;interval=setInterval(()=>{if(mission&&!closed)connection.onmessage?.({data:JSON.stringify({sequence:++sequence,sent_at_ms:Date.now(),status:mission.status()})});},250);},close:()=>{closed=true;clearInterval(interval);connection.onclose?.();}};
    ready.then(()=>setTimeout(()=>{if(!closed)connection.onopen?.();},0)).catch(()=>connection.onclose?.());return connection;
  }
  setInterval(()=>{if(mission?.running){try{mission.step(mission.speed);save();}catch(error){mission.running=false;const n=document.getElementById('notice');if(n)n.textContent=error.message;}}},1000);
  window.addEventListener('pagehide',save);
  window.AsteriaPublic={api,socket};
})();
