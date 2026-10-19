export const COMPANION_TYPES={dog:{name:'Chien',speed:5.8,hp:100},wolf:{name:'Loup',speed:6.5,hp:120},raptor:{name:'Raptor',speed:8,hp:160}};
export function adoptCompanion(s,species='dog',free=false){const def=COMPANION_TYPES[species];if(!def)return {ok:false,message:'Animal inconnu.'};if(!free&&(s.inventory.food||0)<3)return {ok:false,message:'3 rations sont nécessaires pour adopter cet animal.'};if(!free)s.inventory.food-=3;
 s.companion={species,name:def.name,x:s.position.x+2,z:s.position.z+2,hp:def.hp,mode:'follow',hunger:100,cooldown:0,underground:s.underground||null};return {ok:true,message:def.name+' te rejoint.'};}
export function companionCommand(s,mode){if(!s.companion)return {ok:false,message:'Aucun compagnon.'};if(!['follow','stay','guard'].includes(mode))return {ok:false,message:'Ordre inconnu.'};s.companion.mode=mode;return {ok:true,message:{follow:'Il te suit.',stay:'Il reste ici.',guard:'Il protège cette zone.'}[mode]}}
export function feedCompanion(s){if(!s.companion)return {ok:false,message:'Aucun compagnon.'};const food=['cooked_meat','meat','cooked_fish','food'].find(id=>(s.inventory[id]||0)>0);if(!food)return {ok:false,message:'Nourriture nécessaire.'};s.inventory[food]--;s.companion.hunger=100;s.companion.hp=Math.min(COMPANION_TYPES[s.companion.species].hp,s.companion.hp+25);return {ok:true,message:'Compagnon nourri.'}}
export function tickCompanion(s,dt,{heightAt,move,followDistance=3,teleportDistance=90,enemies=[]}){
 const pet=s.companion;if(!pet||pet.hp<=0)return;dt=Math.min(.1,Math.max(0,dt));pet.cooldown=Math.max(0,(pet.cooldown||0)-dt);pet.hunger=Math.max(0,pet.hunger-dt*.008);
 const distance=Math.hypot(s.position.x-pet.x,s.position.z-pet.z);
 if(pet.mode==='follow'){
  if((pet.underground||null)!==(s.underground||null)||distance>teleportDistance&&!s.activeVehicle&&!s.boat){pet.x=s.position.x+2;pet.z=s.position.z+2;pet.underground=s.underground||null;}
  else if(distance>followDistance&&!s.activeVehicle&&!s.boat){const speed=COMPANION_TYPES[pet.species].speed*(pet.hunger>0?1:.5);const step=Math.min(speed*dt,distance-followDistance);const p=move({x:pet.x,z:pet.z},(s.position.x-pet.x)/distance*step,(s.position.z-pet.z)/distance*step);pet.x=p.x;pet.z=p.z;}
 }
 if(pet.mode!=='stay'&&(pet.underground||null)===(s.underground||null)){
  const enemy=enemies.find(e=>e.alive&&Math.hypot(e.x-pet.x,e.z-pet.z)<8);
  if(enemy&&pet.cooldown===0){enemy.hp-=22;pet.hp=Math.max(0,pet.hp-3);pet.cooldown=1.4;if(enemy.hp<=0){enemy.alive=false;if(enemy.mesh)enemy.mesh.visible=false;}}
 }
}
