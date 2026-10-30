/**
 * ANOMALIA'Z official fleet character coordinator (server-side core).
 *
 * An operator defines which server IDs are official and their perspective.
 * Clients can NEVER declare official status or force camera class. No community
 * world structures, buried storage, tents, or vehicles enter this registry.
 *
 * Intended to live behind an authenticated server-only API and a central,
 * transactional store. The in-memory implementation enables deterministic
 * testing and DOES NOT claim to be a deployed durable shared service.
 */
import {randomUUID} from 'node:crypto';

export class OfficialTransferError extends Error {
  constructor(code, message) { super(message); this.code=code; }
}
const deny=(code,message)=>{throw new OfficialTransferError(code,message)};
const id=v=>typeof v==='string'&&/^[a-zA-Z0-9][a-zA-Z0-9_.:-]{1,127}$/.test(v);
const finite=(x,min,max)=>typeof x==='number'&&Number.isFinite(x)&&x>=min&&x<=max;
const MAX_SNAPSHOT_BYTES=1024*1024;
/** Only portable player-owned fields. Everything placed in the world is excluded. */
export function sanitizePortableCharacter(snapshot) {
  if(!snapshot||typeof snapshot!=='object'||Array.isArray(snapshot))deny('INVALID_SNAPSHOT','Invalid survivor snapshot');
  const allowed=new Set(['inventory','worn','hands','survival','appearance','schemaVersion']);
  for(const key of Object.keys(snapshot)) if(!allowed.has(key))deny('WORLD_STATE_FORBIDDEN','World-owned objects cannot be transferred');
  if(snapshot.schemaVersion!==1)deny('INVALID_SNAPSHOT','Unsupported snapshot schema');
  const clean=structuredClone(snapshot);
  const bytes=Buffer.byteLength(JSON.stringify(clean),'utf8');
  if(bytes>MAX_SNAPSHOT_BYTES)deny('INVALID_SNAPSHOT','Survivor snapshot too large');
  if(!clean.survival||typeof clean.survival!=='object'||Array.isArray(clean.survival))
    deny('INVALID_SNAPSHOT','Missing survival state');
  for(const key of ['health','hunger','thirst']){
    if(!finite(clean.survival[key],0,100))deny('INVALID_SNAPSHOT','Invalid '+key);
  }
  for(const key of ['fatigue','stamina']) if(key in clean.survival&&!finite(clean.survival[key],0,100))deny('INVALID_SNAPSHOT','Invalid '+key);
  if('bodyTemperatureC'in clean.survival&&!finite(clean.survival.bodyTemperatureC,25,45))
    deny('INVALID_SNAPSHOT','Invalid body temperature');
  if('inventory' in clean && (!Array.isArray(clean.inventory)&&typeof clean.inventory!=='object'))
    deny('INVALID_SNAPSHOT','Invalid inventory');
  // Never attach a world transform to the destination. Spawn is server-owned.
  return Object.freeze(clean);
}
export function createOfficialCharacterRegistry({
  servers,
  spawnPoints,
  cooldownMs=90000,
  now=()=>Date.now(),
  pickIndex=(count)=>Math.floor(Math.random()*count),
}={}) {
  if(!servers||typeof servers!=='object')throw Error('Explicit trusted server catalog required');
  if(!spawnPoints||typeof spawnPoints!=='object')throw Error('Explicit protected inland spawn points required');
  if(!Number.isInteger(cooldownMs)||cooldownMs<0||cooldownMs>1800000)throw Error('Invalid cooldown');
  const approved=new Map();
  for(const [serverId,entry] of Object.entries(servers)) {
    if(!id(serverId)||!entry||entry.category!=='official'||typeof entry.thirdPerson!=='boolean')
      throw Error('Only operator-approved official servers allowed');
    approved.set(serverId,Object.freeze({thirdPerson:entry.thirdPerson}));
  }
  for(const p of ['1PP','3PP']) {
    if(!Array.isArray(spawnPoints[p])||spawnPoints[p].length<2)throw Error('At least two inland official spawns required for '+p);
    for(const s of spawnPoints[p]) if(!s||!finite(s.x,-2400000,2400000)||!finite(s.y,-2400000,2400000)||!finite(s.z,-2400000,2400000))
      throw Error('Invalid inland official spawn');
  }
  const records=new Map();
  const key=(player,cam)=>player+'|'+cam;
  const perspective=serverId=>{
    const s=approved.get(serverId);
    if(!s)deny('NOT_OFFICIAL','Official characters never migrate to community servers');
    return s.thirdPerson?'3PP':'1PP';
  };
  function checkIn({playerId,serverId}) {
    if(!id(playerId))deny('UNAUTHENTICATED','Only verified server-side player IDs are allowed');
    const view=perspective(serverId),k=key(playerId,view),time=now();
    const rec=records.get(k);
    if(rec?.active)deny('CHARACTER_ALREADY_ONLINE','Character is already active on an official server');
    if(rec && rec.lastServerId!==serverId && time<rec.lastLogoutAt+cooldownMs)
      deny('SERVER_HOP_COOLDOWN', 'Next official transfer available after '+(rec.lastLogoutAt+cooldownMs));
    const switched=!!rec&&rec.lastServerId!==serverId;
    const session= randomUUID(); // fencing token: only the holder can check out.
    const spawnList=spawnPoints[view];
    const selected=switched?spawnList[Math.min(spawnList.length-1,Math.max(0,pickIndex(spawnList.length)))]:null;
    const next={lastServerId:serverId,lastLogoutAt:rec?.lastLogoutAt??0,revision:rec?.revision??0,
      snapshot:rec?.snapshot??null,active:{serverId,session,startedAt:time},perspective:view};
    records.set(k,next);
    return {session,revision:next.revision,view,switched,spawn:switched?structuredClone(selected):null,
      // A newly-created official player gets a fresh identity for each view.
      snapshot:next.snapshot?structuredClone(next.snapshot):null};
  }
  function checkOut({playerId,serverId,session,snapshot}) {
    if(!id(playerId)||!id(session))deny('INVALID_IDENTITY','Invalid session identity');
    const view=perspective(serverId),k=key(playerId,view),record=records.get(k);
    if(!record||!record.active||record.active.serverId!==serverId||record.active.session!==session)
      deny('STALE_SESSION','Disconnected or superseded official session cannot write a character');
    const clean=sanitizePortableCharacter(snapshot);
    const updated={...record,snapshot:clean,active:null,revision:record.revision+1,lastLogoutAt:now()};
    records.set(k,updated);
    return {saved:true,revision:updated.revision,view};
  }
  function getStatus({playerId,serverId}) {
    if(!id(playerId))deny('UNAUTHENTICATED','Invalid player ID');
    const view=perspective(serverId),record=records.get(key(playerId,view));
    return {view,active:!!record?.active,hasCharacter:!!record?.snapshot,
      nextTransferAt:record?.lastLogoutAt?record.lastLogoutAt+cooldownMs:0};
  }
  return Object.freeze({checkIn,checkOut,getStatus,
    // Do not expose records or writing to ordinary players; transport must
    // enforce mTLS / signed official service credentials and persistence.
    _testingRecordCount:()=>records.size});
}
