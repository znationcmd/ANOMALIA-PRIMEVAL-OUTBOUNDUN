/** Assemble licensed art without simplification into an isolated Unreal validation namespace. */
import {NodeIO,Accessor} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {dequantize,flatten,getBounds,prune,transformMesh} from '@gltf-transform/functions';
import {createHash} from 'node:crypto';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const registry=JSON.parse(await readFile(path.join(root,'docs/art/realism-validation-sources.json'),'utf8'));
const cache=path.join(root,'unreal/Saved/RealismSourceCache');
const output=path.join(root,'unreal/SourceAssets/RealismValidation_v1');await mkdir(output,{recursive:true});
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS);
const sha=b=>createHash('sha256').update(b).digest('hex');
async function preserve(file,data){try{if(!Buffer.from(data).equals(await readFile(file)))throw Error('Existing prepared art preserved: '+file);}catch(e){if(e.code!=='ENOENT')throw e;await writeFile(file,data);}}
function plane(doc,id,terrain){
 const r=doc.getRoot(),buffer=r.listBuffers()[0]||doc.createBuffer();
 const points=[],normals=[],uv=[],indices=[],n=terrain?128:1,size=terrain?200:200,width=terrain?200:8;
 const smooth=v=>{const t=Math.max(0,Math.min(1,v));return t*t*(3-2*t);};
 const height=(x,z)=>terrain?2.8*Math.sin(x*.045)*Math.cos(z*.035)*smooth((Math.hypot(x,z)-25)/35)*smooth((Math.abs(x-15)-5)/8):0;
 for(let z=0;z<=n;z++)for(let x=0;x<=n;x++){
  const px=(x/n-.5)*width,pz=(z/n-.5)*size,y=height(px,pz),dx=(height(px+.01,pz)-height(px-.01,pz))/.02,dz=(height(px,pz+.01)-height(px,pz-.01))/.02,len=Math.hypot(dx,1,dz);
  points.push(px,y,pz);normals.push(-dx/len,1/len,-dz/len);uv.push(px/3,pz/3);
 }
 for(let z=0;z<n;z++)for(let x=0;x<n;x++){const a=z*(n+1)+x,b=a+1,c=a+n+1,d=c+1;indices.push(a,c,b,b,c,d);}
 const accessor=(type,data)=>doc.createAccessor().setType(type).setArray(data).setBuffer(buffer);
 return doc.createMesh(id).addPrimitive(doc.createPrimitive().setAttribute('POSITION',accessor(Accessor.Type.VEC3,new Float32Array(points))).setAttribute('NORMAL',accessor(Accessor.Type.VEC3,new Float32Array(normals))).setAttribute('TEXCOORD_0',accessor(Accessor.Type.VEC2,new Float32Array(uv))).setIndices(accessor(Accessor.Type.SCALAR,new Uint32Array(indices))).setMaterial(r.listMaterials()[0]));
}
const models=[],credits=['# ANOMALIA visual validation assets','Prepared for native review, not a declaration of final photorealism.','Powered by Poly Haven — https://polyhaven.com',''];
for(const entry of registry.models){
 for(const f of entry.files){const b=await readFile(path.join(cache,entry.id,f.path));if(b.length!==f.bytes||sha(b)!==f.sha256)throw Error('Pinned source changed: '+entry.id);}
 const doc=await io.read(path.join(cache,entry.id,entry.sourceFile)),r=doc.getRoot();
 if(r.listSkins().length)throw Error('Rigged art requires a dedicated importer');
 for(const a of r.listAnimations())a.dispose();
 if(entry.id==='concept_car'){
  // This pinned source uses texture index 3 for the two excluded Khronos marks.
  const logo=r.listTextures()[3];if(!logo)throw Error('Pinned logo texture missing');
  for(const material of r.listMaterials()){
   if(material.getBaseColorTexture()===logo)material.setBaseColorTexture(null).setBaseColorFactor([.015,.015,.015,1]);
   if(material.getEmissiveTexture()===logo)material.setEmissiveTexture(null).setEmissiveFactor([0,0,0]);
  }
 }
 await doc.transform(dequantize(),flatten({cleanup:false}));
 const scene=r.getDefaultScene()||r.listScenes()[0];if(!scene||r.listScenes().length!==1)throw Error('One source scene required');
 const generated=['forest_ground_04','asphalt_02'].includes(entry.id);
 let mesh;
 if(generated)mesh=plane(doc,entry.id,entry.id==='forest_ground_04');
 else{
  mesh=doc.createMesh(entry.id);const nodes=[];scene.traverse(n=>{if(n.getMesh())nodes.push(n);});
  for(const node of nodes){
   // A review variant with open doorways; retain the original source unchanged.
   if(entry.id==='detached_house' && /entrance (closed finite door leaf|handle spindle|lever handle)/i.test(node.getName()))continue;
   const copy=node.getMesh().clone();transformMesh(copy,node.getWorldMatrix());
   for(const primitive of copy.listPrimitives())if(primitive.getMode()===4)mesh.addPrimitive(primitive);
  }
 }
 for(const n of scene.listChildren())scene.removeChild(n);
 scene.addChild(doc.createNode(entry.id).setMesh(mesh));
 for(const extension of r.listExtensionsUsed())if(extension.extensionName==='KHR_materials_variants')extension.dispose();
 await doc.transform(prune());
 let bounds=getBounds(scene);
 if(!generated){const {min,max}=bounds;transformMesh(mesh,[1,0,0,0,0,1,0,0,0,0,1,0,-(min[0]+max[0])/2,-min[1],-(min[2]+max[2])/2,1]);}
 bounds=getBounds(scene);const dims=bounds.max.map((v,i)=>v-bounds.min[i]);
 if(entry.id==='detached_house' && (Math.max(...dims)<10||Math.max(...dims)>20))throw Error('House scale not in metres');
 if(entry.id==='concept_car' && (Math.max(...dims)<3||Math.max(...dims)>7))throw Error('Car scale not in metres');
 const bytes=await io.writeBinary(doc);await preserve(path.join(output,entry.id+'.glb'),bytes);
 const triangles=mesh.listPrimitives().reduce((s,p)=>s+(p.getIndices()?.getCount()||p.getAttribute('POSITION').getCount())/3,0);
 models.push({id:entry.id,file:entry.id+'.glb',sha256:sha(bytes),bytes:bytes.length,triangles,dimensionsMetresYUp:dims,objectPath:'/Game/Anomalia/VisualValidation_v1/'+entry.id+'/SM_'+entry.id,source:entry.source,author:entry.author,license:entry.license,licenseUrl:entry.licenseUrl});
 credits.push('## '+entry.id,entry.author,entry.source,entry.license+' — '+entry.licenseUrl,'Changes: baked static transforms, retained original material maps, bottom-centred geometry. Terrain/road geometry is original ANOMALIA; uses credited source textures.',...(entry.id==='concept_car'?['Excluded Khronos logo texture removed; no affiliation or endorsement.']:[]),...(entry.id==='detached_house'?['Entrance leaves and their handles omitted in this open-door review variant; source retained intact. Door animations are not implemented.']:[]),'');
 console.log(entry.id,bytes.length,triangles,dims);
}
await preserve(path.join(output,'manifest.json'),Buffer.from(JSON.stringify({schemaVersion:1,models},null,2)+'\n'));
await preserve(path.join(output,'CREDITS.md'),Buffer.from(credits.join('\n')+'\n'));
