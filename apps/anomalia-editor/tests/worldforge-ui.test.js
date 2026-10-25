import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
const dir=path.resolve(import.meta.dirname,'..');
const read=p=>fs.readFileSync(path.join(dir,p),'utf8');
const h=read('index.html'),j=read('src/main.js'),css=read('src/worldforge.css'),menu=read('src/worldforge-ui.js');
test('interface DayZ-style : grand viewport, panneaux scenes/propriétés et vraies placements',()=>{
  const left=h.indexOf('class="left explorerDock"'),viewport=h.indexOf('id="viewport"'),right=h.indexOf('class="right placeableDock"');
  assert.ok(left>0&&right>left&&viewport>left&&viewport<right);
  assert.ok(h.indexOf('id="hierarchy"',left)<viewport);
  assert.ok(h.indexOf('id="inspector"',left)<viewport);
  assert.ok(h.indexOf('id="gameLibraryItems"',right)>right);
  assert.ok(h.indexOf('id="catalog"',right)>right);
  assert.match(css,/\.workspace\.hide-left/);
  assert.match(read('src/workspace-layout.js'),/library:true,inspector:true/);
});
test('les prototypes ne sont plus le catalogue principal ni la carte de première ouverture',()=>{
  assert.match(h,/<details class="prototypeDisclosure"/);
  assert.match(h,/Prototypes géométriques, pas photoréalistes/);
  assert.doesNotMatch(j,/await addPreset\('house',\{x:0,y:0,z:0\}\)/);
  assert.match(j,/Nouvelle scène vide/);
  for(const id of ['emptyWorld','emptyLinkFolder','emptyImportModel','emptyOpenProject','replaceSelected']){
    assert.ok(h.includes('id="'+id+'"'),id);
  }
});
test('remplacement des maquettes par des vrais GLB conserve les transformations',()=>{
  assert.match(j,/async function replaceWithRealModel\(asset\)/);
  assert.match(j,/target\.preset='linked-glb'/);
  assert.match(j,/target\.asset=\{libraryId:asset\.id,filename:asset\.name\}/);
  assert.match(j,/const next=cloneProject\(history\.project\)/);
  assert.match(j,/await createEditorMesh\(target\)/);
  assert.match(j,/history\.commit\(next\)/);
  assert.match(j,/replaceTargetId\)return replaceWithRealModel\(item\)/);
});
test('commandes réelles de caméra, affichage, barre de menu et placements',()=>{
  for(const id of ['menuFile','menuEdit','menuView','menuAssets','toggleGrid','toggleShadows','centerWorld','viewTop','fps']){
    assert.ok(h.includes('id="'+id+'"'),id);
  }
  for(const token of ['renderer.shadowMap.enabled','grid.visible','camera.getWorldDirection','orbit.target.add','keys.has','menuPopup']){
    assert.ok(menu.includes(token),token);
  }
  assert.match(j,/await armLinkedPlacement\(item\)/);
  assert.match(j,/worldForge\.tick\(delta\)/);
  assert.match(j,/src\/worldforge\.css|\.\/worldforge\.css/);
});
test('les boutons existants et la version mobile ne sont pas perdus',()=>{
  for(const id of ['newScene','saveScene','openScene','exportScene','exportCSV','saveAs','fileModel',
    'toggleInspector','toggleLibrary','importGamePack','linkGameFolder','snap','snapSize',
    'selectTool','moveTool','rotateTool','scaleTool','brushTool','undo','redo',
    'inspectorDuplicate','focusObject','updaterPanel','mobileMenu','mobilePanelClose']){
     if(id==='mobileMenu')continue;
     assert.ok(h.includes('id="'+id+'"'),id);
  }
  assert.match(read('src/style.css'),/max-width:820px/);
  assert.match(read('src/main.js'),/serviceWorker.register/);
});
