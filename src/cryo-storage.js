/** ANOMALIA Cryo vault: original gameplay data model, independent of ARK mod assets.
 * Server-authoritative persistence and 3D world spawning must be wired separately.
 */
export const CRYO_DEFAULTS=Object.freeze({range:35,capacity:null,allowHybrids:true,autoCollectBabies:false,incubateEggs:false,passiveResources:false,cryoSickness:false});
const clone=x=>JSON.parse(JSON.stringify(x));
export function createCryoTerminal({id,ownerId,position,options={}}){
 if(!id||!ownerId)throw Error('Terminal requires ID and owner');
 return {id,ownerId,position:clone(position),options:{...CRYO_DEFAULTS,...options},creatures:[],eggs:[]};
}
export function canAccessCryo(terminal,actor){return !!actor&&(actor.id===terminal.ownerId||actor.isAdmin===true||terminal.allowedIds?.includes(actor.id));}
export function captureCreature(terminal,creature,actor,{viaGun=false,distance=0}={}){
 if(!canAccessCryo(terminal,actor))return {ok:false,reason:'forbidden'};
 if(!creature?.id||!creature.tamed||creature.ownerId!==actor.id&&!actor.isAdmin&&!terminal.allowedIds?.includes(creature.ownerId))return {ok:false,reason:'not-owned-or-not-tamed'};
 if(creature.dead||creature.stored||creature.inCombat)return {ok:false,reason:'unavailable'};
 if(creature.hybrid&&terminal.options.allowHybrids===false)return {ok:false,reason:'hybrids-disabled'};
 if(viaGun&&distance>terminal.options.range)return {ok:false,reason:'out-of-range'};
 if(terminal.creatures.some(c=>c.id===creature.id))return {ok:false,reason:'duplicate'};
 if(terminal.options.capacity!==null&&terminal.creatures.length>=terminal.options.capacity)return {ok:false,reason:'full'};
 const stored=clone(creature);stored.stored=true;stored.storedAt=Date.now();
 terminal.creatures.push(stored);
 return {ok:true,creatureId:creature.id,removeWorldEntity:true};
}
export function releaseCreature(terminal,id,actor,{spawnAllowed=true}={}){
 if(!canAccessCryo(terminal,actor))return {ok:false,reason:'forbidden'};
 if(!spawnAllowed)return {ok:false,reason:'unsafe-spawn'};
 const i=terminal.creatures.findIndex(c=>c.id===id);
 if(i<0)return {ok:false,reason:'not-found'};
 const creature=clone(terminal.creatures[i]);creature.stored=false;delete creature.storedAt;
 terminal.creatures.splice(i,1);
 return {ok:true,creature,spawnWorldEntity:true,cryoSickness:terminal.options.cryoSickness};
}
export function configureCryo(terminal,actor,changes){
 if(!canAccessCryo(terminal,actor))return false;
 const permitted=['range','capacity','allowHybrids','autoCollectBabies','incubateEggs','passiveResources','cryoSickness'];
 for(const key of permitted)if(Object.hasOwn(changes,key)){
  const v=changes[key];
  if(key==='range')terminal.options.range=Math.max(1,Math.min(200,Number(v)||35));
  else if(key==='capacity')terminal.options.capacity=v===null?null:Math.max(0,Math.floor(Number(v)||0));
  else terminal.options[key]=Boolean(v);
 }
 return true;
}
