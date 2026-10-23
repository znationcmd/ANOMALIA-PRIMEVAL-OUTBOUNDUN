'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
const js=fs.readFileSync(path.join(root,'src/updates-ui.js'),'utf8');
const pack=JSON.parse(fs.readFileSync(path.join(root,'package.json'),'utf8'));
test('sidebar, footer and updates page render actual installed version',()=>{
 for(const id of ['appSidebarVersion','appFooterVersion','updateVersion'])
   assert.ok(html.includes('id="'+id+'"'),id);
 assert.match(js,/appSidebarVersion/);
 assert.match(js,/appFooterVersion/);
 assert.match(js,/state\.currentVersion/);
 assert.doesNotMatch(html,/VERSION 0\.2\.0/);
 assert.doesNotMatch(html,/ANOMALIA TOOLS 0\.2 ·/);
});
test('versioned package and stable update metadata are configured',()=>{
 assert.equal(pack.version,'0.2.2');
 assert.equal(pack.build.appId,'fr.anomalia.tools');
 assert.match(pack.build.nsis.artifactName,/ANOMALIA-Tools-Setup/);
 assert.match(pack.build.publish[0].url,/anomalia-tools-latest/);
});
