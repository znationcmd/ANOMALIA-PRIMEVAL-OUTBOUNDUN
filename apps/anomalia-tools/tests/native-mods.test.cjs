'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const {scaffoldNativeMod,validateNativeMod,buildStatus,buildNativeMod,pluginNameFor}=require('../native-mods.cjs');
const {AnomaliaTools}=require('../core.cjs');
function setup(t){
  const folder=fs.mkdtempSync(path.join(os.tmpdir(),'anomalia-native-mod-'));
  t.after(()=>fs.rmSync(folder,{recursive:true,force:true}));
  const api=new AnomaliaTools(folder);
  const projectId=api.createProject({name:'Native Demo'}).id;
  return {folder,api,projectId,root:api.getProjectPath(projectId)};
}
test('scaffold generates an Unreal Runtime plugin descriptor, rules, C++ and content directory',t=>{
  const {api,projectId,root}=setup(t);
  const result=api.scaffoldNativeMod({projectId});
  assert.equal(result.created.length,4);
  assert.match(result.plugin,/^ANM[A-Za-z0-9]+$/);
  const descriptor=path.join(root,result.descriptor);
  assert.equal(JSON.parse(fs.readFileSync(descriptor,'utf8')).Modules[0].Name,result.plugin);
  assert.equal(api.validateNativeMod({projectId}).valid,true);
  const cpp=path.join(root,'Plugins',result.plugin,'Source',result.plugin,'Private',result.plugin+'Module.cpp');
  assert.match(fs.readFileSync(cpp,'utf8'),/IMPLEMENT_MODULE/);
});
test('repeated scaffolding never overwrites author files',t=>{
  const {api,projectId,root}=setup(t);
  const r=api.scaffoldNativeMod({projectId});
  const cpp=path.join(root,'Plugins',r.plugin,'Source',r.plugin,'Private',r.plugin+'Module.cpp');
  fs.appendFileSync(cpp,'// user extension\n');
  assert.equal(api.scaffoldNativeMod({projectId}).created.length,0);
  assert.match(fs.readFileSync(cpp,'utf8'),/user extension/);
});
test('broken module descriptor is rejected and does not compile',t=>{
  const {api,projectId,root}=setup(t);
  const r=api.scaffoldNativeMod({projectId});
  const descriptor=path.join(root,r.descriptor);
  fs.writeFileSync(descriptor,'{"FileVersion":1,"Modules":[]}');
  assert.throws(()=>api.validateNativeMod({projectId}),/incompatible/);
  assert.equal(api.getNativeModStatus({projectId}).valid,false);
  assert.throws(()=>api.buildNativeMod({projectId}),/incompatible/);
});
test('native build requires Unreal RunUAT and never reports ZIP as cooked content',t=>{
  const {api,projectId}=setup(t);
  api.scaffoldNativeMod({projectId});
  const state=api.getNativeModStatus({projectId,engineRoot:'Z:/missing-ue'});
  assert.equal(state.nativeBuildAvailable,false);
  assert.equal(state.engineFound,false);
  assert.match(state.note,/mod cuit/);
  assert.throws(()=>api.buildNativeMod({projectId,engineRoot:'Z:/missing-ue'}),/Windows|RunUAT/);
});
test('no unsafe project IDs or symbolic plugin output paths',t=>{
  const {api,projectId,root}=setup(t);
  assert.throws(()=>pluginNameFor('../danger'),/Identifiant/);
  const outside=fs.mkdtempSync(path.join(os.tmpdir(),'anomalia-outside-'));
  t.after(()=>fs.rmSync(outside,{recursive:true,force:true}));
  if(process.platform!=='win32'){
    fs.symlinkSync(outside,path.join(root,'Plugins'),'dir');
    assert.throws(()=>api.scaffoldNativeMod({projectId}),/symbolique/);
  }
});
test('source ZIP remains distinct from native plugin build',async t=>{
  const {api,projectId}=setup(t);
  api.scaffoldNativeMod({projectId});
  const pkg=await api.packageMod({projectId});
  assert.match(pkg.manifest.note,/non compilée/);
  assert.ok(pkg.manifest.assets.some(x=>x.path.endsWith('.uplugin')));
  assert.ok(!pkg.manifest.assets.some(x=>x.path.startsWith('Dist/')));
});
