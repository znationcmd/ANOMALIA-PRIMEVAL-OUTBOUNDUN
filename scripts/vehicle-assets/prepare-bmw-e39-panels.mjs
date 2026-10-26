/** Keep the same E39: derive an actual hinged driver leaf from its authored surfaces. */
import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {getBounds,prune,transformMesh} from '@gltf-transform/functions';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';import {fileURLToPath} from 'node:url';import path from 'node:path';
import {triangleIslands} from './mesh-islands.mjs';
import {partitionTriangle,triangulate,area,gltfToUnreal} from './panel-geometry.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const base=path.join(root,'unreal/SourceAssets/BMWE39Review_v1'),out=path.join(root,'unreal/SourceAssets/BMWE39Review_v2');
const previous=JSON.parse(await readFile(path.join(base,'manifest.json'),'utf8'));
if(previous.source.sha256!=='984a9daab49b5a31c45bbc284c657fa5898a010f2201c003358cb6b6f411751d'||previous.source.license!=='CC-BY-4.0')throw Error('Same reviewed E39 source required');
const hash=b=>createHash('sha256').update(b).digest('hex');
const original=previous.models.find(m=>m.id==='body'),bytes=await readFile(path.join(base,original.file));
if(hash(bytes)!==original.sha256||bytes.length!==original.bytes)throw Error('E39 parent body changed');
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS);await mkdir(out,{recursive:true});
async function preserve(name,data){try{if(!Buffer.from(data).equals(await readFile(path.join(out,name))))throw Error('Existing prepared E39 preserved: '+name);}catch(e){if(e.code!=='ENOENT')throw e;await writeFile(path.join(out,name),data);}}
// Prepared glTF coordinates: X forward, Y up, negative Z is driver side.
const pivot=[.924,.90,-.80],models=[];
const doorPlanes=[p=>p[0]+.285,p=>.95-p[0],p=>p[1]-.50,p=>1.39-p[1],p=>-.55-p[2],p=>2.10-p[0]-1.35*p[1]];
let partition,closedBodyBoundsCm;
for(const selection of ['body','door_driver']){
 const doc=await io.readBinary(bytes),scene=doc.getRoot().getDefaultScene();
 const old=scene.listChildren()[0].getMesh();
 if(scene.listChildren().length!==1||!old||doc.getRoot().listSkins().length)throw Error('Reviewed baked E39 body required');
 const bounds=getBounds(scene);closedBodyBoundsCm={min:gltfToUnreal(bounds.min),max:gltfToUnreal(bounds.max)};
 const mesh=doc.createMesh(selection),buffer=doc.getRoot().listBuffers()[0];
 let originalArea=0,doorArea=0,remainingArea=0,doorTriangles=0,remainingTriangles=0,wholeIslands=0,clippedIslands=0;
 const materialContributions={};
 function append(tris,material){
  if(!tris.length)return;
  const primitive=doc.createPrimitive().setMaterial(material);
  for(const semantic of Object.keys(tris[0][0])){
   const size=tris[0][0][semantic].length,data=[];
   for(const t of tris)for(const v of t){
    let a=[...v[semantic]];
    if(semantic==='NORMAL'||semantic==='TANGENT'){const length=Math.hypot(...a.slice(0,3));if(length<1e-10)throw Error('Invalid interpolated normal');for(let i=0;i<3;i++)a[i]/=length;}
    data.push(...a);
   }
   primitive.setAttribute(semantic,doc.createAccessor().setType(size===1?'SCALAR':'VEC'+size).setBuffer(buffer).setArray(new Float32Array(data)));
  }
  mesh.addPrimitive(primitive);
 }
 for(const p of old.listPrimitives()){
  if(p.getMode()!==4||p.listTargets().length)throw Error('Static triangle source required');
  const pos=p.getAttribute('POSITION'),indices=p.getIndices()?.getArray()??Uint32Array.from({length:pos.getCount()},(_,i)=>i);
  const groups=triangleIslands(pos.getArray(),indices),inside=[],outside=[];
  const name=p.getMaterial()?.getName()??'',vertex=i=>Object.fromEntries(p.listSemantics().map(k=>[k,p.getAttribute(k).getElement(i,[])]));
  for(const g of groups){
   // Original lower leaf, mirror, trim, inner lining and side glass are already
   // disconnected islands. Preserve them whole, rather than cutting the seats.
   const whole=g.min[0]>=-.285&&g.max[0]<=.95&&g.min[1]>=.50&&g.max[1]<=1.39&&g.max[2]<-.55&&
    (g.max[2]<-.66||name==='window');
   // Only the continuous exterior/window frame and side trim require a cut.
   // Cabin islands spanning toward the centre and the roof stay with the body.
   const sideTrim=g.max[2]<-.55&&g.min[1]>.70;
   const continuousFrame=name==='body'&&g.triangleOffsets.length>5000;
   if(whole)wholeIslands++;else if(sideTrim||continuousFrame)clippedIslands++;
   for(const offset of g.triangleOffsets){
    const tri=[0,1,2].map(k=>vertex(indices[offset+k]));originalArea+=area(tri);
    let a=[],b=[];
    if(whole)a=[tri];else if(sideTrim||continuousFrame){const r=partitionTriangle(tri,continuousFrame?[...doorPlanes,p=>p[1]-.99]:doorPlanes);a=triangulate(r.inside);b=triangulate(r.outside);}else b=[tri];
    for(const t of a)doorArea+=area(t);for(const t of b)remainingArea+=area(t);
    doorTriangles+=a.length;remainingTriangles+=b.length;inside.push(...a);outside.push(...b);
   }
  }
  materialContributions[name]=(materialContributions[name]??0)+inside.length;
  append(selection==='body'?outside:inside,p.getMaterial());
 }
 if(doorArea<1||doorArea>6||Math.abs(originalArea-doorArea-remainingArea)>1e-6||wholeIslands<10||materialContributions.window<20)throw Error('Incomplete E39 leaf or original surface coverage');
 if(selection==='door_driver')transformMesh(mesh,[1,0,0,0,0,1,0,0,0,0,1,0,...pivot.map(v=>-v),1]);
 for(const n of scene.listChildren())scene.removeChild(n);scene.addChild(doc.createNode(selection).setMesh(mesh));await doc.transform(prune());
 const data=await io.writeBinary(doc),b=getBounds(scene);await preserve(selection+'.glb',data);
 models.push({id:selection,file:selection+'.glb',bytes:data.length,sha256:hash(data),triangles:selection==='body'?remainingTriangles:doorTriangles,
 dimensionsMetresYUp:b.max.map((v,i)=>v-b.min[i]),originMetresYUp:b.max.map((v,i)=>(v+b.min[i])/2),objectPath:'/Game/Anomalia/BMWE39Review_v2/'+selection+'/SM_'+selection});
 partition={originalSurfaceArea:originalArea,doorSurfaceArea:doorArea,remainingSurfaceArea:remainingArea,doorTriangles,remainingTriangles,wholeIslands,clippedIslands,materialContributions};
}
for(const m of previous.models.filter(m=>m.id.startsWith('wheel_'))){const data=await readFile(path.join(base,m.file));if(hash(data)!==m.sha256)throw Error('Validated E39 wheels changed');await preserve(m.file,data);models.push({...m,objectPath:'/Game/Anomalia/BMWE39Review_v2/'+m.id+'/SM_'+m.id});}
const manifest={schemaVersion:2,source:previous.source,parentBodySha256:original.sha256,models,wheelHubsCm:previous.wheelHubsCm,closedBodyBoundsCm,
 sourceCoverage:{partition},interactiveDoors:false,gameplayVerified:false,
 panels:[{id:'door_driver',pivotCm:gltfToUnreal(pivot),openAngleDegrees:70,side:'negative_Y_same_E39_driver',apertureCm:[20,-80,110],fixtureStandCm:[210,-230,100]}]};
await preserve('manifest.json',JSON.stringify(manifest,null,2)+'\n');
await preserve('CREDITS.md',(await readFile(path.join(base,'CREDITS.md'),'utf8'))+'\nAdditional changes: same E39 original driver leaf, mirror, glass and inner lining separated; shared window-frame surfaces partitioned with area conservation; hinge-local coordinates. Original E39 v1 and its validated wheels retained unchanged. Only the driver door is prepared; native opening and driving must be verified separately.\n');
console.log(JSON.stringify({state:'SAME_E39_DRIVER_DOOR_PREPARED_NOT_GAME_VERIFIED',partition,models:models.map(m=>({id:m.id,triangles:m.triangles}))}));
