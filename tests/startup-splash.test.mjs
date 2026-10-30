import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
const read = p => readFileSync(new URL('../'+p,import.meta.url),'utf8');
test('startup poster is separate from interactive main menu',()=>{
 const html=read('index.html'),css=read('src/style.css');
 assert.ok(html.indexOf('id="launchSplash"') >= 0);
 assert.ok(html.indexOf('id="launchSplash"') < html.indexOf('id="startScreen"'));
 assert.match(html, /prigimalia-startup-poster\.jpg/);
 assert.match(css,/\.prigimalia-launch-splash\{/);
 assert.match(css,/\.prigimalia-splash-done/);
 const mainMenuRule=css.match(/#startScreen\.start\{[^}]*\}/)?.[0]||'';
 assert.doesNotMatch(mainMenuRule,/prigimalia-startup-poster/);
});
test('startup art vanishes without requiring player interaction',()=>{
 const code=read('src/startup-splash.js');
 assert.match(code,/window\.addEventListener\('load', whenReady/);
 assert.match(code,/setTimeout\(close, MAX_DISPLAY_MS\)/);
 assert.match(code,/splash\.remove\(\)/);
 assert.doesNotMatch(code,/localStorage|sessionStorage|\.onclick/);
});
test('startup art is bundled via the existing module build',()=>{
 const html=read('index.html');
 assert.match(html,/<script type="module" src="\/src\/startup-splash\.js"><\/script>/);
});
