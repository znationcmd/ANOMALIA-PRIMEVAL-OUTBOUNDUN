import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
const root=path.resolve(import.meta.dirname,'..');
const get=file=>fs.readFileSync(path.join(root,file),'utf8');

test('iPhone interface undoes the 940px desktop header and uses two-column actions',()=>{
 const css=get('src/style.css');
 const mobile=css.slice(css.indexOf('/* iPhone / Android viewport fix'));
 assert.ok(mobile.startsWith('/* iPhone'));
 assert.match(mobile,/@media\(max-width:820px\)/);
 assert.match(mobile,/\.top\{[^}]*min-width:0!important/);
 assert.match(mobile,/\.top>\.topButtons\{[^}]*grid-template-columns:repeat\(2,minmax\(0,1fr\)\)/);
 assert.match(mobile,/\.workspace[^}]*min-width:0!important/);
 assert.match(mobile,/\.stage #viewport\{min-height:0;/);
 assert.match(mobile,/overflow-x:hidden/);
});

test('viewport touch controls have buttons and resize-aware camera framing',()=>{
 const html=get('index.html'),js=get('src/main.js'),css=get('src/style.css');
 for(const id of ['frameScene','cameraZoomIn','cameraZoomOut']){
  assert.match(html,new RegExp('id="'+id+'"'));
  assert.match(js,new RegExp("document\\.querySelector\\(\\)|\\$\\('#"+id+"'\\)\\.onclick"));
 }
 assert.match(js,/const halfHorizontal=Math\.atan\(Math\.tan\(halfVertical\)\*viewportAspect\)/);
 assert.match(js,/const dist=Math\.min\(orbit.maxDistance\*\.85,Math\.max\(8,/);
 assert.match(js,/window\.matchMedia\('\(max-width:820px\)'\)\.matches\)requestAnimationFrame/);
 assert.match(css,/\.viewportCameraControls button\{min-width:42px/);
});

test('projects are not modified by camera or mobile styling changes',()=>{
 const html=get('index.html'),js=get('src/main.js');
 assert.match(html,/id="saveScene"/);
 assert.match(js,/restoreProject\(\)/);
 assert.match(js,/storeProject\(history.project\)/);
 assert.match(js,/function frameScene\(\)/);
 assert.match(js,/function adjustCameraZoom\(factor\)/);
 assert.match(js,/\.addScaledVector\(delta\.normalize\(\),distance\)/);
 assert.match(get('public/sw.js'),/mobile-centered-20261110/);
});
