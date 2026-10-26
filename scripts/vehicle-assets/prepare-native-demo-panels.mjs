/** Original CC0 sedan: a genuine cut-out driver door, never a moving decal. */
import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {dequantize,flatten,getBounds,prune,transformMesh} from '@gltf-transform/functions';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {partitionTriangle,triangulate,area,boundaryEdges,driverDoorPlanes} from './panel-geometry.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const source=JSON.parse(await readFile(path.join(root,'docs/art/native-demo-sedan-source.json'),'utf8'));
const bytes=await readFile(path.join(root,'unreal/Saved/NativeDemoSedanSource/graphite_sedan.glb'));
const hash=b=>createHash('sha256').update(b).digest('hex');
if(bytes.length!==source.bytes||hash(bytes)!==source.sha256)throw Error('Pinned CC0 source required');
const base=path.join(root,'unreal/SourceAssets/NativeDemoSedan_v1');
const previous=JSON.parse(await readFile(path.join(base,'manifest.json'),'utf8'));
const out=path.join(root,'unreal/SourceAssets/NativeDemoSedan_v2');await mkdir(out,{recursive:true});
async function preserve(name,data){
 try{if(!Buffer.from(data).equals(await readFile(path.join(out,name))))throw Error('Existing prepared panel art preserved: '+name);}
 catch(e){if(e.code!=='ENOENT')throw e;await writeFile(path.join(out,name),data);}
}
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS);
const pivot=[-1.29,.94,.885],models=[];let partitionReport;
for(const selection of ['body','door_driver']){
 const doc=await io.readBinary(bytes);await doc.transform(dequantize(),flatten({cleanup:false}));
 const scene=doc.getRoot().getDefaultScene(),nodes=[];scene.traverse(n=>{if(n.getMesh())nodes.push(n);});
 if(nodes.length!==304||doc.getRoot().listSkins().length)throw Error('Reviewed source topology changed');
 const mesh=doc.createMesh(selection),buffer=doc.getRoot().listBuffers()[0];
 const interior=doc.getRoot().listMaterials().find(m=>m.getName()==='interior');
 let cutArea=0,remainingArea=0,originalArea=0,doorTriangles=[],cutTriangles=0;
 function addTriangles(tris,material){
  if(!tris.length)return;
  const prim=doc.createPrimitive().setMaterial(material),semantics=Object.keys(tris[0][0]);
  for(const semantic of semantics){
   const size=tris[0][0][semantic].length,data=[];
   for(const tri of tris)for(const vertex of tri){
    let v=[...vertex[semantic]];
    if(semantic==='NORMAL'){const length=Math.hypot(...v);if(length>0)v=v.map(x=>x/length);}
    data.push(...v);
   }
   prim.setAttribute(semantic,doc.createAccessor().setType(size===1?'SCALAR':'VEC'+size).setBuffer(buffer).setArray(new Float32Array(data)));
  }
  mesh.addPrimitive(prim);
 }
 const addOriginal=n=>{
  const copy=n.getMesh().clone();transformMesh(copy,n.getWorldMatrix());
  for(const p of copy.listPrimitives())mesh.addPrimitive(p);
 };
 for(const n of nodes){
  const name=n.getName();if(name.startsWith('107 reused ')||name.startsWith('Siped tread blocks'))continue;
  const b=getBounds(n),positiveSide=b.min[2]>.65;
  const attached=positiveSide&&(/^(Front side door glass|Aerodynamic mirror|Mirror reflective insert|Short mirror plinth)/.test(name)||
   /^(Door panel shut line|Satin door pull handle|Recessed handle pocket)$/.test(name));
  if(name==='Watertight 14-station body shell'||(positiveSide&&/^(Beltline satin bead|Painted door glazing lower sill)/.test(name))){
   const baked=n.getMesh().clone();transformMesh(baked,n.getWorldMatrix());
   for(const p of baked.listPrimitives()){
    if(p.getMode()!==4||p.listTargets().length)throw Error('Expected unskinned triangle primitives');
    const position=p.getAttribute('POSITION'),indices=p.getIndices(),inside=[],outside=[];
    const count=indices?indices.getCount():position.getCount();
    const vertex=i=>Object.fromEntries(p.listSemantics().map(k=>[k,p.getAttribute(k).getElement(i,[])]));
    for(let i=0;i<count;i+=3){
     const tri=[0,1,2].map(j=>vertex(indices?indices.getScalar(i+j):i+j));
     const parts=partitionTriangle(tri,driverDoorPlanes),a=triangulate(parts.inside),r=triangulate(parts.outside);
     originalArea+=area(tri);for(const t of a)cutArea+=area(t);for(const t of r)remainingArea+=area(t);
     inside.push(...a);outside.push(...r);
    }
    addTriangles(selection==='body'?outside:inside,p.getMaterial());
    // Only the continuous shell defines the opening's sheet-metal edge.
    if(name==='Watertight 14-station body shell')doorTriangles.push(...inside);
    cutTriangles+=inside.length;
   }
  }else if(selection==='door_driver'?attached:!attached)addOriginal(n);
 }
 if(cutArea<.5||Math.abs(originalArea-cutArea-remainingArea)>1e-6)throw Error('Door cut did not preserve original surface area');
 const edges=boundaryEdges(doorTriangles);
 if(edges.length<8)throw Error('Real door aperture boundary required');
 const offset=v=>({...v,POSITION:[v.POSITION[0],v.POSITION[1],v.POSITION[2]-(selection==='body'?.065:.045)]});
 const faces=[];
 for(const [a,b] of edges){
  const ai=offset(a),bi=offset(b);
  faces.push([b,a,ai],[b,ai,bi]);
 }
 if(selection==='door_driver')for(const t of doorTriangles)faces.push(t.map(offset).reverse().map(v=>({...v,NORMAL:v.NORMAL.map(x=>-x)})));
 // Detailed outer skin, original trim/glass/mirror, extruded edges and inner skin.
 addTriangles(faces,interior);
 if(selection==='door_driver')transformMesh(mesh,[1,0,0,0,0,1,0,0,0,0,1,0,...pivot.map(x=>-x),1]);
 transformMesh(mesh,[-1,0,0,0,0,1,0,0,0,0,-1,0,0,0,0,1]);
 for(const child of scene.listChildren())scene.removeChild(child);
 scene.addChild(doc.createNode(selection).setMesh(mesh));await doc.transform(prune());
 const result=await io.writeBinary(doc),bounds=getBounds(scene);
 await preserve(selection+'.glb',result);
 models.push({id:selection,file:selection+'.glb',sha256:hash(result),bytes:result.length,
  sourceNodes:304,dimensionsMetresYUp:bounds.max.map((x,i)=>x-bounds.min[i]),
  objectPath:'/Game/Anomalia/NativeDemoSedan_v2/'+selection+'/SM_'+selection});
 partitionReport={originalSurfaceArea:originalArea,doorSurfaceArea:cutArea,remainingSurfaceArea:remainingArea,cutTriangles,boundaryEdges:edges.length};
}
for(const model of previous.models.filter(m=>m.id.startsWith('wheel_'))){
 const data=await readFile(path.join(base,model.file));if(hash(data)!==model.sha256)throw Error('Original wheels changed');
 await preserve(model.file,data);models.push({...model,objectPath:model.objectPath.replace('_v1/','_v2/')});
}
const manifest={schemaVersion:2,source,models,wheelHubsCm:previous.wheelHubsCm,
 sourceCoverage:{nodes:304,partition:partitionReport},rigged:false,interactiveDoors:false,gameplayVerified:false,
 panels:[{id:'door_driver',pivotCm:[129,88.5,94],openAngleDegrees:-70,speedDegreesPerSecond:80,
  side:'positive_Y_matches_original_steering_wheel',outerThicknessCm:4.5}]};
await preserve('manifest.json',JSON.stringify(manifest,null,2)+'\n');
await preserve('CREDITS.md','# Original ANOMALIA sedan with cut driver door\n\n'+source.author+'\n'+source.source+'\nCC0-1.0 — '+source.licenseUrl+'\n\nChanges: original continuous body surface partitioned without removing its area, driver door skin separated with original glass/mirror/trim, extruded inner skin and opening edges, hinge-centred local coordinates. Original source and v1 assets retained. Only the driver door is separated; other doors, hood and trunk remain unfinished.\n');
console.log(JSON.stringify({state:'REAL_DRIVER_DOOR_MESH_PREPARED_NOT_UNREAL_VERIFIED',partition:partitionReport,models:models.map(m=>({id:m.id,bytes:m.bytes}))},null,2));
