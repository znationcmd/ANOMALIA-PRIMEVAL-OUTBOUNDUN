/** Khronos glTF structural validation, separate from Unreal visual/gameplay approval. */
import validator from 'gltf-validator';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
const folder=path.resolve(process.argv[2]);
const manifest=JSON.parse(await readFile(path.join(folder,'manifest.json'),'utf8'));
const results=[];
for(const model of manifest.models){
 if(path.basename(model.file)!==model.file)throw Error('Invalid source file');
 const bytes=await readFile(path.join(folder,model.file));
 if(bytes.length!==model.bytes||createHash('sha256').update(bytes).digest('hex')!==model.sha256)throw Error('Prepared asset identity mismatch');
 const r=await validator.validateBytes(new Uint8Array(bytes),{maxIssues:10000});
 results.push({id:model.id,errors:r.issues.numErrors,warnings:r.issues.numWarnings,messages:r.issues.messages.filter(m=>m.severity===0).slice(0,20)});
}
const report={sourceCommit:process.env.GITHUB_SHA||'manual',state:results.some(r=>r.errors)?'FAILED':'GLTF_STRUCTURE_VALIDATED_NOT_VISUALLY_REVIEWED',models:results};
if(process.argv[3]){await mkdir(path.dirname(process.argv[3]),{recursive:true});await writeFile(process.argv[3],JSON.stringify(report,null,2)+'\n');}
console.log(JSON.stringify(report));if(report.state==='FAILED')process.exitCode=1;
