/** ANOMALIA Cryo vault: original gameplay data model, independent of ARK mod assets.
 * Server-authoritative persistence and 3D world spawning must be wired separately.
 * Actor identities/roles must come from trusted server state, not a client payload.
 */
export const CRYO_DEFAULTS=Object.freeze({range:35,capacity:null,allowHybrids:true,autoCollectBabies:false,incubateEggs:false,passiveResources:false,cryoSickness:false});
const clone=x=>JSON.parse(JSON.stringify(x));
const identity=id=>typeof id==='string'&&id.trim().length>0;
const validTerminal=t=>!!t&&identity(t.id)&&identity(t.ownerId)&&!!t.options&&Array.isArray(t.creatures)&&Number.isFinite(t.options.range)&&t.options.range>=1&&t.options.range<=200&&(t.options.capacity===null||Number.isSafeInteger(t.options.capacity)&&t.options.capacity>=0);
function checkedOptions(current,changes){
 if(!changes||typeof changes!=='object'||Array.isArray(changes))return null;
 const next={...current};
 for(const key of Object.keys(CRYO_DEFAULTS))if(Object.hasOwn(changes,key)){
  const v=changes[key];
  if(key==='range'){
   if(!Number.isFinite(v))return null;
   next.range=Math.max(1,Math.min(200,v));
  }else if(key==='capacity'){
   if(v!==null&&(!Number.isSafeInteger(v)||v<0))return null;
   next.capacity=v;
  }else{
   if(typeof v!=='boolean')return null;
   next[key]=v;
  }
 }
 return next;
}
export function createCryoTerminal({id,ownerId,position,options={}}){
 if(!identity(id)||!identity(ownerId))throw Error('Terminal requires ID and owner');
 if(!position||!Number.isFinite(position.x)||!Number.isFinite(position.z)||Object.hasOwn(position,'y')&&!Number.isFinite(position.y))throw Error('Terminal requires finite position');
 const settings=checkedOptions({...CRYO_DEFAULTS,...options},options);
 if(!settings)throw Error('Invalid cryo options');
 return {id,ownerId,position:clone(position),options:settings,creatures:[],eggs:[]};
}
export function canAccessCryo(terminal,actor){return validTerminal(terminal)&&identity(actor?.id)&&(actor.id===terminal.ownerId||actor.isAdmin===true||Array.isArray(terminal.allowedIds)&&terminal.allowedIds.includes(actor.id));}
export function captureCreature(terminal,creature,actor,{viaGun=false,distance=0,adminMode=false}={}){
 if(!canAccessCryo(terminal,actor))return {ok:false,reason:'forbidden'};
 const authorizedAdmin=adminMode===true&&actor?.isAdmin===true;
 if(!identity(creature?.id)||(!authorizedAdmin&&(creature.tamed!==true||creature.ownerId!==actor.id&&!(Array.isArray(terminal.allowedIds)&&terminal.allowedIds.includes(creature.ownerId)))))return {ok:false,reason:'not-owned-or-not-tamed'};
 if(creature.dead||creature.stored||creature.inCombat&&!authorizedAdmin)return {ok:false,reason:'unavailable'};
 if(creature.hybrid&&terminal.options.allowHybrids===false)return {ok:false,reason:'hybrids-disabled'};
 if(!Number.isFinite(distance)||distance<0||viaGun&&distance>terminal.options.range&&!authorizedAdmin)return {ok:false,reason:'out-of-range'};
 if(terminal.creatures.some(c=>c.id===creature.id))return {ok:false,reason:'duplicate'};
 if(terminal.options.capacity!==null&&terminal.creatures.length>=terminal.options.capacity)return {ok:false,reason:'full'};
 const stored=clone(creature);stored.stored=true;stored.storedAt=Date.now();
 terminal.creatures.push(stored);
 // The authoritative world record must also change; otherwise another terminal
 // can capture the same still-referenced creature before its actor is removed.
 creature.stored=true;
 return {ok:true,creatureId:creature.id,removeWorldEntity:true};
}
export function releaseCreature(terminal,id,actor,{spawnAllowed=true}={}){
 if(!canAccessCryo(terminal,actor))return {ok:false,reason:'forbidden'};
 if(spawnAllowed!==true)return {ok:false,reason:'unsafe-spawn'};
 const i=terminal.creatures.findIndex(c=>c.id===id);
 if(i<0)return {ok:false,reason:'not-found'};
 const creature=clone(terminal.creatures[i]);creature.stored=false;delete creature.storedAt;
 terminal.creatures.splice(i,1);
 return {ok:true,creature,spawnWorldEntity:true,cryoSickness:terminal.options.cryoSickness};
}
export function configureCryo(terminal,actor,changes){
 if(!canAccessCryo(terminal,actor)||(actor.id!==terminal.ownerId&&actor.isAdmin!==true))return false;
 const next=checkedOptions(terminal.options,changes);
 if(!next)return false;
 terminal.options=next;
 return true;
}

/** Client-visible color is derived from server-validated role, not trusted as permission. */
export function cryoGunMode(actor,requestedAdminMode=false){
 const admin=Boolean(requestedAdminMode&&actor?.isAdmin===true);
 return {adminMode:admin,color:admin?'#ff9a25':'#19d9ee',label:admin?'CAPTURE ADMIN':'CAPTURE NORMALE'};
}
export function toggleCryoGunMode(actor,currentMode=false){
 return cryoGunMode(actor,!currentMode);
}
