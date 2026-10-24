'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const vm=require('node:vm');
const {EventEmitter}=require('node:events');
const {createRequire}=require('node:module');
test('Native launch selects a scanned map using an argument array and refuses injected map names',async()=>{
 const temp=fs.mkdtempSync(path.join(os.tmpdir(),'anomalia-launch-'));
 try{
  const exe=path.join(temp,'Engine','Binaries','Win64','UnrealEditor.exe');fs.mkdirSync(path.dirname(exe),{recursive:true});fs.writeFileSync(exe,'fixture');
  const file=path.resolve(__dirname,'../desktop/ue5-bridge.cjs');const ownRequire=createRequire(file);
  const calls=[];const exported={exports:{}};
  vm.runInNewContext(fs.readFileSync(file,'utf8'),{
   module:exported,process,require:name=>name==='electron'?{shell:{openPath:async()=>''}}:
    name==='node:child_process'?{spawn:(...args)=>{calls.push(args);const child=new EventEmitter();child.unref=()=>{};process.nextTick(()=>child.emit('spawn'));return child;}}:ownRequire(name)
  });
  const bridge=new exported.exports.UnrealBridge(temp);
  bridge.status=async()=>({linked:true,automatic:true,project:path.join(temp,'AnomaliaPrimeval.uproject'),projectRoot:temp,
   engineRoot:temp,projectName:'AnomaliaPrimeval',mapPackage:'/Game/Maps/ANOMALIA_Inhabited_v2',
   maps:['Maps/ANOMALIA_Inhabited_v2.umap','Maps/ANOMALIA_Playable_v1.umap']});
  const opened=await bridge.launch();assert.equal(opened.mapPackage,'/Game/Maps/ANOMALIA_Inhabited_v2');
  assert.equal(calls[0][0],exe);assert.equal(calls[0][1][1],'/Game/Maps/ANOMALIA_Inhabited_v2');assert.equal(calls[0][2].shell,false);
  await bridge.launch('Maps/ANOMALIA_Playable_v1.umap');assert.equal(calls[1][1][1],'/Game/Maps/ANOMALIA_Playable_v1');
  for(const name of ['Maps/Absent.umap','../escape.umap','Maps/ANOMALIA_Playable_v1.umap?exec=bad'])await assert.rejects(()=>bridge.launch(name),/Carte absente/);
  assert.equal(calls.length,2);
 }finally{fs.rmSync(temp,{recursive:true,force:true});}
});
