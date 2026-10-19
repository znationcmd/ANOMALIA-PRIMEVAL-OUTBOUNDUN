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
let browser;
try{
 browser=await chromium.launch({headless:true,args:['--no-sandbox','--enable-unsafe-swiftshader','--use-angle=swiftshader']});
 const page=await browser.newPage({viewport:{width:1440,height:900}});
 page.on('pageerror',e=>failures.push(e.message));
 page.on('console',m=>{if(m.type()==='error'&&!m.text().includes('favicon'))failures.push(m.text())});
 const base=`http://127.0.0.1:${server.address().port}/?smoke=1`;
 await page.goto(base);await page.click('#startBtn');
 await page.waitForFunction(()=>window.__ANOMALIA_DIAGNOSTICS?.started&&window.__ANOMALIA_DIAGNOSTICS?.triangles>1000);
 await page.waitForTimeout(1800);
 await page.evaluate(()=>document.exitPointerLock?.());
 await page.screenshot({path:'test-results/01-city.png'});
 const before=await page.evaluate(()=>window.__ANOMALIA_DIAGNOSTICS.position);
 await page.keyboard.down('KeyW');await page.waitForTimeout(1000);await page.keyboard.up('KeyW');
 const after=await page.evaluate(()=>window.__ANOMALIA_DIAGNOSTICS.position);
 assert.ok(after.z<before.z,'forward must move towards the camera view');
 await page.keyboard.press('KeyI');await page.waitForSelector('#panel:not(.hidden)');await page.screenshot({path:'test-results/02-inventory.png'});
 await page.locator('#panelClose').click();
 await page.keyboard.press('KeyM');await page.waitForSelector('#panel:not(.hidden)');await page.screenshot({path:'test-results/03-map.png'});
 await page.locator('#panelClose').click();
 await page.waitForTimeout(200);await page.reload();
 assert.ok(await page.evaluate(()=>!!localStorage.getItem('anomalia-primeval-outboundun-save-v1')),'progress saved on pagehide');
 await page.click('#startBtn');await page.waitForTimeout(1000);
 await page.evaluate(()=>document.exitPointerLock?.());
 await page.screenshot({path:'test-results/04-reloaded.png'});
 assert.deepEqual(failures,[],'no page errors or shader compilation errors');
 console.log('Actual WebGL render, forward movement, inventory, map, save and reload passed.');
}finally{await browser?.close();await new Promise(r=>server.close(r))}
