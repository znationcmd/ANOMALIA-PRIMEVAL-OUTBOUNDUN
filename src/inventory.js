import {ITEM_DEFS,capacity,weight} from './systems.js';
export const SLOT_LABELS={head:'Tête',torso:'Veste',vest:'Gilet',legs:'Pantalon',feet:'Chaussures',back:'Sac à dos'};
export function itemSize(id,rotated=false){
 const def=ITEM_DEFS[id],kind=def?.kind;
 let shape=id==='rifle'||id==='fishing_rod'?[2,5]:id==='wood'?[1,3]:kind==='clothing'?[2,2]:id==='saddle'?[3,3]:kind==='weapon'?[2,2]:[1,1];
 return rotated?[shape[1],shape[0]]:shape;
}
export function maxStack(id){return ['clothing','weapon','tool','saddle'].includes(ITEM_DEFS[id]?.kind)?1:['ammo','material'].includes(ITEM_DEFS[id]?.kind)?50:20}
export function compartments(s){
 const out=[{id:'pockets',label:'Poches',width:6,height:4}];
 for(const [slot,id] of Object.entries(s.equipment||{}))if((ITEM_DEFS[id]?.capacity||0)>1)out.push({id:slot,label:ITEM_DEFS[id].label,width:6,height:Math.max(slot==='back'?6:2,Math.ceil(ITEM_DEFS[id].capacity*2/6))});
 return out;
}
export function fits(s,stack,container,x,y,ignore=null){
 if(container==='hands')return !(s.inventoryStacks||[]).some(t=>t.uid!==ignore&&t.container==='hands');
 const box=compartments(s).find(c=>c.id===container);if(!box)return false;
 const [w,h]=itemSize(stack.id,stack.rotated);
 if(!Number.isInteger(x)||!Number.isInteger(y)||x<0||y<0||x+w>box.width||y+h>box.height)return false;
 return !(s.inventoryStacks||[]).some(t=>{
  if(t.uid===ignore||t.container!==container)return false;
  const [tw,th]=itemSize(t.id,t.rotated);return x<t.x+tw&&x+w>t.x&&y<t.y+th&&y+h>t.y;
 });
}
function place(s,stack){
 for(const c of compartments(s))for(let y=0;y<c.height;y++)for(let x=0;x<c.width;x++)if(fits(s,stack,c.id,x,y,stack.uid)){Object.assign(stack,{container:c.id,x,y});return true}
 Object.assign(stack,{container:'overflow',x:0,y:0});return false;
}
function uid(s){s.inventorySequence=(Number(s.inventorySequence)||0)+1;return 'stack-'+s.inventorySequence}
export function syncInventory(s){
 s.inventoryStacks=Array.isArray(s.inventoryStacks)?s.inventoryStacks:[];s.quickbar=Array.isArray(s.quickbar)?s.quickbar.slice(0,10):['pistol','water','food','bandage','fishing_rod'];
 s.groundDrops=Array.isArray(s.groundDrops)?s.groundDrops:[];
 const desired={};for(const [id,n] of Object.entries(s.inventory||{}))if(Number.isFinite(n)&&n>0)desired[id]=Math.floor(n);
 const seen=new Set();
 s.inventoryStacks=s.inventoryStacks.filter(t=>t&&typeof t.id==='string'&&typeof t.uid==='string'&&!seen.has(t.uid)&&Number.isFinite(t.count)&&t.count>0&&(seen.add(t.uid),true));
 for(const stack of [...s.inventoryStacks]){
  const n=Math.min(Math.floor(stack.count),desired[stack.id]||0,maxStack(stack.id));stack.count=n;desired[stack.id]=(desired[stack.id]||0)-n;
 }
 s.inventoryStacks=s.inventoryStacks.filter(t=>t.count>0);
 for(const [id,number] of Object.entries(desired)){
  let left=number;
  for(const t of s.inventoryStacks.filter(t=>t.id===id)) {const n=Math.min(left,maxStack(id)-t.count);t.count+=n;left-=n;}
  while(left>0){const count=Math.min(left,maxStack(id)),stack={uid:uid(s),id,count,container:'overflow',x:0,y:0,rotated:false};s.inventoryStacks.push(stack);place(s,stack);left-=count}
 }
 for(const t of s.inventoryStacks)if(!fits(s,t,t.container,t.x,t.y,t.uid))place(s,t);
 s.hands=s.inventoryStacks.find(t=>t.container==='hands')?.id||null;
 return s.inventoryStacks;
}
export function moveStack(s,id,container,x=0,y=0,rotate=false){
 syncInventory(s);const t=s.inventoryStacks.find(t=>t.uid===id);if(!t)return {ok:false,message:'Objet absent.'};
 const rotated=t.rotated;t.rotated=rotate?!rotated:rotated;
 if(!fits(s,t,container,x,y,t.uid)){t.rotated=rotated;return {ok:false,message:'Cet emplacement est occupé ou trop petit.'}}
 Object.assign(t,{container,x,y});s.hands=s.inventoryStacks.find(t=>t.container==='hands')?.id||null;
 if(ITEM_DEFS[s.hands]?.kind==='weapon')s.weapon=s.hands;
 return {ok:true,message:'Objet déplacé.'};
}
export function takeInHands(s,id){
 syncInventory(s);const t=s.inventoryStacks.find(t=>t.uid===id);if(!t)return {ok:false,message:'Objet absent.'};
 if(t.container==='hands')return {ok:true,message:'Déjà dans les mains.'};
 const old=s.inventoryStacks.find(t=>t.container==='hands');
 if(old){old.container='overflow';place(s,old)}
 return moveStack(s,id,'hands');
}
export function splitStack(s,id,amount){
 syncInventory(s);const t=s.inventoryStacks.find(t=>t.uid===id),n=Math.floor(Number(amount));
 if(!t||!Number.isFinite(n)||n<1||n>=t.count)return {ok:false,message:'Choisis une quantité inférieure à la pile.'};
 const piece={...t,uid:uid(s),count:n,container:'overflow'};s.inventoryStacks.push(piece);
 if(!place(s,piece)){s.inventoryStacks.pop();return {ok:false,message:'Aucun emplacement pour séparer la pile.'}}
 t.count-=n;return {ok:true,message:'Pile séparée.'};
}
export function mergeStacks(s){
 syncInventory(s);for(const t of s.inventoryStacks){if(t.container==='hands')continue;for(const other of s.inventoryStacks){if(other===t||other.id!==t.id||other.container==='hands'||other.count<=0||t.count>=maxStack(t.id))continue;const n=Math.min(maxStack(t.id)-t.count,other.count);t.count+=n;other.count-=n}}
 s.inventoryStacks=s.inventoryStacks.filter(t=>t.count>0);return {ok:true,message:'Piles regroupées.'};
}
export function dropStack(s,id,amount){
 syncInventory(s);const t=s.inventoryStacks.find(t=>t.uid===id),n=Math.min(t?.count||0,Math.max(1,Math.floor(Number(amount)||1)));
 if(!t||!n)return {ok:false,message:'Objet absent.'};
 s.groundDrops.push({uid:uid(s),id:t.id,count:n,x:s.position.x,z:s.position.z,underground:s.underground||null});
 s.inventory[t.id]-=n;t.count-=n;syncInventory(s);return {ok:true,message:'Objet posé au sol.'};
}
export function nearbyDrops(s){return (s.groundDrops||[]).filter(t=>(t.underground||null)===(s.underground||null)&&Math.hypot(t.x-s.position.x,t.z-s.position.z)<=5)}
export function pickupDrop(s,id){
 syncInventory(s);const t=nearbyDrops(s).find(t=>t.uid===id);if(!t)return {ok:false,message:'Objet trop éloigné.'};
 const itemWeight=ITEM_DEFS[t.id]?.weight||.03;
 const count=Math.min(t.count,Math.max(0,Math.floor((capacity(s)-weight(s)+1e-7)/itemWeight)));
 if(!count)return {ok:false,message:'Poids maximal atteint.'};
 const before=structuredClone({inventory:s.inventory,inventoryStacks:s.inventoryStacks});
 const overflowBefore=s.inventoryStacks.filter(x=>x.id===t.id&&x.container==='overflow').reduce((n,x)=>n+x.count,0);
 s.inventory[t.id]=(s.inventory[t.id]||0)+count;syncInventory(s);
 if(s.inventoryStacks.filter(x=>x.id===t.id&&x.container==='overflow').reduce((n,x)=>n+x.count,0)>overflowBefore){Object.assign(s,before);return {ok:false,message:'Aucun emplacement libre.'}}
 t.count-=count;s.groundDrops=s.groundDrops.filter(t=>t.count>0);return {ok:true,message:count+' objet(s) récupéré(s).'};
}
export function sortInventory(s,by='name'){
 syncInventory(s);const movable=s.inventoryStacks.filter(t=>t.container!=='hands');
 movable.sort((a,b)=>by==='weight'?(ITEM_DEFS[b.id]?.weight||0)*b.count-(ITEM_DEFS[a.id]?.weight||0)*a.count:a.id.localeCompare(b.id));
 movable.forEach(t=>t.container='overflow');for(const t of movable)place(s,t);
 return {ok:true,message:'Inventaire trié.'};
}
