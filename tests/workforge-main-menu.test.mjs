import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const menu=readFileSync(new URL('../src/start-menu.js',import.meta.url),'utf8');
const workforge=readFileSync(new URL('../src/workforge.js',import.meta.url),'utf8');
const desktop=readFileSync(new URL('../desktop/main.cjs',import.meta.url),'utf8');

test('WorkForge is mounted in main menu, never in gameplay HUD',()=>{
  assert.match(menu,/import\s+\{mountWorkForge\}\s+from\s+['"]\.\/workforge\.js['"]/);
  assert.match(menu,/id=\\?"workforgeBtn/);
  assert.match(menu,/\$\('workforgeBtn'\)\.onclick/);
  assert.doesNotMatch(menu,/workforgeHudBtn/);
  assert.doesNotMatch(menu,/hud\.append\(.*workforge/);
});

test('WorkForge JOUER starts the real local game',()=>{
  assert.match(menu,/onPlay:\(\)=>\{screen\.querySelector\('#startBtn'\)\?\.click\(\);\}/);
});

test('WorkForge uses installed mapping mods, not fictional remote catalog',()=>{
  assert.match(workforge,/const KEY = "anomalia-workshop-map-mods-v1"/);
  assert.match(workforge,/localStorage\.getItem\(KEY\)/);
  assert.match(workforge,/localStorage\.setItem\(KEY/);
  assert.match(workforge,/Non configurée/);
  assert.match(workforge,/Non disponibles/);
  assert.match(workforge,/data-wf-nav/);
});

test('Electron installed app loads same bundled game UI',()=>{
  assert.match(desktop,/loadURL\("anomalia:\/\/game\/index\.html"\)/);
});
