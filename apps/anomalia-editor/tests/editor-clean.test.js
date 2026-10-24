import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {join} from 'node:path';
const root=new URL('..',import.meta.url);
const read=name=>readFileSync(new URL(name,root),'utf8');
const html=read('index.html');
const main=read('src/main.js');
const css=read('src/editor-clean.css');
const layout=read('src/workspace-layout.js');
const menus=read('src/worldforge-ui.js');
const launcher=read('src/map-launcher.js');

test('le menu principal reste compact, fonctionnel et conserve les commandes',()=>{
  for(const id of ['menuFile','menuEdit','menuView','menuAssets','openMapLibrary','saveScene',
    'newScene','openScene','exportScene','importModel','importGamePack','chooseHeightmap']){
    assert.match(html,new RegExp('id="'+id+'"'));
  }
  assert.match(css,/\.app \.top\{height:44px!important/);
  assert.match(css,/\.app \.topButtons #newScene,[\s\S]*#exportScene\{display:none!important/);
  assert.match(menus,/\['Enregistrer sous…'/);
  assert.match(menus,/\['Importer un modèle GLB'/);
  assert.match(menus,/\['Choisir une carte'/);
});
test('terrain, sources et cartes UE5 accessibles mais repliés au lancement',()=>{
  assert.match(html,/<details class="advancedDisclosure" id="unrealMapsDisclosure">/);
  assert.match(html,/<details class="advancedDisclosure libraryAdvanced" id="librarySourceSettings">/);
  assert.match(html,/id="quickImportGLB"/);
  assert.match(html,/id="quickLibrarySettings"/);
  assert.match(html,/id="worldSourceBar"/);
  assert.match(css,/#worldSourceBar:not\(\.expanded\)\{display:none!important/);
  assert.match(css,/\.workspaceRibbon\{display:none!important/);
  assert.match(menus,/worldSourceBar/);
});
test('les vrais panneaux scene et objets s ouvrent par défaut',()=>{
  assert.match(layout,/library:true,inspector:true/);
  assert.match(layout,/anomalia-editor-clean-layout-v3/);
  assert.match(css,/grid-template-columns:39px/);
  assert.match(css,/\.viewportInfo.*\.viewportTips/);
});
test('le lanceur de cartes est le premier écran sans fausse carte Unreal intégrée',()=>{
  assert.match(main,/mapLauncher\.show\(\)/);
  assert.match(main,/createMapLauncher\(/);
  assert.match(launcher,/onOpenUnreal\(entry\.key\)/);
  assert.match(launcher,/onOpenLocal\(entry\.key\)/);
  assert.match(launcher,/aucune progression simulée/);
  assert.match(main,/import '\.\/editor-clean\.css'/);
});
test('aucun doublon identifiant HTML, hormis id en chaînes dans les attributs textes',()=>{
 const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(x=>x[1]);
 const seen=new Set();
 for(const id of ids){assert.ok(!seen.has(id),'identifiant dupliqué : '+id);seen.add(id);}
});
