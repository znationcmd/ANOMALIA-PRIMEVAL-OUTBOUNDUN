'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const crypto=require('node:crypto');
const {AnomaliaTools}=require('../core.cjs');
const {filesFor}=require('../native-mods.cjs');

function init(t){
  const root=fs.mkdtempSync(path.join(os.tmpdir(),'anomalia-workshop-'));
  t.after(()=>fs.rmSync(root,{recursive:true,force:true}));
  const tools=new AnomaliaTools(root);
  const project=tools.createProject({name:'Mon Vehicule'});
  return {root,tools,id:project.id,project:tools.getProjectPath(project.id)};
}
test('Workshop displays real projects only, no synthetic community counts',t=>{
  const {tools,id}=init(t);
  const empty=tools.listWorkshopMods();
  assert.equal(empty.entries.length,0);
  assert.equal(empty.projects.length,1);
  assert.equal(empty.stats.total,0);
  assert.equal(empty.connection.tools,true);
  assert.equal(empty.connection.game,false);
  assert.equal(empty.connection.community,false);
  tools.publishWorkshopMod({projectId:id,title:'Voiture réaliste',category:'Véhicules',version:'1.0.0'});
  assert.equal(tools.listWorkshopMods().entries.length,1);
  assert.equal(tools.listWorkshopMods().entries[0].compiled,false);
});
test('local publication, filtering fields and subscription survive new app instance',t=>{
  const {tools,root,id}=init(t);
  assert.throws(()=>tools.publishWorkshopMod({projectId:id,category:'Armes',title:'X',version:'bad'}),/Version/);
  assert.throws(()=>tools.publishWorkshopMod({projectId:id,category:'Super catégorie',title:'X',version:'1.0.0'}),/Catégorie/);
  tools.publishWorkshopMod({projectId:id,title:'SUV 4x4',description:'Véhicule de survie',category:'Véhicules',version:'1.2.3'});
  tools.subscribeWorkshopMod({projectId:id,value:true});
  const fresh=new AnomaliaTools(root);
  assert.equal(fresh.listWorkshopMods().entries[0].subscribed,true);
  assert.equal(fresh.listWorkshopMods().entries[0].category,'Véhicules');
  fresh.subscribeWorkshopMod({projectId:id,value:false});
  assert.equal(fresh.listWorkshopMods().entries[0].subscribed,false);
  assert.throws(()=>fresh.subscribeWorkshopMod({projectId:'unknown-123'}),/introuvable|publié/);
});
test('uncompiled plugin cannot be installed or activated',t=>{
  const {tools,id}=init(t);
  tools.publishWorkshopMod({projectId:id,title:'Petit mod',category:'Autres',version:'0.1.0'});
  assert.throws(()=>tools.prepareWorkshopMod({projectId:id}),/non compilé/);
  assert.throws(()=>tools.toggleWorkshopMod({projectId:id,enabled:false}),/Prépare/);
});
test('local installation accepts matching compiled plugin evidence, verifies copy, and toggles',t=>{
  const {tools,id,project,root}=init(t);
  tools.publishWorkshopMod({projectId:id,title:'SUV',category:'Véhicules',version:'0.5.0'});
  const plugin=tools.scaffoldNativeMod({projectId:id}).plugin;
  const p=filesFor(project,id);
  fs.mkdirSync(path.join(p.output,'Binaries','Win64'),{recursive:true});
  fs.writeFileSync(path.join(p.output,plugin+'.uplugin'),JSON.stringify({FileVersion:3,Modules:[{Name:plugin,Type:'Runtime'}]}));
  fs.writeFileSync(path.join(p.output,'Binaries','Win64',plugin+'.dll'),'test fixture only: not an Unreal binary');
  fs.writeFileSync(path.join(project,'Dist',plugin+'-native-build.json'),JSON.stringify({schema:'anomalia-native-build',plugin,projectId:id,platform:'Win64'}));
  assert.equal(tools.listWorkshopMods().entries[0].compiled,true);
  const handoff=tools.exportWorkshopHostingManifest({projectId:id});
  assert.equal(handoff.schema,'anomalia-hosting-mod-handoff');
  assert.equal(handoff.game,'anomalia-primeval-outboundun');
  assert.equal(handoff.deployment.ready,false);
  assert.equal(handoff.mod.files.length,2);
  assert.ok(handoff.mod.files.every(f=>!path.isAbsolute(f.path)&&f.sha256.length===64));
  assert.ok(!JSON.stringify(handoff).includes(root),'Do not expose private absolute paths');
  const prepared=tools.prepareWorkshopMod({projectId:id});
  assert.equal(prepared.prepared,true);
  assert.equal(prepared.gameLoaded,false);
  assert.ok(fs.existsSync(path.join(root,'_workshop','installed',plugin,plugin+'.uplugin')));
  assert.equal(tools.listWorkshopMods().stats.prepared,1);
  assert.equal(tools.toggleWorkshopMod({projectId:id,enabled:false}).gameLoaded,false);
  assert.equal(tools.listWorkshopMods().entries[0].active,false);
  assert.equal(tools.toggleWorkshopMod({projectId:id,enabled:true}).enabled,true);
  const again=tools.prepareWorkshopMod({projectId:id});
  assert.equal(again.prepared,true);
});
test('symlinks in staged files are rejected',t=>{
  if(process.platform==='win32')return;
  const {tools,id,project}=init(t);
  tools.publishWorkshopMod({projectId:id,title:'Test',version:'0.1.0'});
  const p=filesFor(project,id),name=p.name;
  fs.mkdirSync(p.output,{recursive:true});
  fs.writeFileSync(path.join(p.output,name+'.uplugin'),'{}');
  fs.symlinkSync(project,path.join(p.output,'evil'),'dir');
  fs.writeFileSync(path.join(project,'Dist',name+'-native-build.json'),JSON.stringify({schema:'anomalia-native-build',plugin:name,projectId:id,platform:'Win64'}));
  assert.throws(()=>tools.prepareWorkshopMod({projectId:id}),/symbolique/);
});
test('Workshop installed application includes backing module, page and events',()=>{
  const pkg=require('../package.json');
  const html=fs.readFileSync(path.resolve(__dirname,'../index.html'),'utf8');
  const js=fs.readFileSync(path.resolve(__dirname,'../src/renderer.js'),'utf8');
  const electron=fs.readFileSync(path.resolve(__dirname,'../main.cjs'),'utf8');
  assert.ok(pkg.build.files.includes('workshop.cjs'));
  assert.match(electron,/tools:exportHostingManifest/);
  assert.match(js,/exportHostingManifest/);
  assert.equal(pkg.version,'0.2.6');
  for(const id of ['wsModGrid','wsCategories','wsPublishForm','wsSearch','wsConnection','wsProjectSelect']){
    assert.ok(id==='wsConnection'||html.includes('id="'+id+'"'),'Missing Workshop HTML '+id);
  }
  for(const name of ['listWorkshopMods','publishWorkshopMod','subscribeWorkshopMod','prepareWorkshopMod','toggleWorkshopMod']){
    assert.match(electron,new RegExp(name));
    assert.match(js,new RegExp(name));
  }
  assert.match(html,/ANOMALIA/);
  assert.doesNotMatch(html,/158K membres|2 347 mods/);
});

test('Windows game menu opens a registered ANOMALIA Tools Workshop deep link',()=>{
  const projectRoot=path.resolve(__dirname,'../../..');
  const menu=fs.readFileSync(path.join(projectRoot,'src','start-menu.js'),'utf8');
  const gameMain=fs.readFileSync(path.join(projectRoot,'desktop','main.cjs'),'utf8');
  const gamePreload=fs.readFileSync(path.join(projectRoot,'desktop','preload.cjs'),'utf8');
  const toolsMain=fs.readFileSync(path.join(projectRoot,'apps','anomalia-tools','main.cjs'),'utf8');
  assert.match(menu,/startWorkshopBtn/);
  assert.match(menu,/anomaliaServer\.openWorkshop/);
  assert.match(gameMain,/anomalia:open-workshop/);
  assert.match(gameMain,/anomalia-tools:\/\/workshop/);
  assert.match(gamePreload,/openWorkshop/);
  assert.match(toolsMain,/requestSingleInstanceLock/);
  assert.match(toolsMain,/tools:navigate/);
});
