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
  if('inventory' in clean) {
    const inventory=clean.inventory;
    if(!inventory||typeof inventory!=='object')deny('INVALID_SNAPSHOT','Invalid inventory');
    if(!Array.isArray(inventory)) {
      // This mirrors Unreal InventoryComponent::ExportInventoryObject:
      // compartments and stacks belong to the character, never the map.
      const allowedInventory=new Set(['schemaVersion','layoutVersion','weightCapacityKg','compartments','stacks']);
      for(const key of Object.keys(inventory))
        if(!allowedInventory.has(key))deny('WORLD_STATE_FORBIDDEN','Nonportable inventory state');
      if(inventory.schemaVersion!==1||inventory.layoutVersion!==2||
         !Array.isArray(inventory.compartments)||!Array.isArray(inventory.stacks))
        deny('INVALID_SNAPSHOT','Invalid UE5 inventory layout');
      if(inventory.stacks.length>512||inventory.compartments.length>128)
        deny('INVALID_SNAPSHOT','Character storage exceeds validated limits');
    }
    const stacks=Array.isArray(inventory)?inventory:inventory.stacks;
    if(stacks.length>512)deny('INVALID_SNAPSHOT','Too many carried items');
    for(const stack of stacks) {
      if(!stack||typeof stack!=='object'||Array.isArray(stack)||
         typeof stack.itemId!=='string'||!/^[A-Za-z0-9_.:-]{1,128}$/.test(stack.itemId)||
         !Number.isSafeInteger(stack.count)||stack.count<1||stack.count>1000000)
        deny('INVALID_SNAPSHOT','Malformed carried item stack');
      const allowedStack=new Set(['stackId','itemId','count','containerId','x','y','rotated','condition','container']);
      for(const key of Object.keys(stack))
        if(!allowedStack.has(key))deny('WORLD_STATE_FORBIDDEN','World ownership cannot hide inside inventory');
      if('containerId'in stack&&!/^[A-Za-z0-9_.:-]{1,128}$/.test(String(stack.containerId)))
        deny('INVALID_SNAPSHOT','Invalid inventory container');
    }
  }
  // Never attach a world transform to the destination. Spawn is server-owned.
  return Object.freeze(clean);
}
export function createOfficialCharacterRegistry({
  servers,
  spawnPoints,
  cooldownMs=90000,
  now=()=>Date.now(),
  pickIndex=(count)=>Math.floor(Math.random()*count),
  initialRecords={},
  persist=()=>{},
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
  if(!initialRecords||typeof initialRecords!=='object'||Array.isArray(initialRecords))
    throw Error('Invalid central registry recovery state');
  const records=new Map();
  for(const [k,record] of Object.entries(initialRecords)){
    const [player,view,...rest]=k.split('|');
    if(!id(player)||!['1PP','3PP'].includes(view)||rest.length||
       !record||typeof record!=='object'||!Number.isSafeInteger(record.revision)||
       record.revision<0||!approved.has(record.lastServerId)||
       (approved.get(record.lastServerId).thirdPerson?'3PP':'1PP')!==view)
      throw Error('Invalid persisted character registry state; refusing startup');
    if(record.snapshot)sanitizePortableCharacter(record.snapshot);
    if(record.active && (!approved.has(record.active.serverId)||
       typeof record.active.session!=='string'||!id(record.active.session)))
      throw Error('Unresolved official session must be recovered by operator');
    records.set(k,structuredClone(record));
  }
  const commit=(k,record)=>{
    const next=Object.fromEntries(records);
    next[k]=record;
    persist(structuredClone(next)); // Durable write MUST succeed before state becomes live.
    records.set(k,record);
  };
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
    commit(k,next);
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
    commit(k,updated);
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
