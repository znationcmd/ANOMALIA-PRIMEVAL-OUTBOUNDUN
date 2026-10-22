/** ANOMALIA original NPC recruitment and base-assignment prototype.
 * NPCs are fictional characters. Capturing is non-lethal; no torture simulation.
 * Dedicated servers must validate actor permissions and persist changes atomically.
 * Actor identities/roles must come from trusted server state, not a client payload.
 */
export const NPC_ROLES=Object.freeze(['fighter','archer','performer','blacksmith','tanner','carpenter','cook','farmer']);
export const RECRUITMENT_CONFIG=Object.freeze({maxTorpor:100,clubTorpor:25,restorationSeconds:120,ropeMaxDistance:14,baseTrainingSeconds:90});
const clamp=(v,min,max)=>Math.max(min,Math.min(max,Number(v)||0));
const identity=id=>typeof id==='string'&&id.trim().length>0;
const canManage=(station,actor)=>!!station&&identity(station.id)&&identity(station.ownerId)&&Array.isArray(station.recruits)&&identity(actor?.id)&&(station.ownerId===actor.id||actor.isAdmin===true);
export function strikeNonlethal(npc,{torpor=25}={}){
 if(!npc||npc.dead||npc.recruited||npc.inStation||!Number.isFinite(torpor)||torpor<=0||!Number.isFinite(npc.torpor??0))return {ok:false,reason:'invalid-target'};
 npc.torpor=clamp((npc.torpor||0)+torpor,0,100);
 npc.unconscious=npc.torpor>=100;
 return {ok:true,unconscious:npc.unconscious,torpor:npc.torpor};
}
export function bindNpc(npc,actor,{hasRope=false,distance=Infinity}={}){
 if(!npc?.unconscious||npc.dead||npc.inStation||npc.recruited||hasRope!==true||!Number.isFinite(distance)||distance<0||distance>3||!identity(actor?.id))return {ok:false,reason:'cannot-bind'};
 if(npc.boundBy&&npc.boundBy!==actor.id)return {ok:false,reason:'already-bound'};
 npc.boundBy=actor.id;return {ok:true};
}
export function dragNpc(npc,actor,{distance=0,climbing=false}={}){
 if(!npc?.boundBy||npc.boundBy!==actor?.id)return {ok:false,reason:'not-bound'};
 if(!Number.isFinite(distance)||distance<0)return {ok:false,reason:'invalid-distance'};
 if(distance>RECRUITMENT_CONFIG.ropeMaxDistance||climbing){npc.boundBy=null;return {ok:false,reason:'rope-broken'};}
 return {ok:true,speedMultiplier:0.5};
}
export function createRecruitmentStation(id,ownerId){
 if(!identity(id)||!identity(ownerId))throw Error('Recruitment station requires ID and owner');
 return {id,ownerId,recruits:[],active:true};
}
export function admitNpc(station,npc,actor){
 if(!canManage(station,actor))return {ok:false,reason:'forbidden'};
 if(!station.active||!identity(npc?.id)||!npc.unconscious||npc.dead||npc.inStation||npc.recruited||npc.boundBy!==actor.id||station.recruits.some(x=>x.id===npc.id)||!Number.isFinite(npc.level??1))return {ok:false,reason:'invalid-recruit'};
 station.recruits.push({id:npc.id,role:NPC_ROLES.includes(npc.role)?npc.role:'fighter',level:clamp(npc.level??1,1,100),progress:0,status:'training',name:npc.name||'Recrue'});
 npc.boundBy=null;npc.inStation=true;return {ok:true,removeWorldEntity:true};
}
export function advanceRecruitment(station,seconds,{supplies=0}={}){
 if(!station?.active||!Array.isArray(station.recruits)||!Number.isFinite(supplies)||supplies<=0||!Number.isFinite(seconds)||seconds<=0)return [];
 const ready=[];
 for(const recruit of station.recruits){if(recruit.status!=='training')continue;
  recruit.progress=clamp(recruit.progress+Math.max(0,seconds)/(RECRUITMENT_CONFIG.baseTrainingSeconds*recruit.level)*100,0,100);
  if(recruit.progress>=100){recruit.status='ready';ready.push(recruit.id);}
 }return ready;
}
export function deployRecruit(station,id,actor,{role,placementAllowed=true}={}){
 if(!canManage(station,actor))return {ok:false,reason:'forbidden'};
 const i=station.recruits.findIndex(n=>n.id===id&&n.status==='ready');
 if(i<0||placementAllowed!==true)return {ok:false,reason:'not-ready-or-invalid-placement'};
 const recruit=station.recruits.splice(i,1)[0];
 recruit.role=NPC_ROLES.includes(role)?role:recruit.role;
 return {ok:true,recruit:{...recruit,ownerId:station.ownerId,status:'deployed'},spawnWorldEntity:true};
}
export function assignRecruit(recruit,role,{workshopType,actor}={}){
 if(!recruit||recruit.status!=='deployed'||!NPC_ROLES.includes(role)||!identity(actor?.id)||(actor.id!==recruit.ownerId&&actor.isAdmin!==true))return false;
 if(workshopType&&!['blacksmith','tanner','carpenter','cook','farmer'].includes(role))return false;
 recruit.role=role;recruit.workshopType=workshopType||null;return true;
}
