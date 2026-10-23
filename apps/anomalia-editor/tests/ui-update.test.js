import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
const dir=path.resolve(import.meta.dirname,'..');
const html=fs.readFileSync(path.join(dir,'index.html'),'utf8');
const css=fs.readFileSync(path.join(dir,'src','style.css'),'utf8');
const source=fs.readFileSync(path.join(dir,'src','main.js'),'utf8');
const updater=fs.readFileSync(path.join(dir,'desktop','updates.cjs'),'utf8');
const main=fs.readFileSync(path.join(dir,'desktop','main.cjs'),'utf8');
test('le nouvel habillage conserve tous les boutons connectes aux outils 3D',()=>{
  for(const id of ['viewport','catalog','hierarchy','inspector','undo','redo','moveTool','rotateTool',
    'scaleTool','brushTool','snap','assetSearch','importModel','saveScene','openScene','exportScene',
    'posFields','rotFields','scaleFields','focusObject','exportCSV','saveAs','fileModel','fileOpen']){
    assert.ok(html.includes('id="'+id+'"'),id+' manquant');
  }
  assert.ok(source.includes("import './style.css'"));
  assert.ok(css.includes('.canvas'));
  assert.ok(css.includes('.workspace'));
});
test('le panneau de mises a jour est present mais reste masque dans le navigateur web',()=>{
  for(const id of ['updaterPanel','checkForUpdates','installUpdate','updateState','updateProgress']){
    assert.ok(html.includes('id="'+id+'"'));
  }
  assert.match(html,/id="updaterPanel"[^>]+hidden/);
  assert.ok(fs.readFileSync(path.join(dir,'src','updates-ui.js'),'utf8').includes("window.anomaliaDesktop?.updates"));
});
test('mises a jour reservees au bon Windows et a la bonne release',()=>{
  assert.match(updater,/process\.platform!=='win32'/);
  assert.match(updater,/anomalia-editor-latest/);
  assert.match(updater,/autoInstallOnAppQuit=true/);
  assert.match(updater,/autoDownload=true/);
  assert.ok(!updater.includes('CMD Studio'));
  assert.match(main,/preload:path.join\(__dirname,'preload.cjs'\)/);
});
test('l application garde l isolation de securite Electron',()=>{
  assert.match(main,/sandbox:true/);
  assert.match(main,/contextIsolation:true/);
  assert.match(main,/nodeIntegration:false/);
  assert.match(main,/will-navigate/);
});
