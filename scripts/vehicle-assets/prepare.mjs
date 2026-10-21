/** Convert pinned, credited CC BY source meshes into separate Unreal review assets. */
import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {convertPrimitiveToTriangles,dequantize,flatten,getBounds,prune,transformMesh} from '@gltf-transform/functions';
import {MeshoptDecoder} from 'meshoptimizer';
import sharp from 'sharp';
import {createHash} from 'node:crypto';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const args=process.argv.slice(2);
const output=path.resolve(args[0]||path.join(root,'unreal/SourceAssets/NamedVehicles1'));
const cache=path.resolve(args[1]||path.join(root,'unreal/Saved/VehicleSourceCache'));
const registry=JSON.parse(await readFile(path.join(root,'docs/vehicles/named-assets-sources.json'),'utf8'));
const sha=data=>createHash('sha256').update(data).digest('hex');
await mkdir(output,{recursive:true});await mkdir(cache,{recursive:true});await MeshoptDecoder.ready;
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.decoder':MeshoptDecoder});
const models=[],credits=['# Third-party vehicle art','Individual visual variants for review. No manufacturer affiliation.',''];
async function savePreserving(file,bytes){try{const prior=await readFile(file);if(!Buffer.from(bytes).equals(prior))throw Error('Existing artist output preserved: '+file);}catch(e){if(e.code!=='ENOENT')throw e;await writeFile(file,bytes);}}
for(const entry of registry.models){
 if(!/^[a-z0-9_]+$/.test(entry.id)||entry.license!=='CC-BY-4.0')throw Error('Invalid source registry');
 const source=path.join(cache,entry.sourceId+'.glb');let raw;
 try{raw=await readFile(source);}catch(e){if(e.code!=='ENOENT')throw e;const response=await fetch(entry.downloadUrl);if(!response.ok)throw Error('Source unavailable: '+entry.id);raw=Buffer.from(await response.arrayBuffer());if(sha(raw)!==entry.sourceSHA256||raw.length!==entry.sourceBytes)throw Error('Source integrity: '+entry.id);await writeFile(source,raw);}
 if(sha(raw)!==entry.sourceSHA256||raw.length!==entry.sourceBytes)throw Error('Source identity: '+entry.id);
 const doc=await io.readBinary(raw);const r=doc.getRoot();
 if(r.listSkins().length)throw Error('Skinned art needs dedicated rig import: '+entry.id);
 const animations=r.listAnimations().length;for(const a of r.listAnimations())a.dispose();
 await doc.transform(dequantize(),flatten({cleanup:false}));
 const scene=r.getDefaultScene()||r.listScenes()[0];if(!scene||r.listScenes().length!==1)throw Error('Expected one source scene');
 const nodes=[];scene.traverse(n=>{if(n.getMesh())nodes.push(n);});
 const mesh=doc.createMesh(entry.id);
 for(const node of nodes){const copy=node.getMesh().clone();transformMesh(copy,node.getWorldMatrix());for(const prim of copy.listPrimitives())mesh.addPrimitive(prim);}
 for(const p of mesh.listPrimitives()){if(p.getMode()===5||p.getMode()===6)convertPrimitiveToTriangles(p);if(p.getMode()!==4)mesh.removePrimitive(p);}
 if(!mesh.listPrimitives().length)throw Error('No source triangles');
 for(const node of scene.listChildren())scene.removeChild(node);
 const node=doc.createNode(entry.id).setMesh(mesh);scene.addChild(node);
 await doc.transform(prune());
 let {min,max}=getBounds(scene);let dims=max.map((v,i)=>v-min[i]);
 // Only obvious source centimetre/millimetre conventions are rescaled. Artist proportions are retained.
 const longest=Math.max(dims[0],dims[2]);const scale=longest>1000?.001:longest>100?.01:1;
 const matrix=[scale,0,0,0,0,scale,0,0,0,0,scale,0,-(min[0]+max[0])*scale/2,-min[1]*scale,-(min[2]+max[2])*scale/2,1];
 transformMesh(mesh,matrix);
 for(const texture of r.listTextures()){
  const image=texture.getImage();if(!image)continue;
  const png=await sharp(image,{limitInputPixels:100000000}).resize({width:1024,height:1024,fit:'inside',withoutEnlargement:true}).png().toBuffer();
  texture.setImage(png).setMimeType('image/png').setURI('');
 }
 for(const ext of r.listExtensionsUsed())if(['EXT_meshopt_compression','KHR_mesh_quantization','EXT_texture_webp'].includes(ext.extensionName))ext.dispose();
 await doc.transform(prune());
 ({min,max}=getBounds(scene));dims=max.map((v,i)=>v-min[i]);
 if(dims.some(d=>!Number.isFinite(d)||d<=0)||Math.max(dims[0],dims[2])<.1||Math.max(dims[0],dims[2])>100)throw Error('Car scale needs manual review: '+entry.id+' '+dims);
 const bytes=await io.writeBinary(doc);await savePreserving(path.join(output,entry.id+'.glb'),bytes);
 const triangles=mesh.listPrimitives().reduce((n,p)=>{if(p.getMode()!==4)throw Error('Expected triangle topology');return n+(p.getIndices()?.getCount()||p.getAttribute('POSITION').getCount())/3;},0);
 models.push({...entry,kind:'reference_vehicle',file:entry.id+'.glb',sha256:sha(bytes),bytes:bytes.length,triangles,dimensionsMetresYUp:dims,objectPath:'/Game/Anomalia/NamedVehicles1/'+entry.id+'/SM_'+entry.id,state:'ARTIST_VARIANT_STATIC_REVIEW_NOT_DRIVABLE',scaleFactor:scale,sourceUnitsUnverified:true,sourceBoundsNeedReview:(Math.max(dims[0],dims[2])<3||Math.max(dims[0],dims[2])>7||dims[1]<.8||dims[1]>3),scaleVerified:false,orientationValidated:false,manufacturerReplicaVerified:false,drivingTested:false,changes:['Source pack previously welded/simplified/meshopt compressed.','Decoded meshopt; baked node transforms into one static mesh; bottom-centred; inferred source unit scale '+scale+'.','Embedded textures converted to PNG with 1024px maximum; no additional mesh simplification.',...(animations?['Source animation removed for static review.']:[])]});
 credits.push('## '+entry.sourceTitle,'Artist: '+entry.artist+' — '+entry.artistUrl,'Original: '+entry.sourceUrl,'License: Creative Commons Attribution 4.0 — '+entry.licenseUrl,'Public mirror: '+entry.downloadUrl,'Changes: decoded compression, assembled static geometry, centred and inferred units; texture PNG conversion, maximum 1024px.',...entry.additionalCredits.map(c=>'Additional component: '+c.title+' by '+c.artist+' — '+c.sourceUrl+' ('+c.license+').'),'');
 console.log(entry.id,bytes.length,dims.map(v=>v.toFixed(3)).join(' × '));
}
await savePreserving(path.join(output,'manifest.json'),Buffer.from(JSON.stringify({schemaVersion:1,models,notes:registry.coverage},null,2)+'\n'));
await savePreserving(path.join(output,'CREDITS.md'),Buffer.from(credits.join('\n')+'\n'));
console.log('Prepared',models.length,'credited artist variants. Native import remains required.');
