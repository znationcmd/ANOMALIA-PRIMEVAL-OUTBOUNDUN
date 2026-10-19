import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,mkdirSync,writeFileSync,readFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {loadServerSettings} from '../server/server-settings.mjs';
import {serverDirectory} from '../server/server-storage.mjs';
import {CONFIG_GROUPS,CONFIG_FILES,validateConfigCatalog} from '../src/config-catalog.js';
test('config catalog contains unique filenames and legacy aliases',()=>{
 assert.equal(validateConfigCatalog(),true);
 assert.equal(new Set(CONFIG_FILES).size,CONFIG_FILES.length);
 assert.equal(CONFIG_GROUPS.server.primary,'config.json');
 assert.ok(CONFIG_FILES.includes('vehicles.xml'));
 assert.ok(CONFIG_FILES.includes('cfgplayerspawnpoints.xml'));
});
test('server-specific settings are loaded independently, environment overrides work',()=>{
 const root=mkdtempSync(join(tmpdir(),'anomalia-config-'));
 try{
  for(const [id,name,mode] of [['one','Serveur Un','rp'],['two','Serveur Deux','pvp']]){
   const dir=serverDirectory(root,id);mkdirSync(dir,{recursive:true});
   writeFileSync(join(dir,'config.json'),JSON.stringify({schemaVersion:1,server:{name,port:2303,maxPlayers:8,mode,timeMultiplier:2}}));
  }
  const one=loadServerSettings({dataRoot:root,serverId:'one',env:{}});
  const two=loadServerSettings({dataRoot:root,serverId:'two',env:{}});
  assert.equal(one.name,'Serveur Un');assert.equal(two.name,'Serveur Deux');
  assert.equal(one.mode,'rp');assert.equal(two.mode,'pvp');
  assert.equal(loadServerSettings({dataRoot:root,serverId:'one',env:{MAX_PLAYERS:'24',GAME_MODE:'mixed'}}).maxPlayers,24);
  assert.equal(loadServerSettings({dataRoot:root,serverId:'one',env:{GAME_MODE:'mixed'}}).mode,'mixed');
  assert.match(readFileSync(join(serverDirectory(root,'two'),'config.json'),'utf8'),/Serveur Deux/);
 }finally{rmSync(root,{recursive:true,force:true})}
});
test('malformed server JSON is rejected, not silently overwritten',()=>{
 const root=mkdtempSync(join(tmpdir(),'anomalia-config-invalid-'));
 try{const dir=serverDirectory(root,'test');mkdirSync(dir,{recursive:true});writeFileSync(join(dir,'config.json'),'{bad');assert.throws(()=>loadServerSettings({dataRoot:root,serverId:'test',env:{}}));}
 finally{rmSync(root,{recursive:true,force:true})}
});
