import test from 'node:test';
import assert from 'node:assert/strict';
import os from 'node:os';
import path from 'node:path';
import fs from 'node:fs';
import { EventEmitter } from 'node:events';
import { createRequire } from 'node:module';

const require=createRequire(import.meta.url);
const bridge=require('../desktop/native-skarvik-bridge.cjs');
const { getNativePreviewStatus, publicPreviewStatus, launchNativePreview, WORLD }=bridge;

function fixture(){
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'anomalia-skarvik-'));
 const stage=path.join(dir,'native-stage');
 const editorRoot=path.join(dir,'UE_5.8');
 fs.mkdirSync(path.join(stage,'Content','Maps'),{recursive:true});
 fs.mkdirSync(path.join(editorRoot,'Engine','Binaries','Win64'),{recursive:true});
 const editor=path.join(editorRoot,'Engine','Binaries','Win64','UnrealEditor.exe');
 fs.writeFileSync(editor,'dummy-test-editor','utf8');
 fs.writeFileSync(path.join(stage,'AnomaliaZPrigimalia.uproject'),'{}');
 fs.writeFileSync(path.join(stage,'Content','Maps','PRIGIMALIA_SKARVIK_FINAL_v1.umap'),'test-map');
 fs.writeFileSync(path.join(stage,'.skarvik-ci-stage-marker'),'41188816555\n');
 const options={stageRoot:stage,platform:'win32',env:{UE_ROOT:editorRoot}};
 return {dir,stage,editor,options,close:()=>fs.rmSync(dir,{recursive:true,force:true})};
}
test('the true World Partition final map and trusted editor are detected only with the exact marker',()=>{
 const f=fixture();
 try{
  const state=getNativePreviewStatus(f.options);
  assert.equal(state.available,true);
  assert.equal(state.world,WORLD);
  assert.equal(state.state,'editor-preview-ready');
  assert.equal(state.mode,'unreal-editor-preview');
  assert.ok(state._editorPath.endsWith('UnrealEditor.exe'));
  const sanitized=publicPreviewStatus(state);
  assert.equal(sanitized._editorPath,undefined);
  assert.equal(sanitized._projectPath,undefined);
  fs.writeFileSync(path.join(f.stage,'.skarvik-ci-stage-marker'),'wrong');
  assert.equal(getNativePreviewStatus(f.options).available,false);
 }finally{f.close()}
});
test('missing final native map disables launch',async()=>{
 const f=fixture();
 try{
  fs.unlinkSync(path.join(f.stage,'Content','Maps','PRIGIMALIA_SKARVIK_FINAL_v1.umap'));
  assert.equal(getNativePreviewStatus(f.options).state,'map-not-present');
  let attempted=false;
  const r=await launchNativePreview({...f.options,spawn:()=>{attempted=true;}});
  assert.equal(r.started,false);
  assert.equal(attempted,false);
 }finally{f.close()}
});
test('Windows-only preview always reports truthful status',()=>{
 assert.equal(getNativePreviewStatus({platform:'linux'}).state,'windows-required');
});
test('launch uses fixed project/map and executable, not renderer-provided paths or shell',async()=>{
 const f=fixture();
 try{
  let cmd,args,options;
  const result=await launchNativePreview({...f.options,
   spawn:(executable,argv,opts)=>{
    cmd=executable;args=argv;options=opts;
    const emitter=new EventEmitter();
    emitter.unref=()=>{};
    process.nextTick(()=>emitter.emit('spawn'));
    return emitter;
   }
  });
  assert.equal(result.started,true);
  assert.equal(cmd,f.editor);
  assert.deepEqual(args,[path.join(f.stage,'AnomaliaZPrigimalia.uproject'),WORLD,'-log']);
  assert.equal(options.shell,false);
  assert.equal(options.detached,true);
 }finally{f.close()}
});
