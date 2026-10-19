import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,readFileSync,existsSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {appendServerLog} from '../server/server-logs.mjs';
import {serverDirectory} from '../server/server-storage.mjs';
test('each server keeps separate logs and secrets are redacted',()=>{
 const root=mkdtempSync(join(tmpdir(),'anomalia-logs-'));
 try{
  appendServerLog({dataRoot:root,serverId:'alpha',event:'joined',details:{name:'Alice',password:'do-not-log',adminKey:'also-secret'}});
  appendServerLog({dataRoot:root,serverId:'beta',file:'console.log',event:'command',details:{command:'set-mode',token:'private'}});
  const alpha=readFileSync(join(serverDirectory(root,'alpha'),'Server.log'),'utf8');
  const beta=readFileSync(join(serverDirectory(root,'beta'),'console.log'),'utf8');
  assert.match(alpha,/Alice/);assert.doesNotMatch(alpha,/do-not-log|also-secret|password|adminKey/);
  assert.match(beta,/set-mode/);assert.doesNotMatch(beta,/private|token/);
  assert.equal(existsSync(join(serverDirectory(root,'alpha'),'console.log')),false);
  assert.throws(()=>appendServerLog({dataRoot:root,serverId:'alpha',file:'../../hack',event:'bad'}));
 }finally{rmSync(root,{recursive:true,force:true})}
});
