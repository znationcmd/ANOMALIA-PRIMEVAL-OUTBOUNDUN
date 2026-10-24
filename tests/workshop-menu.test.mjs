import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const read=path=>readFileSync(new URL(path,import.meta.url),'utf8');
test('main game Mods button is connected to trusted local ANOMALIA Workshop protocol',()=>{
 const menu=read('../src/start-menu.js');
 const preload=read('../desktop/preload.cjs');
 const main=read('../desktop/main.cjs');
 assert.match(menu,/id="startWorkshopBtn"/);
 assert.match(menu,/anomaliaServer\.openWorkshop/);
 assert.match(menu,/Cette version du navigateur/);
 assert.match(preload,/openWorkshop:\(\)=>ipcRenderer\.invoke\('anomalia:open-workshop'\)/);
 assert.match(main,/ipcMain\.handle\('anomalia:open-workshop'/);
 assert.match(main,/shell\.openExternal\('anomalia-tools:\/\/workshop'\)/);
 assert.match(main,/validSender\(event\)/);
 assert.doesNotMatch(main,/shell\.openExternal\(.*address/);
});
