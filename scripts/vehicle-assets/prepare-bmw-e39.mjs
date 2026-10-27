/** Preserve the licensed E39, bake its hierarchy and separate its four authored wheels. */
import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {dequantize,getBounds,prune,transformMesh} from '@gltf-transform/functions';
import {MeshoptDecoder} from 'meshoptimizer';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const registry=JSON.parse(await readFile(path.join(root,'docs/vehicles/named-assets-sources.json'),'utf8'));
const items=Array.isArray(registry)?registry:Object.values(registry).find(v=>Array.isArray(v)&&v.some(x=>x.id==='bmw_e39'));
const source=items.find(x=>x.id==='bmw_e39');
const bytes=await readFile(path.join(root,'unreal/Saved/BMWE39Source/bmw-e39.glb'));
const hash=b=>createHash('sha256').update(b).digest('hex');
if(source.license!=='CC-BY-4.0'||bytes.length!==source.sourceBytes||hash(bytes)!==source.sourceSHA256)throw Error('Pinned licensed E39 required');
await MeshoptDecoder.ready;
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.decoder':MeshoptDecoder});
const out=path.join(root,'unreal/SourceAssets/BMWE39Review_v1');await mkdir(out,{recursive:true});
async function preserve(name,data){try{if(!Buffer.from(data).equals(await readFile(path.join(out,name))))throw Error('Prepared artist asset preserved: '+name);}catch(e){if(e.code!=='ENOENT')throw e;await writeFile(path.join(out,name),data);}}
const models=[];let wheelHubsCm,sourceTriangles,exportedTriangles=0;
for(const selection of ['body','wheel_fl','wheel_fr','wheel_rl','wheel_rr']){
 const d=await io.readBinary(bytes);await d.transform(dequantize());
 if(d.getRoot().listSkins().length||d.getRoot().listAnimations().length)throw Error('Unexpected source rig');
 const scene=d.getRoot().listScenes()[0],nodes=[];scene.traverse(n=>{if(n.getMesh())nodes.push(n);});
 // The source reuses wheel geometry across nodes. Clone primitives and arrays
 // before baking each instance, or the four wheel transforms accumulate.
 const bounds=getBounds(scene),lift=-bounds.min[1];
 const center=n=>{const b=getBounds(n);return b.min.map((v,i)=>(v+b.max[i])/2);};
 const tires=nodes.filter(n=>/^Object_39\..*_tire_protector_0$/.test(n.getName()));
 if(tires.length!==4)throw Error('Four authored tires required');
 // Source: -Z forward, +Y up, -X driver side. Native: +X forward, +Y right.
 const hubs=tires.map(n=>{const p=center(n);return {p,ue:[-p[2]*100,p[0]*100,(p[1]+lift)*100]};});
 hubs.sort((a,b)=>b.ue[0]-a.ue[0]);hubs.splice(0,2,...hubs.slice(0,2).sort((a,b)=>a.ue[1]-b.ue[1]));hubs.splice(2,2,...hubs.slice(2).sort((a,b)=>a.ue[1]-b.ue[1]));wheelHubsCm=hubs.map(x=>x.ue);
 const mesh=d.createMesh(selection),index=['wheel_fl','wheel_fr','wheel_rl','wheel_rr'].indexOf(selection);let triangles=0,total=0;
 for(const n of nodes){
  const wheel=/^Object_39\..*_(tire_protector|tire_left_L)_0$/.test(n.getName())||/^Object_4\..*_Scene_-_Root_0$/.test(n.getName())||/^Object_24\..*_texture_2_brakedisc_0$/.test(n.getName());
  for(const p of n.getMesh().listPrimitives())total+=(p.getIndices()?.getCount()??p.getAttribute('POSITION').getCount())/3;
  if(index<0?wheel:!wheel)continue;
  if(index>=0){const c=center(n),dist=hubs.map(h=>Math.hypot(...c.map((v,i)=>v-h.p[i])));if(dist.indexOf(Math.min(...dist))!==index)continue;}
  const original=d.createMesh();
  for(const p of n.getMesh().listPrimitives()){
   const copy=p.clone();
   for(const semantic of p.listSemantics()){
    const a=p.getAttribute(semantic);copy.setAttribute(semantic,a.clone().setArray(a.getArray().slice()));
   }
   if(p.getIndices()){const a=p.getIndices();copy.setIndices(a.clone().setArray(a.getArray().slice()));}
   original.addPrimitive(copy);
  }
  transformMesh(original,n.getWorldMatrix());
  const translation=index<0?[0,lift,0]:hubs[index].p.map(v=>-v);
  transformMesh(original,[1,0,0,0,0,1,0,0,0,0,1,0,...translation,1]);
  transformMesh(original,[0,0,1,0,0,1,0,0,-1,0,0,0,0,0,0,1]);
  for(const p of original.listPrimitives()){mesh.addPrimitive(p);triangles+=(p.getIndices()?.getCount()??p.getAttribute('POSITION').getCount())/3;}
 }
 if(triangles<100)throw Error('Missing E39 geometry');sourceTriangles=total;exportedTriangles+=triangles;
 for(const child of scene.listChildren())scene.removeChild(child);
 scene.addChild(d.createNode(selection).setMesh(mesh));d.getRoot().setDefaultScene(scene);await d.transform(prune());
 for(const ext of d.getRoot().listExtensionsUsed())if(['EXT_meshopt_compression','KHR_mesh_quantization'].includes(ext.extensionName))ext.dispose();
 const result=await io.writeBinary(d),b=getBounds(scene);await preserve(selection+'.glb',result);
 models.push({id:selection,file:selection+'.glb',bytes:result.length,sha256:hash(result),triangles,
 dimensionsMetresYUp:b.max.map((v,i)=>v-b.min[i]),originMetresYUp:b.max.map((v,i)=>(v+b.min[i])/2),objectPath:'/Game/Anomalia/BMWE39Review_v1/'+selection+'/SM_'+selection});
}
if(sourceTriangles!==exportedTriangles)throw Error('Source triangle coverage changed');
const manifest={schemaVersion:1,source:{license:source.license,sha256:source.sourceSHA256,author:source.artist,source:source.sourceUrl,download:source.downloadUrl},models,wheelHubsCm,sourceTriangles,exportedTriangles,interactiveDoors:false,entryAnimation:false,gameplayVerified:false};
await preserve('manifest.json',JSON.stringify(manifest,null,2)+'\n');
await preserve('CREDITS.md',`# BMW E39 Free\n\nBy ${source.artist} — ${source.artistUrl}\n${source.sourceUrl}\nCC BY 4.0 — ${source.licenseUrl}\n\nRedistributed source: ${source.downloadUrl}\nChanges: decompression, baked node transforms, forward-axis and ground-origin correction; original four wheel assemblies separated. Brake calipers remain on chassis. Existing source preserved. Interior and exterior retained. No claim of animated doors, native rigging, game acceptance or final art quality.\n`);
console.log(JSON.stringify({state:'E39_STATIC_PARTS_PREPARED_NOT_GAME_VERIFIED',sourceTriangles,exportedTriangles,wheelHubsCm,models:models.map(m=>({id:m.id,triangles:m.triangles}))}));
