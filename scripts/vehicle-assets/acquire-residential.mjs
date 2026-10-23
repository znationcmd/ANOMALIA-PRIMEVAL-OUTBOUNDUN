/** Acquire individually CC0 architectural sources for detailed native review. */
import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {getBounds} from '@gltf-transform/functions';
import {createHash,randomUUID} from 'node:crypto';
import {readFile,writeFile,mkdir,rename,unlink} from 'node:fs/promises';
import {spawn} from 'node:child_process';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const base=path.join(root,'unreal/SourceAssets/ResidentialSource_v1');
await mkdir(base,{recursive:true});
const sources=[
 {id:'townhouse_row',slug:'row-of-three-townhouses-c954dc27',dimensionsMetresYUp:[18.720,9.147,12.170]},
 {id:'cottage',slug:'cottage-with-pitched-roof-bc88ab4f',dimensionsMetresYUp:[8.900,6.712,12.812]},
 {id:'modern_villa',slug:'modern-flat-roof-villa-12ed3c60',dimensionsMetresYUp:[15.189,6.832,14.021]},
 {id:'garage_apartment',slug:'garage-with-apartment-above-60d5222c',dimensionsMetresYUp:[9.610,8.589,8.966]}
];
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS);
const digest=b=>createHash('sha256').update(b).digest('hex');
function curl(url,file){return new Promise((resolve,reject)=>{
 const child=spawn(process.platform==='win32'?'curl.exe':'curl',['-fSL','--max-time','180','--max-filesize','40000000',url,'-o',file],{stdio:['ignore','ignore','pipe']});
 let error='';child.stderr.on('data',b=>{error=(error+b.toString()).slice(-1500);});
 child.on('error',reject);child.on('close',code=>code===0?resolve():reject(Error('Source download failed: '+code+' '+error)));
});}
const models=[];
for(const source of sources){
 const file=path.join(base,source.id+'.glb'),url='https://www.innerscene.com/api/library/'+source.slug+'/download';
 try{await readFile(file);}catch(e){
  if(e.code!=='ENOENT')throw e;
  const part=file+'.part-'+randomUUID();
  try{await curl(url,part);const b=await readFile(part);if(b.length>40000000||b.subarray(0,4).toString()!=='glTF'||b.readUInt32LE(4)!==2)throw Error('Invalid source GLB');await rename(part,file);}
  finally{try{await unlink(part);}catch(e){if(e.code!=='ENOENT')throw e;}}
 }
 const bytes=await readFile(file),doc=await io.read(file),r=doc.getRoot();
 if(r.listSkins().length||r.listAnimations().length||r.listScenes().length!==1)throw Error('Dedicated animated/multiscene source workflow required');
 const bounds=getBounds(r.listScenes()[0]),dimensions=bounds.max.map((v,i)=>v-bounds.min[i]);
 const triangles=r.listMeshes().reduce((sum,m)=>sum+m.listPrimitives().reduce((n,p)=>n+(p.getIndices()?.getCount()||p.getAttribute('POSITION')?.getCount()||0)/3,0),0);
 if(triangles<1000||!r.listTextures().length||dimensions.some((v,i)=>!Number.isFinite(v)||Math.abs(v-source.dimensionsMetresYUp[i])>.05))throw Error('Detailed textured metre-scale source check failed: '+source.id);
 models.push({id:source.id,slug:source.slug,file:source.id+'.glb',download:url,source:'https://www.innerscene.com/tools/library/3d-parts/'+source.slug,
  author:'Innerscene',license:'CC0-1.0',licenseUrl:'https://creativecommons.org/publicdomain/zero/1.0/',bytes:bytes.length,sha256:digest(bytes),
  dimensionsMetresYUp:dimensions,sourceTriangles:triangles,materials:r.listMaterials().length,textures:r.listTextures().length,
  state:'DOWNLOADED_SOURCE_NOT_IMPORTED',visualQualityValidated:false});
 process.stdout.write(JSON.stringify(models.at(-1))+'\n');
}
const registry=Buffer.from(JSON.stringify({schemaVersion:1,models},null,2)+'\n');
const destination=path.join(base,'manifest.json');
try{if(!(await readFile(destination)).equals(registry))throw Error('Existing residential manifest identity differs; preserved');}
catch(e){if(e.code!=='ENOENT')throw e;await writeFile(destination,registry);}
const creditPath=path.join(base,'CREDITS.md');
const credits=Buffer.from('# Residential architectural sources\n\nFour original Innerscene models, CC0 1.0.\nSource pages and hashes: manifest.json. Original GLBs unchanged.\nDownloaded and geometry checked; not imported, rendered or placed in Unreal.\n');
try{if(!(await readFile(creditPath)).equals(credits))throw Error('Existing residential credits differ; preserved');}
catch(e){if(e.code!=='ENOENT')throw e;await writeFile(creditPath,credits);}
