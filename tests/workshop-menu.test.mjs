import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,mkdtempSync,mkdirSync,writeFileSync,symlinkSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const {listLocalWorkshop}=require('../desktop/workshop-library.cjs');
const read=p=>readFileSync(new URL(p,import.meta.url),'utf8');

test('Mods opens a real in-game Workshop page on Windows and browser',()=>{
 const menu=read('../src/start-menu.js'),ui=read('../src/workshop-ui.js');
 const html=read('../index.html'),css=read('../src/style.css');
 assert.match(menu,/import \{createWorkshopPanel\} from '\.\/workshop-ui\.js'/);
 assert.match(menu,/\$\('startWorkshopBtn'\)\.onclick=\(\)=>workshop\.open\(\)/);
 assert.match(ui,/page\.hidden=false/);
 assert.match(ui,/page\.hidden=true/);
 for(const id of ['inGameWorkshop','igwClose','igwGrid','igwCategories','igwSearch','igwOpenTools'])
  assert.ok(html.includes('id="'+id+'"'),id);
 assert.match(css,/#inGameWorkshop\[hidden\]/);
 assert.match(css,/workshop-landscape\.svg/);
 assert.doesNotMatch(menu,/startWorkshopBtn'\)\.onclick=async/);
});

test('native Workshop IPC only reads the existing Tools appData with a trusted sender',()=>{
 const desktop=read('../desktop/main.cjs'),preload=read('../desktop/preload.cjs');
 assert.match(desktop,/ipcMain\.handle\('anomalia:workshop:list'/);
 assert.match(desktop,/validSender\(event\)/);
 assert.match(desktop,/app\.getPath\('appData'\)/);
 assert.match(preload,/exposeInMainWorld\('anomaliaWorkshop'/);
 assert.match(preload,/ipcRenderer\.invoke\('anomalia:workshop:list'\)/);
});
test('real local mods are visible but never claimed as loaded in UE5',t=>{
 const appData=mkdtempSync(join(tmpdir(),'anomalia-workshop-'));
 t.after(()=>rmSync(appData,{recursive:true,force:true}));
 const base=join(appData,'ANOMALIA Tools','private-workspaces');
 const mod=join(base,'test-mod-123'),conf=join(mod,'Config');
 mkdirSync(conf,{recursive:true});mkdirSync(join(base,'_workshop'),{recursive:true});
 writeFileSync(join(mod,'anomalia.project.json'),JSON.stringify({schema:'anomalia-tools-project',name:'SUV premium'}));
 writeFileSync(join(conf,'workshop.json'),JSON.stringify({schema:'anomalia-workshop-entry',projectId:'test-mod-123',title:'SUV réaliste',category:'Véhicules',modVersion:'1.2.0',description:'Mod de test',updatedAt:'2026-10-24T12:00:00Z'}));
 writeFileSync(join(base,'_workshop','library.json'),JSON.stringify({subscriptions:['test-mod-123'],installed:{'test-mod-123':{enabled:true,version:'1.2.0'}}}));
 const result=listLocalWorkshop(appData);
 assert.equal(result.available,true);
 assert.equal(result.mods.length,1);
 assert.equal(result.mods[0].title,'SUV réaliste');
 assert.equal(result.mods[0].subscribed,true);
 assert.equal(result.mods[0].prepared,true);
 assert.equal(result.mods[0].loadedInGame,false);
 assert.doesNotMatch(JSON.stringify(result),/private-workspaces/);
});
test('no local mods still returns usable page, symbolic links are ignored',t=>{
 const appData=mkdtempSync(join(tmpdir(),'anomalia-workshop-empty-'));
 t.after(()=>rmSync(appData,{recursive:true,force:true}));
 assert.equal(listLocalWorkshop(appData).mods.length,0);
 if(process.platform==='win32')return;
 const base=join(appData,'ANOMALIA Tools','private-workspaces');
 mkdirSync(base,{recursive:true});symlinkSync(appData,join(base,'fake-mod-123'),'dir');
 assert.equal(listLocalWorkshop(appData).mods.length,0);
});

test('WorkForge is branded in real Windows game and keeps local favorites',()=>{
 const menu=read('../src/start-menu.js');
 const ui=read('../src/workshop-ui.js');
 const html=read('../index.html');
 const pkg=JSON.parse(read('../package.json'));
 assert.equal(pkg.version,'0.7.3');
 assert.match(menu,/WORKFORGE · Mods/);
 assert.match(html,/ANOMALIA <b>WORKFORGE<\/b>/);
 assert.match(html,/id="igwFavorites"/);
 assert.match(ui,/anomalia-workforge-favorites-v1/);
 assert.match(ui,/localStorage\.setItem/);
 assert.match(ui,/toggleFavorite\(mod\.id\)/);
 assert.doesNotMatch(ui,/loadedInGame:true/);
});
