import test from 'node:test';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {createHash} from 'node:crypto';
import {EventEmitter} from 'node:events';
const {createNativeGameLauncher}=createRequire(import.meta.url)('../desktop/native-game.cjs');
const bytes=Buffer.from('verified standalone binary');
const world='/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1';
const root=String.raw`D:\ANOMALIAZ\Jeu\Versions\SKARVIK-123\Windows`;
const valid={state:'AUTHENTIC_GAMEPLAY_VERIFIED',standalonePackagedExe:true,map:world,packageRoot:root,exe:root+'\\AnomaliaPrimeval.exe',sha256:createHash('sha256').update(bytes).digest('hex')};
function harness(record=valid){
 const calls=[];
 const launch=createNativeGameLauncher({readFileSync:(name)=>name.endsWith('.json')?JSON.stringify(record):bytes,existsSync:()=>true,spawn:(...args)=>{calls.push(args);const child=new EventEmitter();child.pid=42;child.exitCode=null;child.unref=()=>{};queueMicrotask(()=>child.emit('spawn'));return child;}});
 return {launch,calls};
}
test('launches verified standalone SKARVIK, once, without editor or shell',async()=>{
 const h=harness();assert.equal((await h.launch()).launched,true);
 assert.equal((await h.launch()).alreadyRunning,true);assert.equal(h.calls.length,1);
 assert.equal(h.calls[0][0],valid.exe);assert.deepEqual(h.calls[0][1],[world,'-d3d11','-sm5']);assert.equal(h.calls[0][2].shell,false);
});
for(const [name,patch] of [['unverified',{state:'FAILED'}],['editor executable',{exe:root+'\\UnrealEditor.exe'}],['different map',{map:'/Game/Maps/ANOMALIA_Playable_v1'}],['changed binary',{sha256:'0'.repeat(64)}],['external directory',{packageRoot:'C:\\Other',exe:'C:\\Other\\AnomaliaPrimeval.exe'}]]){
 test(`refuses ${name} before starting a process`,async()=>{const h=harness({...valid,...patch});await assert.rejects(h.launch());assert.equal(h.calls.length,0);});
}
test('missing installation reports failure without fallback',async()=>{const launch=createNativeGameLauncher({readFileSync:()=>{throw Error('missing');},spawn:()=>{assert.fail('must not spawn');}});await assert.rejects(launch(),/pas encore installé/);});
