import * as THREE from 'three';
import {edgePosition} from './construction.js';
export function createConstructionWorld({scene,state,heightAt,materials}){
 const root=new THREE.Group();scene.add(root);let signature='',solids=[],surfaces=[];
 const owned=new Set();const stone=materials.rock.clone();stone.color.set(0xaaa398);owned.add(stone);const metal=new THREE.MeshStandardMaterial({color:0x7c8585,map:materials.wall.map,roughness:.5,metalness:.5});owned.add(metal);
 function rebuild(){const next=JSON.stringify(state.construction);if(next===signature)return;signature=next;root.traverse(o=>o.geometry?.dispose());root.clear();solids=[];surfaces=[];
  for(const p of state.construction||[]){const mat=p.material==='stone'?stone:p.material==='metal'?metal:materials.wood,g=new THREE.Group();g.position.set(p.x,p.y,p.z);root.add(g);
   const box=(x,y,z,w,h,d,solid=false)=>{const m=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),mat);m.position.set(x,y,z);m.castShadow=true;m.receiveShadow=true;m.userData.cameraSolid=true;m.userData.constructionId=p.id;g.add(m);if(solid)solids.push({x:p.x+x,z:p.z+z,width:w,depth:d,minY:p.y+y-h/2,maxY:p.y+y+h/2});return m;};
   if(['foundation','piles','floating','underwater','ceiling'].includes(p.type)){
    box(0,-.14,0,4,.28,4);surfaces.push({...p,width:4,depth:4});
    if(p.type==='floating'){for(const x of [-1.6,1.6])box(x,-.65,0,.6,.9,3.7);}
    if(['piles','foundation','underwater'].includes(p.type))for(const x of [-1.65,1.65])for(const z of [-1.65,1.65]){const bottom=heightAt(p.x+x,p.z+z),h=Math.max(.4,p.y-bottom);box(x,-h/2,z,.25,h,.25);}
    if(p.material==='wood')for(let z=-1.8;z<2;z+=.4)box(0,.005,z,4,.02,.015);
   }else if(['wall','doorway','window','door'].includes(p.type)){
    const e=edgePosition(p),wall=new THREE.Group();wall.position.set(e.x-p.x,0,e.z-p.z);wall.rotation.y=e.yaw;g.add(wall);
    const panel=(x,y,w,h)=>{const m=new THREE.Mesh(new THREE.BoxGeometry(w,h,.18),mat);m.position.set(x,y,0);m.castShadow=true;m.receiveShadow=true;m.userData.cameraSolid=true;m.userData.constructionId=p.id;wall.add(m);const a=e.yaw;solids.push({x:e.x+x*Math.cos(a),z:e.z-x*Math.sin(a),width:w,depth:.18,yaw:a,minY:p.y+y-h/2,maxY:p.y+y+h/2});};
    if(p.type==='wall')panel(0,1.5,4,3);
    if(p.type==='doorway'){panel(-1.4,1.5,1.2,3);panel(1.4,1.5,1.2,3);panel(0,2.7,1.6,.6);}
    if(p.type==='window'){panel(0,.5,4,1);panel(0,2.75,4,.5);panel(-1.5,1.75,1,1.5);panel(1.5,1.75,1,1.5);}
    if(p.type==='door'){if(!p.open)panel(0,1.2,1.5,2.4);else{const leaf=new THREE.Mesh(new THREE.BoxGeometry(.18,2.4,1.5),mat);leaf.position.set(-.75,1.2,.75);leaf.userData.constructionId=p.id;leaf.userData.cameraSolid=true;wall.add(leaf);}}
   }else if(p.type==='roof'){
    for(const sign of [-1,1]){const m=box(sign*1.04,3.55,0,2.35,.18,4.35);m.rotation.z=-sign*.47;}box(0,4.1,0,.16,.16,4.4);
   }else if(p.type==='ramp'){
    g.rotation.y=p.yaw*Math.PI/2;const a=p.yaw*Math.PI/2,drop=Math.min(3,Math.max(.3,p.y-Math.max(0,heightAt(p.x+Math.sin(a)*6,p.z+Math.cos(a)*6))));for(let i=0;i<12;i++)box(0,-drop*(i+.5)/12-.1,2+(i+.5)/3,1.8,.2,.36);surfaces.push({...p,width:1.8,depth:4,access:true,drop});
   }else if(p.type==='stairs'){
    g.rotation.y=p.yaw*Math.PI/2;for(let i=0;i<12;i++)box(0,(i+1)*.25-.125,-1.85+i/3,1.7,.25,.36);surfaces.push({...p,width:1.7,depth:4,ramp:true});
   }
  }
 }
 function floorAt(x,z,feet=0){let floor=null;for(const p of surfaces){const a=p.yaw*Math.PI/2,dx=x-p.x,dz=z-p.z,lx=dx*Math.cos(a)-dz*Math.sin(a),lz0=dx*Math.sin(a)+dz*Math.cos(a),lz=p.access?lz0-4:lz0;if(Math.abs(lx)>p.width/2||Math.abs(lz)>p.depth/2)continue;const y=p.access?p.y-(lz+2)/4*p.drop:p.ramp?p.y+(lz+2)/4*3:p.y;if(y>feet+.8)continue;if(floor===null||y>floor)floor=y;}return floor;}
 rebuild();return {update:rebuild,floorAt,solids:feet=>solids.filter(s=>s.maxY>feet+.2&&s.minY<feet+1.65),root};
}
