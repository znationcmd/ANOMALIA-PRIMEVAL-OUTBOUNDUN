/** Exact source-mesh sightlines: independent of Unreal physics and visual acceptance. */
import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const subtract=(a,b)=>a.map((v,i)=>v-b[i]);
const dot=(a,b)=>a.reduce((sum,v,i)=>sum+v*b[i],0);
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
function segmentTriangle(origin,direction,triangle){
 const e1=subtract(triangle[1],triangle[0]),e2=subtract(triangle[2],triangle[0]);
 const h=cross(direction,e2),det=dot(e1,h);if(Math.abs(det)<1e-9)return null;
 const inverse=1/det,s=subtract(origin,triangle[0]),u=inverse*dot(s,h);if(u<0||u>1)return null;
 const q=cross(s,e1),v=inverse*dot(direction,q);if(v<0||u+v>1)return null;
 const distance=inverse*dot(e2,q);return distance>1e-6&&distance<=1?distance:null;
}
export function isCargoFloorHit(hit, ceilingMetres=.92){
 if(!hit || hit.part!=='body' || hit.material!=='frame')return false;
 const height=hit.pointMetresYUp?.[1];
 const normal=hit.normalYUp;
 if(!Number.isFinite(height)||!Array.isArray(normal)||normal.length!==3||!normal.every(Number.isFinite))return false;
 const length=Math.hypot(...normal);
 return height>=.62&&height<=.70&&ceilingMetres-height>=.20&&
  length>1e-9&&normal[1]/length>=.8;
}
export async function auditCargoVisibility(folder,trunkPanel,{includeClearance=false}={}){
 const io=new NodeIO().registerExtensions(ALL_EXTENSIONS),triangles=[];
 for(const part of ['body','trunk']){
  const document=await io.read(path.join(folder,part+'.glb'));
  for(const primitive of document.getRoot().listMeshes()[0].listPrimitives()){
   const positions=primitive.getAttribute('POSITION');
   const indices=primitive.getIndices()?.getArray()??Uint32Array.from({length:positions.getCount()},(_,i)=>i);
   for(let i=0;i<indices.length;i+=3)triangles.push({part,material:primitive.getMaterial()?.getName(),
    vertices:[0,1,2].map(k=>positions.getElement(indices[i+k],[]))});
  }
 }
 if(triangles.some(t=>t.part==='trunk'&&t.material==='frame'))throw Error('Original cargo tub must not move with the boot lid');
 const pivot=[trunkPanel.pivotCm[0],trunkPanel.pivotCm[2],trunkPanel.pivotCm[1]].map(v=>v/100);
 if(trunkPanel.hingeAxis.join(',')!=='0,1,0')throw Error('Cargo sightline audit requires the authored horizontal hinge');
 const rows=[],clearanceRows=[];
 function firstHit(eye,end,angle){
  const direction=subtract(end,eye),rad=angle*Math.PI/180;
  let first=null;
  for(const triangle of triangles){
   const vertices=triangle.part==='body'?triangle.vertices:triangle.vertices.map(([x,y,z])=>
    [pivot[0]+Math.cos(rad)*x+Math.sin(rad)*y,pivot[1]-Math.sin(rad)*x+Math.cos(rad)*y,pivot[2]+z]);
   const fraction=segmentTriangle(eye,direction,vertices);
   if(fraction!==null&&(!first||fraction<first.fraction))first={fraction,part:triangle.part,material:triangle.material,
    pointMetresYUp:eye.map((v,i)=>v+direction[i]*fraction),
    normalYUp:cross(subtract(vertices[1],vertices[0]),subtract(vertices[2],vertices[0]))};
  }
  return first;
 }
 for(const angle of [0,trunkPanel.openAngleDegrees])for(const lateralMetres of [-.25,0,.25]){
  // Rear eye-height view to just below the original cargo floor, not through the rear seat.
  const eye=[-3.8,1.54,lateralMetres],end=[-2.04,.60,lateralMetres];
  const first=firstHit(eye,end,angle);
  if(angle===0?first?.part!=='trunk':!isCargoFloorHit(first))
   throw Error('Cargo sightline blocked or original cargo floor missing: '+JSON.stringify({angle,lateralMetres,first}));
  const {normalYUp,...legacyFirst}=first;
  rows.push({angleDegrees:angle,lateralMetres,first:includeClearance?first:legacyFirst});
 }
 // A rear wall at the expected floor height must not count as usable cargo space.
 // Probe down through six interior columns and require both clearance and a
 // predominantly horizontal floor. These are source-mesh checks, not screenshots.
 for(const forwardMetres of [-2.20,-2.05])for(const lateralMetres of [-.25,0,.25]){
  const eye=[forwardMetres,.92,lateralMetres],end=[forwardMetres,.40,lateralMetres];
  const first=firstHit(eye,end,trunkPanel.openAngleDegrees);
  if(!isCargoFloorHit(first))throw Error('Cargo volume has no clear horizontal floor: '+JSON.stringify({forwardMetres,lateralMetres,first}));
  clearanceRows.push({forwardMetres,lateralMetres,clearHeightMetres:.92-first.pointMetresYUp[1],first});
 }
 const result={state:'CPU_MESH_SIGHTLINES_PASSED_NOT_UNREAL_OR_VISUAL_ACCEPTANCE',rows};
 // Preserve the existing v7 manifest byte-for-byte. Expanded observations are
 // separate evidence and must not rewrite a previously accepted asset receipt.
 return includeClearance?{...result,clearanceRows,visualAcceptance:false,
  minimumClearHeightMetres:Math.min(...clearanceRows.map(r=>r.clearHeightMetres))}:result;
}
if(process.argv[1]&&fileURLToPath(import.meta.url)===path.resolve(process.argv[1])){
 const folder=process.argv[2];if(!folder)throw Error('Prepared E39 asset folder required');
 const manifest=JSON.parse(await readFile(path.join(folder,'manifest.json'),'utf8'));
 console.log(JSON.stringify(await auditCargoVisibility(folder,manifest.panels.find(p=>p.id==='trunk'),{includeClearance:true}),null,2));
}
