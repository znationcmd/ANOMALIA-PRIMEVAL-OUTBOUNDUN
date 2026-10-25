/** Derive original gameplay terrain from already verified, credited PBR surfaces. */
import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {playableHeight,playableNormal} from './playable-landscape.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const base=path.join(root,'unreal/SourceAssets/RealismValidation_v2');
const output=path.join(root,'unreal/SourceAssets/PlayableLandscape_v2');
const source=JSON.parse(await readFile(path.join(base,'manifest.json'),'utf8')).models.find(m=>m.id==='forest_ground_04');
const bytes=await readFile(path.join(base,source.file));
const sha=b=>createHash('sha256').update(b).digest('hex');
if(sha(bytes)!==source.sha256)throw Error('Verified terrain source required');
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS);const doc=await io.readBinary(bytes);
for(const mesh of doc.getRoot().listMeshes())for(const p of mesh.listPrimitives()){
 const positions=p.getAttribute('POSITION'),normals=p.getAttribute('NORMAL');
 if(!positions||!normals)throw Error('Terrain positions and normals required');
 for(let i=0;i<positions.getCount();i++){
  const [x,,z]=positions.getElement(i,[]);positions.setElement(i,[x,playableHeight(x,z),z]);normals.setElement(i,playableNormal(x,z));
 }
}
const result=await io.writeBinary(doc);await mkdir(output,{recursive:true});
async function preserve(name,data){try{if(!Buffer.from(data).equals(await readFile(path.join(output,name))))throw Error('Existing prepared playable terrain preserved');}catch(e){if(e.code!=='ENOENT')throw e;await writeFile(path.join(output,name),data);}}
await preserve('playable_terrain.glb',result);
await preserve('manifest.json',JSON.stringify({schemaVersion:1,sourceSha256:source.sha256,sha256:sha(result),file:'playable_terrain.glb',objectPath:'/Game/Anomalia/PlayableLandscape_v2/SM_PlayableTerrain',geometry:'Original ANOMALIA; 200 m, reserved flat gameplay parcels, rolling forest perimeter',source:source.source,author:source.author,license:source.license,licenseUrl:source.licenseUrl},null,2)+'\n');
await preserve('CREDITS.md',(await readFile(path.join(base,'CREDITS.md'),'utf8'))+'\nPlayable terrain geometry: original ANOMALIA. Central gameplay parcels and road remain flat; outer forest relief added.\n');
console.log('Verified playable PBR terrain prepared',sha(result));
