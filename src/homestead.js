/** ANOMALIA homestead prototype. Safe, bounded solo state updates (not yet a UE5 feature). */
export const HOMESTEAD_TYPES=Object.freeze({
 bed:{label:'Lit et couchage',category:'furniture',width:2.1,depth:3.1,color:0x8b786a},
 sofa:{label:'Canapé',category:'furniture',width:3.2,depth:1.3,color:0x65696f},
 table:{label:'Table',category:'furniture',width:2.5,depth:1.6,color:0x8d7456},
 chair:{label:'Chaise',category:'furniture',width:.75,depth:.75,color:0x6e5848},
 wardrobe:{label:'Armoire',category:'furniture',width:2.1,depth:.8,color:0x806752},
 shelf:{label:'Étagère',category:'furniture',width:2.2,depth:.7,color:0x8a7a62},
 kitchen:{label:'Cuisine',category:'furniture',width:3.2,depth:1,color:0x777f77},
 lamp:{label:'Lampe',category:'furniture',width:.5,depth:.5,color:0xc6b27f},
 cow_pen:{label:'Enclos à vaches · lait',category:'farm',width:18,depth:14,color:0x8c815e},
 chicken_coop:{label:'Poulailler · œufs',category:'farm',width:8,depth:7,color:0xb29b6e},
 beehive:{label:'Ruche · miel',category:'farm',width:2,depth:2,color:0x9f824c},
 doghouse:{label:'Niche du compagnon',category:'farm',width:3,depth:3,color:0x9a795b},
 barn:{label:'Grange',category:'farm',width:22,depth:18,color:0x966c56},
 tractor_shed:{label:'Hangar à tracteur',category:'farm',width:14,depth:12,color:0x81867e},
 garden:{label:'Potager',category:'farm',width:10,depth:10,color:0x547650}
});
export const FARM_PRODUCTION=Object.freeze({
 cow_pen:{item:'milk',label:'lait',quantity:2,cooldownMs:12*60*1000},
 chicken_coop:{item:'eggs',label:'œufs',quantity:3,cooldownMs:8*60*1000},
 beehive:{item:'honey',label:'miel',quantity:1,cooldownMs:15*60*1000}
});
const clamp=(x,min,max)=>Math.min(max,Math.max(min,x));
export function sleepTick(state,seconds,{sprinting=false}={}){
 if(!Number.isFinite(seconds)||seconds<=0)return;
 state.sleep=clamp(Number.isFinite(state.sleep)?state.sleep:100,0,100);
 state.sleep=clamp(state.sleep-Math.min(seconds,.25)*(sprinting ? .017 : .008),0,100);
 if(state.sleep<=5)state.stamina=clamp((state.stamina||0)-.5*Math.min(seconds,.25),0,100);
}
export function restAtBed(state,objects,now=Date.now()){
 const nearest=objects?.find(o=>o.type==='bed'&&Math.hypot(o.x-state.position.x,o.z-state.position.z)<=3.5);
 if(!nearest)return {ok:false,message:'Approche-toi d’un lit posé dans ta maison (3,5 m).'};
 if(!Number.isFinite(now)||now-(state.lastRestAt||0)<60_000)return {ok:false,message:'Tu viens de te reposer.'};
 if(state.health<=0)return {ok:false,message:'Impossible de dormir dans cet état.'};
 state.sleep=clamp((state.sleep||0)+65,0,100);
 state.stamina=clamp((state.stamina||0)+35,0,100);
 state.lastRestAt=now;
 return {ok:true,message:'Repos au lit : sommeil et endurance récupérés.'};
}
export function collectFarmProduce(state,objects,now=Date.now()){
 if(!Number.isFinite(now)||now<0)return {ok:false,message:'Horloge incorrecte.'};
 const target=objects?.filter(o=>FARM_PRODUCTION[o.type])
  .map(o=>({object:o,dist:Math.hypot(o.x-state.position.x,o.z-state.position.z)}))
  .filter(o=>o.dist<=7).sort((a,b)=>a.dist-b.dist)[0]?.object;
 if(!target)return {ok:false,message:'Approche-toi d’un enclos, d’un poulailler ou d’une ruche (7 m).'};
 const product=FARM_PRODUCTION[target.type];
 state.farmHarvests??={};
 const last=state.farmHarvests[target.id];
 if(Number.isFinite(last)&&now-last<product.cooldownMs)return {ok:false,message:'La production n’est pas encore prête.'};
 state.farmHarvests[target.id]=now;
 state.inventory??={};
 state.inventory[product.item]=clamp((state.inventory[product.item]||0)+product.quantity,0,9999);
 return {ok:true,message:`Récolte : +${product.quantity} ${product.label}.`,item:product.item,quantity:product.quantity};
}
