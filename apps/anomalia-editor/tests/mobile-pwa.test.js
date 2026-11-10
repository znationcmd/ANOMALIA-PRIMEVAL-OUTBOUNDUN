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
 assert.match(read('src/main.js'),/startMobileAutoUpdates/);
 assert.match(read('src/mobile-auto-updates.js'),/serviceWorker.register/);
 assert.match(read('public/sw.js'),/caches.open/);
});
test('panneaux 3D accessibles au tactile et positionnement local sauvegardé',()=>{
 const style=read('src/style.css'),layout=read('src/workspace-layout.js');
 assert.match(style,/@media\(max-width:1024px\)/);
 assert.match(style,/touch-action:none/);
 assert.match(style,/mobilePanelBackdrop/);
 assert.match(layout,/isMobile\(\)/);
 assert.match(layout,/localStorage/);
 assert.match(read('index.html'),/id="mobilePanelClose"/);
});
test('éditeur natif Windows continue de garder les vrais outils',()=>{
 const source=read('src/main.js');
 for(const fn of ['addModel','createEditorMesh','validateProject','rebuild'])assert.ok(source.includes(fn));
 assert.match(read('src/mobile-auto-updates.js'),/window.anomaliaDesktop/);
});

test('mobile updates check published revision, persist local scenes and auto reload',()=>{
 const js=read('src/mobile-auto-updates.js'),vite=read('vite.config.js'),main=read('src/main.js');
 assert.match(js,/CURRENT_REVISION=__ANOMALIA_WEB_BUILD__/);
 assert.match(js,/release\.json/);
 assert.match(js,/cache:'no-store'/);
 assert.match(js,/saveBeforeReload\(\)/);
 assert.match(js,/window\.location\.reload\(\)/);
 assert.match(js,/visibilitychange/);
 assert.match(js,/navigator\.onLine/);
 assert.match(main,/await startupPromise;await storeProject\(history\.project\)/);
 assert.match(vite,/writeFileSync\(path\.join\(appRoot,'public','release\.json'\)/);
 assert.match(vite,/define:\{__ANOMALIA_WEB_BUILD__/);
 assert.match(read('public/sw.js'),/self\.skipWaiting/);
});
