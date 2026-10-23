'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const {PNG}=require('pngjs');
const {AnomaliaTools,validateEconomy,relativeSafe,heightAt}=require('../core.cjs');
function setup(t){
  const root=fs.mkdtempSync(path.join(os.tmpdir(),'anomalia-tools-'));
  t.after(()=>fs.rmSync(root,{recursive:true,force:true}));
  const api=new AnomaliaTools(root);
  const p=api.createProject({name:'Mon Mod Test'});
  return {root,api,projectId:p.id};
}
test('création et isolation de projets locaux',t=>{
  const {api,projectId}=setup(t);
  const two=api.createProject({name:'Deuxième projet'});
  assert.equal(api.listProjects().length,2);
  assert.notEqual(projectId,two.id);
  assert.equal(api.overview().privacy,'local-only');
  assert.throws(()=>api.getProjectPath('../CMD Studio'));
  assert.ok(api.listFiles({projectId}).some(f=>f.path==='Source/module.cpp'));
});
test('Workbench : ouvrir et sauver fichier, refuser traversal et fichiers secrets',t=>{
  const {api,projectId}=setup(t);
  const code=api.readText({projectId,file:'Source/module.cpp'});
  assert.match(code.content,/ANOMALIA/);
  api.writeText({projectId,file:'Source/test_script.cpp',content:'int value = 42;\n'});
  assert.equal(api.readText({projectId,file:'Source/test_script.cpp'}).content,'int value = 42;\n');
  assert.throws(()=>api.readText({projectId,file:'../other.cpp'}));
  assert.throws(()=>api.writeText({projectId,file:'.env',content:'SECRET=1'}));
  assert.throws(()=>relativeSafe(api.getProjectPath(projectId),'../cmd-studio/password'));
});
test('Central Economy : validation et persistance',t=>{
  const {api,projectId}=setup(t);
  const economy=api.getEconomy({projectId});
  assert.ok(economy.items.length>=3);
  economy.items.push({id:'custom_med',category:'Médical',min:1,max:4,chance:22});
  assert.equal(api.saveEconomy({projectId,economy}).count,4);
  assert.equal(api.getEconomy({projectId}).items[3].id,'custom_med');
  assert.throws(()=>validateEconomy({items:[{id:'x',min:0,max:2,chance:101}]}));
  assert.throws(()=>validateEconomy({items:[{id:'x',min:0,max:2,chance:10},{id:'x',min:0,max:2,chance:10}]}));
});
test('Terrain Builder : heightmap PNG réelle, reproductible, bonne taille',t=>{
  const {api,projectId}=setup(t);
  const terrain=api.generateTerrain({projectId,seed:123,resolution:128,octaves:5});
  const full=path.join(api.getProjectPath(projectId),terrain.image);
  const decoded=PNG.sync.read(fs.readFileSync(full));
  assert.equal(decoded.width,128);
  assert.equal(decoded.height,128);
  assert.equal(heightAt(1.4,3.7,123),heightAt(1.4,3.7,123));
  assert.throws(()=>api.generateTerrain({projectId,resolution:123}));
});
test('import asset puis package ZIP avec manifest',async t=>{
  const {root,api,projectId}=setup(t);
  const src=path.join(root,'texture.png');
  fs.writeFileSync(src,PNG.sync.write(new PNG({width:2,height:2})));
  const [asset]=api.importAssets({projectId,paths:[src]});
  assert.match(asset.path,/Content\/Textures/);
  const preview=api.previewAsset({projectId,file:asset.path});
  assert.equal(preview.mime,'image/png');
  const pkg=await api.packageMod({projectId});
  assert.ok(fs.statSync(pkg.path).size>100);
  assert.ok(pkg.manifest.assets.some(f=>f.path==='Config/economy.json'));
  assert.ok(!pkg.manifest.assets.some(f=>f.path.startsWith('Dist/')));
  assert.ok(!pkg.manifest.assets.some(f=>f.path.includes('../')));
});
test('modification ne traverse pas les liens symboliques',t=>{
  const {root,api,projectId}=setup(t);
  const folder=path.join(api.getProjectPath(projectId),'Content','malicious');
  fs.symlinkSync(root,folder,'dir');
  assert.throws(()=>api.writeText({projectId,file:'Content/malicious/test.cpp',content:'hello'}));
});
