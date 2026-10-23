/** Bake scene transforms for isolated review; source units remain unaltered. */
import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {dequantize,flatten,getBounds,prune,transformMesh} from '@gltf-transform/functions';
import {createHash} from 'node:crypto';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const registry=JSON.parse(await readFile(path.join(root,'docs/art/world-features-sources.json'),'utf8'));
const input=path.join(root,'unreal/SourceAssets/WorldFeatures1');
const output=path.join(root,'unreal/SourceAssets/WorldFeaturesPrepared_v1');
await mkdir(output,{recursive:true});
const sha=b=>createHash('sha256').update(b).digest('hex');
async function preserve(file,data){
 try{if(!Buffer.from(data).equals(await readFile(file)))throw Error('Existing prepared asset preserved: '+file);}
 catch(e){if(e.code!=='ENOENT')throw e;await writeFile(file,data);}
}
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS),models=[];
const credits=['# World features for ANOMALIA','Distribution: AllenAI Objaverse, ODC-By. https://huggingface.co/datasets/allenai/objaverse',
 'Individual model licenses follow. Static transforms baked and geometry bottom centred; original source files retained.',
 'Units preserved from sources. Physical scale, access, collision and visual quality require native review.',''];
for(const item of registry.models){
 const source=path.join(input,item.file),original=await readFile(source);
 if(original.length!==item.bytes||sha(original)!==item.sha256||item.license!=='CC-BY-4.0')throw Error('Source identity/license mismatch');
 const doc=await io.read(source),r=doc.getRoot();
 if(r.listSkins().length||r.listAnimations().length||r.listScenes().length!==1)throw Error('Dedicated rigged/multiscene import required: '+item.id);
 await doc.transform(dequantize(),flatten({cleanup:false}));
 const scene=r.listScenes()[0],mesh=doc.createMesh(item.id),nodes=[];let omittedLinePrimitives=0;
 scene.traverse(n=>{if(n.getMesh())nodes.push(n);});
 for(const node of nodes){
  const copy=node.getMesh().clone();transformMesh(copy,node.getWorldMatrix());
  for(const p of copy.listPrimitives()){
   if(p.getMode()===1){omittedLinePrimitives++;continue;}
   if(p.getMode()!==4||!p.getAttribute('POSITION'))throw Error('Unsupported source primitive');
   mesh.addPrimitive(p);
  }
 }
 if(!mesh.listPrimitives().length)throw Error('Empty model');
 for(const node of scene.listChildren())scene.removeChild(node);
 scene.addChild(doc.createNode(item.id).setMesh(mesh));
 let bounds=getBounds(scene);
 const dims=bounds.max.map((v,i)=>v-bounds.min[i]);
 if(dims.some(v=>!Number.isFinite(v)||v<=0))throw Error('Invalid geometry bounds');
 transformMesh(mesh,[1,0,0,0,0,1,0,0,0,0,1,0,-(bounds.min[0]+bounds.max[0])/2,-bounds.min[1],-(bounds.min[2]+bounds.max[2])/2,1]);
 await doc.transform(prune());
 const bytes=await io.writeBinary(doc);await preserve(path.join(output,item.file),bytes);
 models.push({...item,sha256:sha(bytes),bytes:bytes.length,originalSha256:item.sha256,
  dimensionsSourceUnitsYUp:dims,triangles:mesh.listPrimitives().reduce((s,p)=>s+(p.getIndices()?.getCount()||p.getAttribute('POSITION').getCount())/3,0),
  omittedLinePrimitives,state:'PREPARED_NOT_IMPORTED',objectPath:'/Game/Anomalia/WorldFeaturesReview_v1/'+item.id+'/SM_'+item.id});
 credits.push('## '+item.name,item.author,item.source,item.license+' — '+item.licenseUrl,
  'Changes: baked static transforms, bottom-centred geometry; omitted '+omittedLinePrimitives+' non-surface line primitives.','');
 console.log(item.id,bytes.length,dims);
}
await preserve(path.join(output,'manifest.json'),Buffer.from(JSON.stringify({schemaVersion:1,models},null,2)+'\n'));
await preserve(path.join(output,'CREDITS.md'),Buffer.from(credits.join('\n')+'\n'));
