'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const {discoverInstalledProject}=require('../desktop/installed-project.cjs');
function fixture(){
 const temp=fs.mkdtempSync(path.join(os.tmpdir(),'anomalia-sync-'));
 const base=path.join(temp,'CMD','ANOMALIA-UE5');fs.mkdirSync(base,{recursive:true});
 fs.writeFileSync(path.join(base,'owner.json'),JSON.stringify({product:'ANOMALIA-UE5-EDITOR-v1'}));
 function activate(commit){
  const projectRoot=path.join(base,'versions',commit);fs.mkdirSync(path.join(projectRoot,'Content','Maps'),{recursive:true});
  const project=path.join(projectRoot,'AnomaliaPrimeval.uproject');
  fs.writeFileSync(project,JSON.stringify({Modules:[{Name:'AnomaliaPrimeval'}],EngineAssociation:'5.8'}));
  fs.writeFileSync(path.join(projectRoot,'Content','Maps','ANOMALIA_Inhabited_v2.umap'),'real-test-map-bytes');
  fs.writeFileSync(path.join(projectRoot,'house.glb'),Buffer.from('glTFsource-mesh-'+commit));
  const active={state:'VALIDATED_EDITOR_PROJECT_INSTALLED',commit,project,mapPackage:'/Game/Maps/ANOMALIA_Inhabited_v2',engineRoot:path.join(temp,'UE_5.8')};
  fs.writeFileSync(path.join(base,'active.json'),'\uFEFF'+JSON.stringify(active));
  return active;
 }
 return {temp,base,activate,cleanup:()=>fs.rmSync(temp,{recursive:true,force:true})};
}
test('Automatic discovery follows activation without changing old projects or user data',()=>{
 const f=fixture();try{
  const a=f.activate('a'.repeat(40));const first=discoverInstalledProject(f.temp);
  assert.equal(first.project,a.project);assert.equal(first.mapPackage,'/Game/Maps/ANOMALIA_Inhabited_v2');
  const saved=path.join(f.base,'userdata','Saved','Servers','solo','player.json');fs.mkdirSync(path.dirname(saved),{recursive:true});fs.writeFileSync(saved,'player-save');
  const b=f.activate('b'.repeat(40));assert.equal(discoverInstalledProject(f.temp).project,b.project);
  assert.ok(fs.existsSync(a.project));assert.equal(fs.readFileSync(saved,'utf8'),'player-save');
 }finally{f.cleanup();}
});
test('An unrelated installation or a project outside owned versions is refused',()=>{
 const f=fixture();try{
  const active=f.activate('a'.repeat(40));
  const external=path.join(f.temp,'AnomaliaPrimeval.uproject');fs.copyFileSync(active.project,external);
  fs.writeFileSync(path.join(f.base,'active.json'),JSON.stringify({...active,project:external}));
  assert.throws(()=>discoverInstalledProject(f.temp),/versions/);
  fs.writeFileSync(path.join(f.base,'owner.json'),JSON.stringify({product:'unrelated'}));
  assert.throws(()=>discoverInstalledProject(f.temp),/non reconnue/);
 }finally{f.cleanup();}
});
test('Missing active world is reported instead of showing an obsolete project',()=>{
 const f=fixture();try{
  const active=f.activate('c'.repeat(40));
  fs.unlinkSync(path.join(path.dirname(active.project),'Content','Maps','ANOMALIA_Inhabited_v2.umap'));
  assert.throws(()=>discoverInstalledProject(f.temp));
 }finally{f.cleanup();}
});
test('Library discovers installed GLBs and switches versions without a manual folder',async()=>{
 const {GameLibrary}=require('../desktop/game-library.cjs');
 const f=fixture(),prior=process.env.LOCALAPPDATA;process.env.LOCALAPPDATA=f.temp;
 try{
  f.activate('d'.repeat(40));const library=new GameLibrary(path.join(f.temp,'editor-userdata'));
  let status=await library.scan();assert.equal(status.automaticProject,true);assert.equal(status.installedCommit,'d'.repeat(40));
  const house=status.items.find(x=>x.name==='house.glb');assert.ok(house);assert.equal(house.rootTag,'native');
  assert.equal((await library.read(house.id)).kind,'glb');
  f.activate('e'.repeat(40));await assert.rejects(()=>library.read(house.id),/mis à jour/);
  status=await library.scan();assert.equal(status.changed,true);assert.equal(status.installedCommit,'e'.repeat(40));
  assert.equal(Buffer.from((await library.read(house.id)).data,'base64').toString(),'glTFsource-mesh-'+'e'.repeat(40));
 }finally{if(prior===undefined)delete process.env.LOCALAPPDATA;else process.env.LOCALAPPDATA=prior;f.cleanup();}
});
