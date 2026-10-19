import {hash2,CITIES} from './mechanics.js';
import {ITEM_DEFS} from './systems.js';
export const EVENT_TYPES={HelicopterCrash:'Épave d’hélicoptère',TrainCrash:'Train accidenté',ShipCrash:'Épave de bateau'};
export function tickEconomy(s,config,now){
 s.groundDrops??=[];s.lootTimers??={};s.worldEvents??=[];s.eventTimers??={};
 s.groundDrops=s.groundDrops.filter(d=>!d.expires||d.expires>now);
 if(config.economy.loot&&config.globals.LootEnabled!==0){
  let budget=300;
  for(const type of config.types){if(!ITEM_DEFS[type.id])continue;const nominal=Math.min(budget,Math.floor(type.nominal*(config.globals.LootMultiplier??1)));budget-=nominal;
   const existing=s.groundDrops.filter(d=>d.id===type.id&&d.uid.startsWith('ce-')).length;
   const replenish=existing<=Math.min(type.min,nominal);
   for(let i=0;i<nominal;i++){
    const id='ce-'+type.id+'-'+i;if(s.groundDrops.some(d=>d.uid===id)){s.lootTimers[id]=now+type.restock;continue}
    if(s.lootTimers[id]===undefined||config.economy.lootRespawn&&replenish&&s.lootTimers[id]<=now){
     const city=CITIES[i%CITIES.length],gx=Math.round((city.x+(hash2(i,type.id.length,522)-.5)*city.radius)/76),gz=Math.round((city.z+(hash2(i,type.id.length,923)-.5)*city.radius)/76);
     s.groundDrops.push({uid:id,id:type.id,count:type.quantity,x:gx*76+52,z:gz*76+52,underground:null,expires:now+type.lifetime});s.lootTimers[id]=now+type.restock;
    }
   }
  }
 }
 if(config.economy.events){
  s.worldEvents=s.worldEvents.filter(e=>e.expires>now);
  for(const spec of config.events){if(!spec.active||!EVENT_TYPES[spec.name])continue;for(let i=0;i<Math.min(spec.nominal,spec.positions.length);i++){
   const id=spec.name+'-'+i;if(s.worldEvents.some(e=>e.id===id)){s.eventTimers[id]=now+spec.restock;continue}
   if(s.eventTimers[id]!==undefined&&(!config.economy.eventRespawn||s.eventTimers[id]>now))continue;
   const p=spec.positions[i];s.worldEvents.push({id,type:spec.name,...p,expires:now+spec.lifetime});s.eventTimers[id]=now+spec.restock;
   for(const [j,item]of spec.cargo.entries())if(ITEM_DEFS[item.id])s.groundDrops.push({uid:'event-'+id+'-'+Math.floor(now)+'-'+j,id:item.id,count:item.count,x:p.x+3+j*.7,z:p.z+3,underground:null,expires:now+spec.lifetime});
  }}
 }
}
