import {createMultiplayerServer} from '../server/server.mjs';
import {chromium} from 'playwright';
import {createServer} from 'node:http';
import {readFile,mkdir} from 'node:fs/promises';
import {resolve,extname} from 'node:path';
import assert from 'node:assert/strict';
const root=resolve('dist'),failures=[];
const server=createServer(async(req,res)=>{
 try{
  const name=new URL(req.url,'http://localhost').pathname;
  const file=resolve(root,'.'+(name==='/'?'/index.html':name));
  if(!file.startsWith(root+'/')){res.writeHead(403);res.end();return}
  res.setHeader('Content-Type',({'.js':'text/javascript','.css':'text/css','.html':'text/html'})[extname(file)]||'application/octet-stream');
  res.end(await readFile(file));
 }catch{res.writeHead(404);res.end()}
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
await mkdir('test-results',{recursive:true});
const multiplayerServer=createMultiplayerServer({port:0,host:'127.0.0.1',password:'browser-test'});
await new Promise(r=>multiplayerServer.server.listening?r():multiplayerServer.server.once('listening',r));
let browser;
try{
 browser=await chromium.launch({headless:true,args:['--no-sandbox','--enable-unsafe-swiftshader','--use-angle=swiftshader']});
 const page=await browser.newPage({viewport:{width:1440,height:900}});
 page.on('pageerror',e=>failures.push(e.message));
 page.on('console',m=>{if(m.type()==='error'&&!m.text().includes('favicon'))failures.push(m.text())});
 const base=`http://127.0.0.1:${server.address().port}/?smoke=1`;
 await page.goto(base);
 await page.waitForSelector('#startBtn');
 await page.screenshot({path:'test-results/00-main-menu.png'});
 await page.click('#settingsBtn');
 for(const [language,label] of [['de','Solo spielen'],['ru','Одиночная игра'],['it','Gioca da solo'],['en','Play solo'],['ja','ソロプレイ'],['zh','单人游戏'],['es','Jugar solo'],['fr','Jouer en solo']]){await page.selectOption('#menuLanguage',language);assert.equal(await page.locator('#startBtn').textContent(),label);}
 await page.locator('#menuSettings .menu-back').click();
 await page.click('#multiBtn');
 await page.fill('#survivorName','Alice');await page.fill('#serverAddress',`ws://127.0.0.1:${multiplayerServer.server.address().port}`);await page.fill('#serverPassword','browser-test');await page.locator('#joinBtn').evaluate(button=>button.click());
 await page.waitForFunction(()=>window.__ANOMALIA_DIAGNOSTICS?.network.connected);
 const second=await browser.newPage({viewport:{width:960,height:720}});second.on('pageerror',e=>failures.push(e.message));await second.goto(base);await second.click('#multiBtn');await second.fill('#survivorName','Bob');await second.fill('#serverAddress',`ws://127.0.0.1:${multiplayerServer.server.address().port}`);await second.fill('#serverPassword','browser-test');await second.locator('#joinBtn').evaluate(button=>button.click());
 await page.waitForFunction(()=>window.__ANOMALIA_DIAGNOSTICS.network.players===2);await second.waitForFunction(()=>window.__ANOMALIA_DIAGNOSTICS.network.players===2);
 await page.screenshot({path:'test-results/00-multiplayer.png'});await second.close();await page.waitForFunction(()=>window.__ANOMALIA_DIAGNOSTICS.network.players===1);await page.evaluate(()=>document.exitPointerLock?.());await page.click('#menuBtn');await page.click('#startBtn');
 await page.waitForFunction(()=>window.__ANOMALIA_DIAGNOSTICS?.started&&window.__ANOMALIA_DIAGNOSTICS?.triangles>1000);
 await page.waitForTimeout(1800);
 await page.evaluate(()=>document.exitPointerLock?.());
 await page.screenshot({path:'test-results/01-city.png'});
 await page.keyboard.press('F4');await page.fill('#editorCode','ANOMALIA-EDITOR-2026');await page.click('#editorUnlock');
 await page.setInputFiles('#editorImport',{name:'test-map.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify({schemaVersion:1,objects:[{id:'test-house',type:'house',x:1000,z:180,yaw:0}]}))});
 await page.waitForFunction(()=>document.querySelectorAll('#editorObject option').length===2);await page.selectOption('#editorObject','0');await page.fill('#editorYaw','90');await page.click('#editorApply');await page.click('#editorDuplicate');assert.equal(await page.locator('#editorObject option').count(),3);await page.click('#editorUndo');assert.equal(await page.locator('#editorObject option').count(),2);await page.click('#editorRedo');assert.equal(await page.locator('#editorObject option').count(),3);
 await page.screenshot({path:'test-results/00-map-editor.png'});await page.click('#editorExit');

 const before=await page.evaluate(()=>window.__ANOMALIA_DIAGNOSTICS.position);
 await page.keyboard.down('KeyW');await page.waitForTimeout(1000);await page.keyboard.up('KeyW');
 const after=await page.evaluate(()=>window.__ANOMALIA_DIAGNOSTICS.position);
 assert.ok(after.z<before.z,'forward must move towards the camera view');
 await page.keyboard.press('KeyE');
 await page.keyboard.press('KeyI');await page.waitForSelector('.survival-inventory');await page.waitForTimeout(800);
 await page.screenshot({path:'test-results/02-inventory.png'});
 await page.locator('.cargo-item').filter({hasText:'Bois'}).first().click();
 await page.locator('#inventoryAmount').fill('2');await page.locator('[data-action="split"]').click();
 assert.equal(await page.locator('.cargo-item').filter({hasText:'Bois'}).count(),2,'split creates a second wood stack');
 await page.locator('[data-action="merge"]').click();
 assert.equal(await page.locator('.cargo-item').filter({hasText:'Bois'}).count(),1,'merge restores wood stack');
 await page.locator('.cargo-item').filter({hasText:'Bois'}).first().click();
 await page.locator('[data-action="transfer"]').click();
 assert.equal(await page.locator('.ground-grid .cargo-item').filter({hasText:'Bois'}).count(),1,'drop appears in vicinity');
 await page.locator('.ground-grid .cargo-item').filter({hasText:'Bois'}).first().click();
 await page.locator('[data-action="transfer"]').click();
 assert.equal(await page.locator('.ground-grid .cargo-item').filter({hasText:'Bois'}).count(),0,'pickup removes ground pile');
 await page.locator('#inventorySearch').fill('eau');
 assert.equal(await page.locator('.cargo-item').count(),1,'search filters cargo');
 await page.locator('#inventorySearch').fill('');
 await page.locator('[data-tab="craft"]').click();await page.waitForSelector('.recipe-card');
 await page.screenshot({path:'test-results/05-crafting.png'});
 await page.locator('[data-tab="inventory"]').click();
 await page.locator('#panelClose').click();
 await page.keyboard.press('KeyM');await page.waitForSelector('#panel:not(.hidden)');await page.screenshot({path:'test-results/03-map.png'});
 await page.locator('#panelClose').click();
 await page.waitForTimeout(200);await page.reload();
 assert.ok(await page.evaluate(()=>!!localStorage.getItem('anomalia-primeval-outboundun-save-v1')),'progress saved on pagehide');
 await page.click('#startBtn');await page.waitForTimeout(1000);
 await page.evaluate(()=>document.exitPointerLock?.());
 await page.screenshot({path:'test-results/04-reloaded.png'});
 await page.keyboard.press('F2');await page.waitForSelector('.admin-tabs');
 await page.locator('[data-admin-tab="player"]').click();await page.locator('[data-admin-action="god"]').click();
 await page.locator('[data-admin-tab="creatures"]').click();await page.locator('[data-admin-pet="dog"]').click();
 await page.locator('[data-admin-tab="vehicles"]').click();await page.locator('[data-vehicle="car"]').click();
 assert.ok(await page.locator('[data-goto-vehicle]').count()>=2,'admin spawn adds a car alongside the beach vehicle');
 await page.locator('[data-goto-vehicle]').last().click();await page.screenshot({path:'test-results/06-admin.png'});
 await page.locator('#panelClose').click();await page.keyboard.press('KeyE');
 await page.waitForFunction(()=>!!window.__ANOMALIA_DIAGNOSTICS?.world?.activeVehicle);
 const carBefore=await page.evaluate(()=>window.__ANOMALIA_DIAGNOSTICS.position);
 await page.keyboard.down('KeyW');try{await page.waitForFunction(p=>Math.hypot(window.__ANOMALIA_DIAGNOSTICS.position.x-p.x,window.__ANOMALIA_DIAGNOSTICS.position.z-p.z)>.3,carBefore,{timeout:30000})}finally{await page.keyboard.up('KeyW')}
 const carAfter=await page.evaluate(()=>window.__ANOMALIA_DIAGNOSTICS.position);
 assert.ok(Math.hypot(carAfter.x-carBefore.x,carAfter.z-carBefore.z)>.1,'vehicle responds to throttle');
 await page.keyboard.press('F5');await page.waitForTimeout(200);assert.equal(await page.evaluate(()=>window.__ANOMALIA_DIAGNOSTICS.world.vehicleView),'inside');
 await page.screenshot({path:'test-results/07-cockpit.png'});
 await page.keyboard.press('KeyE');await page.keyboard.press('F2');await page.locator('[data-admin-tab="player"]').click();await page.locator('[data-admin-action="bank"]').click();
 await page.locator('#panelClose').click();await page.keyboard.press('KeyE');await page.waitForSelector('#bankAmount');
 await page.locator('[data-bank="deposit"]').click();await page.waitForTimeout(100);assert.equal(await page.evaluate(()=>window.__ANOMALIA_DIAGNOSTICS.world.bank),100);
 await page.screenshot({path:'test-results/08-bank.png'});await page.locator('#panelClose').click();
 await page.keyboard.press('F3');await page.waitForSelector('[data-pet="follow"]');await page.screenshot({path:'test-results/09-companion.png'});await page.locator('#panelClose').click();
 assert.ok(await page.evaluate(()=>window.__ANOMALIA_DIAGNOSTICS.world.events>=1),'XML crash events are running');
 await page.keyboard.press('KeyB');await page.waitForSelector('#buildType');await page.selectOption('#buildType','foundation');await page.selectOption('#buildMaterial','wood');await page.locator('#harvestBuild').click();await page.locator('#beginBuild').click();await page.keyboard.press('KeyE');await page.waitForFunction(()=>window.__ANOMALIA_DIAGNOSTICS.construction.count>=1);await page.keyboard.press('Escape');
 assert.ok(await page.evaluate(()=>JSON.parse(localStorage.getItem('anomalia-primeval-outboundun-save-v1')).construction.length>=1),'placed modular foundation is saved');
 await page.screenshot({path:'test-results/10-construction.png'});

 assert.deepEqual(failures,[],'no page errors or shader compilation errors');
 console.log('Actual WebGL render, forward movement, inventory split/merge/drop/pickup/search/crafting, map, save and reload passed.');
}finally{await browser?.close();await multiplayerServer.close();server.closeAllConnections();await new Promise(r=>server.close(r))}
