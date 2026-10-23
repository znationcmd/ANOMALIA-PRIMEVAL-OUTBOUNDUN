import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
const root=path.resolve(import.meta.dirname,'..');
const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
const layout=fs.readFileSync(path.join(root,'src','workspace-layout.js'),'utf8');
const css=fs.readFileSync(path.join(root,'src','style.css'),'utf8');
const main=fs.readFileSync(path.join(root,'src','main.js'),'utf8');
test('nouvel espace professionnel conserve tous les identifiants des commandes 3D',()=>{
 for(const id of ['viewport','catalog','hierarchy','inspector','saveScene','exportScene','importModel','fileModel','fileOpen','snap','snapSize','moveTool','rotateTool','scaleTool','brushTool','selectTool','undo','redo','delete','duplicate','focusObject']){
  assert.ok(html.includes('id="'+id+'"'),id);
 }
});
test('barre d activite et panneaux redimensionnables restent accessibles au clavier',()=>{
 for(const id of ['toggleLibrary','toggleInspector','toggleFocus','ribbonFocus','resetLayout','librarySplitter','inspectorSplitter']){
  assert.ok(html.includes('id="'+id+'"'),id);
 }
 assert.match(html,/role="separator"/);
 assert.match(html,/aria-orientation="vertical"/);
 assert.match(layout,/ArrowLeft/);
 assert.match(layout,/ArrowRight/);
 assert.match(layout,/setPointerCapture/);
 assert.match(layout,/aria-expanded/);
});
test('preferences visuelles locales sans transfert ni modification des scenes',()=>{
 assert.match(layout,/localStorage/);
 assert.doesNotMatch(layout,/fetch\s*\(|indexedDB|XMLHttpRequest|https?:\/\//);
 assert.match(layout,/focus:false/);
 assert.match(main,/import '\.\/workspace-layout\.js'/);
 assert.match(css,/\.workspace\.hide-left\.hide-right/);
 assert.match(css,/\.activityRail/);
});
test('la nouvelle presentation ne supprime pas le mode prive ni le panneau updates',()=>{
 assert.match(html,/ESPACE PERSONNEL PROTÉGÉ/);
 assert.match(html,/id="updaterPanel"/);
 assert.match(html,/id="noSelection"/);
});
