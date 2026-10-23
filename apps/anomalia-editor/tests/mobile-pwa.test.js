import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
const root=path.resolve(import.meta.dirname,'..');
const read=p=>fs.readFileSync(path.join(root,p),'utf8');
test('éditeur sur iPhone, iPad et Android : PWA installable',()=>{
 const manifest=JSON.parse(read('public/manifest.webmanifest'));
 assert.equal(manifest.display,'standalone');assert.equal(manifest.start_url,'./');
 assert.match(read('index.html'),/rel="manifest"/);
 assert.match(read('src/main.js'),/serviceWorker.register/);
 assert.match(read('public/sw.js'),/caches.open/);
});
test('panneaux 3D accessibles au tactile et positionnement local sauvegardé',()=>{
 const style=read('src/style.css'),layout=read('src/workspace-layout.js');
 assert.match(style,/@media\(max-width:820px\)/);
 assert.match(style,/touch-action:none/);
 assert.match(style,/mobilePanelBackdrop/);
 assert.match(layout,/isMobile\(\)/);
 assert.match(layout,/localStorage/);
 assert.match(read('index.html'),/id="mobilePanelClose"/);
});
test('éditeur natif Windows continue de garder les vrais outils',()=>{
 const source=read('src/main.js');
 for(const fn of ['addModel','createEditorMesh','saveProject','rebuild'])assert.ok(source.includes(fn));
 assert.match(source,/window.anomaliaDesktop/);
});
