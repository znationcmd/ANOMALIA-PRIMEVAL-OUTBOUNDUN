import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const read = path => readFileSync(new URL('../'+path, import.meta.url),'utf8');
test('public game title appears in game and Unreal metadata',()=>{
 const title='ANOMALIA’Z PRIGIMALIA';
 assert.match(read('index.html'),/ANOMALIA’Z/);
 assert.ok(read('desktop/main.cjs').includes(title));
 assert.ok(read('server/server-settings.mjs').includes(title));
 assert.ok(read('unreal/AnomaliaPrimeval.uproject').includes(title));
 assert.ok(read('unreal/Config/DefaultGame.ini').includes(title));
 const p=JSON.parse(read('package.json'));
 assert.equal(p.name,'anomaliaz-prigimalia');
 assert.equal(p.build.productName,title);
 assert.match(p.build.nsis.artifactName,/ANOMALIAZ-PRIGIMALIA/);
});
test('existing runtime identifiers are stable for user-data compatibility',()=>{
 const p=JSON.parse(read('package.json'));
 assert.equal(p.build.appId,'com.cmd.anomalia.primevaloutboundun');
 assert.ok(read('unreal/AnomaliaPrimeval.uproject').includes('"Name": "AnomaliaPrimeval"'));
 assert.ok(read('src/main.js').includes('anomalia-primeval-outboundun-save-v1'));
});
