'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const {EventEmitter}=require('node:events');

const root=path.resolve(__dirname,'..');
function setup(beforeRestart){
  const source=fs.readFileSync(path.join(root,'desktop','updates.cjs'),'utf8');
  const engine=new EventEmitter();
  let installs=0;
  const timers=[];
  let feed=null;
  engine.setFeedURL=value=>{feed=value;};
  engine.quitAndInstall=()=>{installs++;};
  engine.checkForUpdates=async()=>({version:'0.5.6'});
  const electron={app:{getVersion:()=> '0.5.5',isPackaged:true},
    BrowserWindow:{getAllWindows:()=>[]}};
  const module={exports:{}};
  const ctx={module,exports:module.exports,process:{platform:'win32'},
    setTimeout(fn,delay){timers.push({fn,delay});return timers.length;},
    clearTimeout(){},setInterval(){return 1;},clearInterval(){},
    require(id){
      if(id==='electron')return electron;
      if(id==='electron-updater')return {autoUpdater:engine};
      throw Error('Unexpected dependency '+id);
    }};
  vm.runInNewContext(source,ctx,{filename:'updates.cjs'});
  const updater=new module.exports.EditorUpdates({prepareForRestart:beforeRestart});
  return {updater,engine,timers,feed,get installs(){return installs;}};
}
function tick(){return new Promise(resolve=>setImmediate(resolve));}

test('NSIS updater listens to the real editor-only published channel',()=>{
  const h=setup(async()=>true);
  assert.equal(h.feed.url,
    'https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/releases/download/anomalia-editor-latest/');
  assert.equal(h.engine.autoDownload,true);
  assert.equal(h.engine.autoInstallOnAppQuit,true);
});

test('a downloaded update automatically saves before replacing installed files',async()=>{
  const order=[];
  const h=setup(async()=>{order.push('saved');return true;});
  h.engine.emit('update-downloaded',{version:'0.5.6'});
  await tick();
  assert.deepEqual(order,['saved']);
  assert.equal(h.updater.getStatus().phase,'installation');
  assert.equal(h.installs,0);
  const timer=h.timers.find(x=>x.delay===1500);
  assert.ok(timer,'restart must occur only after successful save');
  timer.fn();
  assert.equal(h.installs,1);
});

test('failed or unconfirmed scene save never triggers forced restart',async()=>{
  const h=setup(async()=>false);
  h.engine.emit('update-downloaded',{version:'0.5.6'});
  await tick();
  assert.equal(h.installs,0);
  assert.equal(h.updater.getStatus().phase,'prete');
  assert.ok(!h.timers.some(x=>x.delay===1500));
  assert.match(h.updater.getStatus().message,/Carte non confirmée/);
});

test('without an authorized save handler, NSIS retains update for normal app quit',async()=>{
  const h=setup(undefined);
  h.engine.emit('update-downloaded',{version:'0.5.6'});
  await tick();
  assert.equal(h.installs,0);
  assert.equal(h.updater.getStatus().phase,'prete');
});

test('restart confirmation wiring is present from Electron to saved scene',()=>{
  const main=fs.readFileSync(path.join(root,'desktop','main.cjs'),'utf8');
  const preload=fs.readFileSync(path.join(root,'desktop','preload.cjs'),'utf8');
  const renderer=fs.readFileSync(path.join(root,'src','main.js'),'utf8');
  assert.match(main,/editor:updates:prepare-install/);
  assert.match(main,/event\.sender!==win\.webContents/);
  assert.match(main,/15000/);
  assert.match(preload,/onPrepareInstall/);
  assert.match(preload,/confirmSaved/);
  assert.match(renderer,/await storeProject\(history\.project\)/);
  assert.match(renderer,/updateBridge\.confirmSaved\(request\?\.id,saved\)/);
});
