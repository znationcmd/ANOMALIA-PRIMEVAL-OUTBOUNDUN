import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,readdirSync} from 'node:fs';
import {join} from 'node:path';

const root=new URL('../',import.meta.url);
const read=(p)=>readFileSync(new URL(p,root),'utf8');
const title='ANOMALIA’Z PRIGIMALIA';

test('every GitHub Actions workflow displays the official public title',()=>{
  const dir=new URL('.github/workflows/',root);
  const files=readdirSync(dir).filter(name=>/\.ya?ml$/.test(name));
  assert.ok(files.length>=60,'expected the full workflow catalog');
  for(const file of files){
    const first=read('.github/workflows/'+file).split(/\r?\n/,1)[0];
    assert.ok(first.startsWith('name: '+title),file+': wrong workflow display name');
  }
});

test('Windows script names use new public brand with legacy shortcut fallback',()=>{
  const ue=read('scripts/ue5/install-pc-editor-update.ps1');
  const playable=read('scripts/ue5/install-playable-windows.ps1');
  const smoke=read('scripts/ue5/smoke-installed-launchers.ps1');
  const ci=read('.github/workflows/ue5-installed-launcher-smoke.yml');
  assert.ok(ue.includes(title+' - Unreal.lnk'));
  assert.ok(playable.includes(title+' - Jouer.lnk'));
  assert.ok(smoke.includes('function Resolve-BrandShortcut'));
  assert.ok(ci.includes('function Resolve-BrandShortcut'));
  assert.ok(smoke.includes("'ANOMALIA - Jouer.lnk'"),'legacy installed builds remain testable');
  assert.ok(ci.includes("'ANOMALIA - Jouer.lnk'"),'legacy GitHub runners remain testable');
});

test('historic Unreal, Windows and save identifiers remain valid',()=>{
  const unreal=read('unreal/AnomaliaPrimeval.uproject');
  const desktop=read('desktop/main.cjs');
  const pkg=JSON.parse(read('package.json'));
  assert.ok(unreal.includes('"Name": "AnomaliaPrimeval"'));
  assert.equal(pkg.build.productName,title);
  assert.equal(pkg.build.appId,'com.cmd.anomalia.primevaloutboundun');
  assert.ok(desktop.includes('const SCHEME="anomalia"'));
});
