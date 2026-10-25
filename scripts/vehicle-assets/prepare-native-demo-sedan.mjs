/** Preserve a licensed original sedan while deriving body and four centred wheel assets. */
import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {dequantize,flatten,getBounds,prune,transformMesh} from '@gltf-transform/functions';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const source=JSON.parse(await readFile(path.join(root,'docs/art/native-demo-sedan-source.json'),'utf8'));
const bytes=await readFile(path.join(root,'unreal/Saved/NativeDemoSedanSource/graphite_sedan.glb'));
const sha=b=>createHash('sha256').update(b).digest('hex');
if(bytes.length!==source.bytes||sha(bytes)!==source.sha256)throw Error('Pinned original sedan source required');
const output=path.join(root,'unreal/SourceAssets/NativeDemoSedan_v1');await mkdir(output,{recursive:true});
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS);
async function preserve(name,data){try{if(!Buffer.from(data).equals(await readFile(path.join(output,name))))throw Error('Existing prepared sedan preserved');}catch(e){if(e.code!=='ENOENT')throw e;await writeFile(path.join(output,name),data);}}
const models=[];let recordedHubs;
for(const selection of ['body','wheel_fl','wheel_fr','wheel_rl','wheel_rr']){
 const doc=await io.readBinary(bytes);await doc.transform(dequantize(),flatten({cleanup:false}));
 const r=doc.getRoot();if(r.listSkins().length||r.listAnimations().length)throw Error('Unexpected source rig; review required');
 const scene=r.getDefaultScene(),nodes=[];scene.traverse(n=>{if(n.getMesh())nodes.push(n);});
 const centre=n=>{const b=getBounds(n);return b.min.map((v,i)=>(v+b.max[i])/2);};
 const tyres=nodes.filter(n=>n.getName().startsWith('107 reused Sculpted_tyre'));
 if(tyres.length!==4)throw Error('Four individually identifiable source tyres required');
 // Original car front is -X; turn the model to Unreal's +X before import.
 const hubs=tyres.map(n=>{const p=centre(n);return {original:p,ue:[-p[0]*100,p[2]*100,p[1]*100]};});
 hubs.sort((a,b)=>b.ue[0]-a.ue[0]);hubs.splice(0,2,...hubs.slice(0,2).sort((a,b)=>a.ue[1]-b.ue[1]));hubs.splice(2,2,...hubs.slice(2,4).sort((a,b)=>a.ue[1]-b.ue[1]));
 recordedHubs=hubs.map(h=>h.ue);
 const wheelPart=n=>n.getName().startsWith('107 reused ')||n.getName().startsWith('Siped tread blocks');
 const wheelIndex=selection==='body'?-1:['wheel_fl','wheel_fr','wheel_rl','wheel_rr'].indexOf(selection);
 const mesh=doc.createMesh(selection);let count=0;
 for(const n of nodes){
  if(selection==='body' ? wheelPart(n) : !wheelPart(n))continue;
  if(wheelIndex>=0){const c=centre(n),distance=hubs.map(h=>Math.hypot(...c.map((v,i)=>v-h.original[i])));if(distance.indexOf(Math.min(...distance))!==wheelIndex)continue;}
  const copy=n.getMesh().clone();transformMesh(copy,n.getWorldMatrix());
  if(wheelIndex>=0){const [x,y,z]=hubs[wheelIndex].original;transformMesh(copy,[1,0,0,0,0,1,0,0,0,0,1,0,-x,-y,-z,1]);}
  transformMesh(copy,[-1,0,0,0,0,1,0,0,0,0,-1,0,0,0,0,1]);
  for(const p of copy.listPrimitives())mesh.addPrimitive(p);count++;
 }
 if(count<5)throw Error('Incomplete derived sedan part');
 for(const n of scene.listChildren())scene.removeChild(n);
 scene.addChild(doc.createNode(selection).setMesh(mesh));await doc.transform(prune());
 const result=await io.writeBinary(doc);await preserve(selection+'.glb',result);
 const bounds=getBounds(scene),dims=bounds.max.map((v,i)=>v-bounds.min[i]);
 models.push({id:selection,file:selection+'.glb',sha256:sha(result),bytes:result.length,sourceNodes:count,dimensionsMetresYUp:dims,objectPath:'/Game/Anomalia/NativeDemoSedan_v1/'+selection+'/SM_'+selection});
}
await preserve('manifest.json',JSON.stringify({schemaVersion:1,source,models,wheelHubsCm:recordedHubs,rigged:false,interactiveDoors:false,gameplayVerified:false},null,2)+'\n');
await preserve('CREDITS.md','# Original ANOMALIA demonstration sedan source\n\n'+source.author+'\n'+source.source+'\nCC0-1.0 — '+source.licenseUrl+'\n\nChanges: baked static transforms, forward-axis correction, preserved interior/body and separated original wheel assemblies. No original data deleted. Skeleton, interactive door openings and gameplay remain to be integrated and tested.\n');
console.log(JSON.stringify({models,wheelHubsCm:recordedHubs},null,2));
