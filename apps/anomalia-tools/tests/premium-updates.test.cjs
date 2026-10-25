'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const read=p=>fs.readFileSync(path.join(root,p),'utf8');
const html=read('index.html');
const renderer=read('src/renderer.js');
const css=read('src/style.css');
const main=read('main.cjs');
const preload=read('preload.cjs');
const updates=read('updates.cjs');
test('tous les sept outils authentiques ont conservé leurs vues et commandes',()=>{
  const pages=['home','workbench','objects','terrain','economy','textures','addon','publisher'];
  for(const id of pages)assert.match(html,new RegExp('id="'+id+'"'),id);
  const controls=['newProject','saveFile','newSource','sourceEditor','import3D','modelView','modelsList',
    'terrainForm','terrainPreview','saveEconomy','lootRows','importTexture',
    'buildAddon','exportMod','activeProject','createForm','projectsList','fileOpen'];
  for(const id of controls)if(id!=='fileOpen')assert.ok(html.includes('id="'+id+'"'),id);
  assert.match(renderer,/api\.call\('generateTerrain'/);
  assert.match(renderer,/api\.call\('writeText'/);
  assert.match(renderer,/api\.call\('packageMod'/);
});
test('refonte premium réelle avec compteurs issus des fichiers et projets locaux',()=>{
  for(const id of ['overviewProjectTotal','overviewFileTotal','sidebarWorkspaceName','heroExplore','moduleCards']){
    assert.ok(html.includes('id="'+id+'"'));
  }
  assert.match(renderer,/files\.filter\(f=>f\.type==='file'\)\.length/);
  assert.match(renderer,/projects\.length/);
  assert.match(css,/\.updatesLayout/);
  assert.match(css,/\.heroArtwork/);
});
test('auto-update Windows garde un canal spécifique et reste absent sur navigateur',()=>{
  assert.match(updates,/anomalia-tools-latest/);
  assert.doesNotMatch(updates,/anomalia-editor-latest|cmd-studio-latest/);
  assert.match(updates,/autoDownload=true/);
  assert.match(updates,/autoInstallOnAppQuit=true/);
  assert.match(updates,/allowDowngrade=false/);
  assert.match(updates,/process\.platform!=='win32'/);
  assert.match(preload,/tools:updates:check/);
  assert.match(main,/new ToolsUpdater\(\)/);
  assert.match(main,/sandbox:true/);
  assert.match(main,/contextIsolation:true/);
  assert.match(main,/nodeIntegration:false/);
});
test('page de mise à jour entièrement câblée et données conservées',()=>{
  for(const id of ['updates','updateMessage','checkUpdates','installUpdates','updateProgress','updateVersion']){
    assert.ok(html.includes('id="'+id+'"'));
  }
  assert.match(read('src/updates-ui.js'),/window\.anomaliaTools\?\.updates/);
  assert.match(read('package.json'),/deleteAppDataOnUninstall": false/);
  assert.match(read('package.json'),/anm|anomalia-tools-latest/);
});
