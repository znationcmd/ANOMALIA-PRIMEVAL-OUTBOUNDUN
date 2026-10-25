import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
const root=path.resolve(import.meta.dirname,'..');
const read=x=>fs.readFileSync(path.join(root,x),'utf8');
const html=read('index.html');
const main=read('src/main.js');
const native=read('desktop/main.cjs');
const bridge=read('desktop/ue5-bridge.cjs');
const scanner=read('desktop/game-library.cjs');
const terrain=read('src/terrain-world.js');
const gameui=read('src/game-library-ui.js');
test('Le vrai projet Unreal et les cartes .umap se découvrent sans les interpréter comme GLB',()=>{
 assert.match(bridge,/\.uproject/);
 assert.match(bridge,/\.umap/);
 assert.match(bridge,/fs\.promises\.realpath/);
 assert.match(bridge,/shell\.openPath/);
 assert.match(bridge,/process\.platform!=='win32'/);
 assert.doesNotMatch(bridge,/exec\s*\(|cmd\.exe|powershell\.exe|shell:\s*true/);
 assert.match(native,/editor:unreal:status/);
 assert.match(native,/editor:unreal:link/);
 assert.match(native,/editor:unreal:open/);
 assert.match(read('desktop/preload.cjs'),/unreal:Object\.freeze/);
});
test('Terrain réel PNG/JPEG/WebP importé en géométrie Three.js avec échelles et raycasts',()=>{
 for(const id of ['chooseHeightmap','fileTerrain','resetTerrain','heightmapWidth','worldSourceLabel','viewportWorldMode']){
  assert.ok(html.includes('id="'+id+'"'),id);
 }
 assert.match(terrain,/getImageData/);
 assert.match(terrain,/PlaneGeometry\(width,width,segments,segments\)/);
 assert.match(terrain,/computeVertexNormals/);
 assert.match(terrain,/ground\.geometry=geometry/);
 assert.match(terrain,/ground\.geometry=originalGeometry/);
 assert.match(read('src/terrain-cache.js'),/indexedDB\.open/);
 assert.match(main,/await restoreTerrainForScene\(\)/);
});
test('Ressources DayZ-like : vrai terrain lié et actualisation automatique locale',()=>{
 assert.match(scanner,/kind==='heightmap'/);
 assert.match(scanner,/canTerrain:kind==='heightmap'/);
 assert.match(gameui,/activeTerrain=\{id:item\.id/);
 assert.match(gameui,/Le relief a été rechargé automatiquement/);
 assert.match(read('src/world-source-ui.js'),/setInterval/);
 assert.match(read('src/world-source-ui.js'),/60000/);
});
test('Mauvais cubes masqués par défaut sans effacer les cartes ni les modèles',()=>{
 assert.match(main,/let prototypesVisible=false/);
 assert.match(main,/prototypes géométriques masqués/);
 assert.match(main,/prototypesVisible\|\|item\.preset==='custom-glb'/);
 assert.match(main,/const genuine=history\.project\.objects/);
 assert.doesNotMatch(main,/history\.reset\(newProject\(\)\).*rmSync/);
 assert.match(main,/worldForge\.tick/);
 assert.match(read('src/world-real.css'),/\.realWorldDock/);
 assert.match(read('src/world-real.css'),/\.worldSourceBar/);
 for(const id of ['toggleLegacy','openWorldNow','realWorldDock','linkRealWorld','launchRealWorld','gameLibraryItems']){
   assert.ok(html.includes('id="'+id+'"'),id);
 }
});
test('Même projet Windows et mobile : pas d’appel API non autorisé pour parcourir les disques',()=>{
 assert.match(read('desktop/main.cjs'),/contextIsolation:true,nodeIntegration:false,sandbox:true/);
 assert.match(read('desktop/main.cjs'),/webSecurity:true/);
 assert.match(read('src/world-source-ui.js'),/window\.anomaliaDesktop\?\.unreal/);
 assert.match(read('src/main.js'),/serviceWorker.register/);
});
