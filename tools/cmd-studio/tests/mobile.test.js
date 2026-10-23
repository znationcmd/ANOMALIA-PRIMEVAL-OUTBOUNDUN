'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const r=path.join(__dirname,'..'),read=f=>fs.readFileSync(path.join(r,f),'utf8');
test('CMD Studio mobile : vrais modèles enregistrés localement et interface préservée',()=>{
 const ui=read('ui/index.html'),api=read('ui/mobile-api.js'),css=read('ui/style.css');
 for(const id of ['assets','projects','searchResults','modelViewport','mobileMenu','studioSidebar','mobileOverlay'])assert.match(ui,new RegExp('id="'+id+'"'));
 assert.match(api,/indexedDB.open/);assert.match(api,/previewAsset:/);
 assert.match(api,/import:async payload/);assert.match(api,/addProject:async/);
 assert.match(css,/max-width:760px/);
});
test('application iOS Android installable en PWA avec mécanisme hors ligne',()=>{
 const m=JSON.parse(read('ui/manifest.webmanifest'));
 assert.equal(m.display,'standalone');assert.ok(m.icons.length);
 assert.match(read('ui/sw.js'),/caches.open/);
 assert.match(read('scripts/build-mobile.cjs'),/mobile-dist/);
});
test('moteurs natifs clairement exclus du navigateur mobile',()=>{
 const api=read('ui/mobile-api.js');
 assert.match(api,/Conversion Blender réservée au PC/);
 assert.match(api,/Unreal Engine réservée au PC/);
 assert.ok(!api.includes('eval('));
});
