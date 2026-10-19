import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,mkdirSync,writeFileSync,readFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
test('offline packager embeds JavaScript replacement tokens literally and removes external assets',()=>{
 const dir=mkdtempSync(join(tmpdir(),'anomalia-offline-'));
 try{
  mkdirSync(join(dir,'dist'));
  const js='console.log("WebGL", "$&", "$`", "$\'");';
  writeFileSync(join(dir,'dist','index.html'),'<script type="module" src="./game.js"></script><link rel="stylesheet" href="./game.css">');
  writeFileSync(join(dir,'dist','game.js'),js);
  writeFileSync(join(dir,'dist','game.css'),'body{color:red}');
  execFileSync(process.execPath,[fileURLToPath(new URL('../scripts/package-offline.mjs',import.meta.url))],{cwd:dir});
  const html=readFileSync(join(dir,'release','ANOMALIA_PRIMEVAL_OUTBOUNDUN.html'),'utf8');
  assert.ok(html.includes(js));assert.ok(!html.includes('src="'));assert.ok(html.includes('<style>body{color:red}</style>'));
 }finally{rmSync(dir,{recursive:true,force:true})}
});
