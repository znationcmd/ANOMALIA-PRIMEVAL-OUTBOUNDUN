import {WORLD_HALF} from './mechanics.js';
export const GRID=4,STOREY=3;
export const BUILD_PARTS={foundation:{label:'Fondation terrestre',factor:2},piles:{label:'Fondation sur pilotis',factor:3},floating:{label:'Plateforme flottante ancrée',factor:4},underwater:{label:'Fondation sous-marine',factor:3},wall:{label:'Mur',factor:1},window:{label:'Mur avec fenêtre',factor:1},doorway:{label:'Cadre de porte',factor:1},door:{label:'Porte ouvrante',factor:1},ceiling:{label:'Plancher / plafond',factor:2},roof:{label:'Toit à deux pans',factor:2},stairs:{label:'Escalier',factor:2},ramp:{label:'Rampe d’accès',factor:2}};
export const BUILD_MATERIALS={wood:{label:'Bois',item:'wood',amount:4},stone:{label:'Pierre',item:'stone',amount:5},metal:{label:'Métal',item:'scrap',amount:4}};
const foundations=new Set(['foundation','piles','floating','underwater']);
const wallTypes=new Set(['wall','window','doorway','door']);
export function price(part,material){const p=BUILD_PARTS[part],m=BUILD_MATERIALS[material];return p&&m?{[m.item]:m.amount*p.factor}:null;}
export function placement(s,{type,material='wood',x,z,level=0,yaw=0},heightAt){
 if(!Object.hasOwn(BUILD_PARTS,type)||!Object.hasOwn(BUILD_MATERIALS,material)||![x,z,level,yaw].every(Number.isFinite)||!Number.isInteger(level)||level<0||level>4)return {ok:false,message:'Élément invalide.'};
 x=Math.round(x/GRID)*GRID;z=Math.round(z/GRID)*GRID;yaw=((Math.round(yaw)%4)+4)%4;
 if(Math.abs(x)>WORLD_HALF-4||Math.abs(z)>WORLD_HALF-4)return {ok:false,message:'Limite de carte.'};
 const all=s.construction||[];if(all.length>=1500)return {ok:false,message:'1500 éléments maximum.'};
 const foundation=all.find(p=>foundations.has(p.type)&&p.x===x&&p.z===z);
 const ground=heightAt(x,z);let y,parent=null;
 if(foundations.has(type)){
  if(level!==0||foundation)return {ok:false,message:'Fondation déjà présente ou étage invalide.'};
  const corners=[[-2,-2],[-2,2],[2,-2],[2,2]].map(([dx,dz])=>heightAt(x+dx,z+dz));
  if(type==='foundation'&&(Math.min(ground,...corners)<.5||Math.max(...corners)-Math.min(...corners)>3))return {ok:false,message:'Choisis un terrain sec et moins pentu, ou des pilotis.'};
  if(['floating','underwater'].includes(type)&&Math.max(ground,...corners)>=-.5)return {ok:false,message:'Cette fondation nécessite de l’eau.'};
  y=type==='floating'?1.3:type==='piles'?Math.max(2,ground+.4):type==='underwater'?Math.max(ground,...corners)+.3:Math.max(ground,...corners)+.3;
  const neighbor=all.find(p=>foundations.has(p.type)&&Math.hypot(p.x-x,p.z-z)===GRID&&Math.abs(p.y-y)<1);if(neighbor)y=neighbor.y;
 }else{
  if(!foundation)return {ok:false,message:'Pose d’abord une fondation dans cette case.'};
  y=foundation.y+level*STOREY;
  const floor=level===0?foundation:all.find(p=>p.x===x&&p.z===z&&p.type==='ceiling'&&p.level===level);
  if(type==='ceiling'){
   if(level===0)return {ok:false,message:'Un plancher supérieur commence à l’étage 1.'};
   const below=level===1?foundation:all.find(p=>p.x===x&&p.z===z&&p.type==='ceiling'&&p.level===level-1);
   const wall=all.find(p=>p.x===x&&p.z===z&&['wall','window','doorway'].includes(p.type)&&p.level===level-1);if(!below||!wall)return {ok:false,message:'Le plancher nécessite un étage inférieur et un mur porteur.'};parent=wall.id;
  }else{if(!floor)return {ok:false,message:'Cet étage nécessite un plancher.'};parent=floor.id;}
  if(type==='roof'){const wall=all.find(p=>p.x===x&&p.z===z&&['wall','window','doorway'].includes(p.type)&&p.level===level);if(!wall)return {ok:false,message:'Le toit nécessite un mur porteur.'};parent=wall.id;}
  if(type==='door'){const frame=all.find(p=>p.type==='doorway'&&p.x===x&&p.z===z&&p.level===level&&p.yaw===yaw);if(!frame)return {ok:false,message:'Pose d’abord un cadre de porte sur ce côté.'};parent=frame.id;}
 }
 const position={x,z,y,level,yaw,type,material,parent};
 const duplicate=all.some(p=>p.x===x&&p.z===z&&p.level===level&&(wallTypes.has(type)?wallTypes.has(p.type)&&p.yaw===yaw&&(type==='door'?p.type==='door':p.type!=='door'):p.type===type));if(duplicate)return {ok:false,message:'Un élément occupe déjà cet emplacement.'};
 const cost=price(type,material);for(const [item,n]of Object.entries(cost))if((s.inventory[item]||0)<n)return {ok:false,message:`Matériaux insuffisants : ${n} ${BUILD_MATERIALS[material].label.toLowerCase()}.`,position,cost};
 return {ok:true,position,cost,message:'Emplacement valide.'};
}
export function placeConstruction(s,request,heightAt){const result=placement(s,request,heightAt);if(!result.ok)return result;for(const [item,n]of Object.entries(result.cost))s.inventory[item]-=n;s.constructionSequence=(s.constructionSequence||0)+1;const piece={...result.position,id:'build-'+s.constructionSequence,open:false,hp:100};s.construction??=[];s.construction.push(piece);return {ok:true,piece,message:BUILD_PARTS[piece.type].label+' construit.'};}
export function demolishConstruction(s,id){const p=s.construction?.find(p=>p.id===id);if(!p)return {ok:false,message:'Élément introuvable.'};if(s.construction.some(n=>n.parent===id||foundations.has(p.type)&&n.x===p.x&&n.z===p.z&&n.id!==id))return {ok:false,message:'Retire les éléments supportés avant de démolir celui-ci.'};s.construction=s.construction.filter(n=>n.id!==id);for(const [item,n]of Object.entries(price(p.type,p.material)))s.inventory[item]=(s.inventory[item]||0)+Math.floor(n/2);return {ok:true,message:'Élément démoli, moitié des matériaux récupérée.'};}
export function validateConstruction(items){if(!Array.isArray(items))return [];const ids=new Set(),out=[];for(const p of items){if(out.length>=1500)break;if(!p||typeof p.id!=='string'||ids.has(p.id)||!Object.hasOwn(BUILD_PARTS,p.type)||!Object.hasOwn(BUILD_MATERIALS,p.material)||![p.x,p.z,p.y,p.level,p.yaw].every(Number.isFinite)||Math.abs(p.x)>=WORLD_HALF||Math.abs(p.z)>=WORLD_HALF||p.level<0||p.level>4||p.y<=-100||p.y>=3000)continue;ids.add(p.id);out.push({...p,open:!!p.open});}return out;}
export function edgePosition(p,offset=2){const a=p.yaw*Math.PI/2;return {x:p.x+Math.sin(a)*offset,z:p.z+Math.cos(a)*offset,yaw:a};}
