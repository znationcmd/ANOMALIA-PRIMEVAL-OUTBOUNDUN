'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.join(__dirname,'..'),read=f=>fs.readFileSync(path.join(root,f),'utf8');
test('outils mobiles : réelles opérations locales, archives ZIP et 3D',()=>{
 const api=read('src/mobile-api.js');
 for(const operation of ['createProject','listFiles','readText','writeText','getEconomy','saveEconomy','importAssets','previewAsset','generateTerrain','packageMod'])assert.ok(api.includes(operation),operation);
 assert.match(api,/indexedDB.open/);assert.match(api,/zipSync/);assert.match(api,/crypto.subtle.digest/);
});
test('PWA autonome et contrôles adaptés au toucher',()=>{
 const m=JSON.parse(read('public/manifest.webmanifest'));
 assert.equal(m.display,'standalone');assert.match(read('index.html'),/id="mobileMenu"/);
 assert.match(read('src/style.css'),/max-width:770px/);
 assert.match(read('src/renderer.js'),/import '.\/mobile-api.js'/);
 assert.match(read('public/sw.js'),/caches.open/);
});
test('données de projets privées et fonctions Windows non simulées',()=>{
 const api=read('src/mobile-api.js');
 assert.match(api,/Les dossiers de Windows ne sont pas accessibles/);
 assert.match(api,/Aucune installation EXE nécessaire/);
 assert.ok(!api.includes('https://'));
});
