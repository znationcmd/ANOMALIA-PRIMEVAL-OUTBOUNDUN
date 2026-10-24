import {chromium} from 'playwright';
import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import {resolve,extname} from 'node:path';
import assert from 'node:assert/strict';

const root=resolve('dist');
const types={'.html':'text/html','.css':'text/css','.js':'text/javascript','.svg':'image/svg+xml','.json':'application/json'};
const server=createServer(async(req,res)=>{
 try{
  const loc=new URL(req.url,'http://localhost').pathname;
  const file=resolve(root,'.'+(loc==='/'?'/index.html':loc));
  if(!file.startsWith(root+'/')){res.writeHead(403);res.end();return;}
  res.setHeader('Content-Type',types[extname(file)]||'application/octet-stream');
  res.end(await readFile(file));
 }catch{res.writeHead(404);res.end();}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
let browser;
try{
 browser=await chromium.launch({headless:true,args:['--no-sandbox','--enable-unsafe-swiftshader','--use-angle=swiftshader']});
 const page=await browser.newPage({viewport:{width:1330,height:850}});
 const errors=[];page.on('pageerror',error=>errors.push(error.message));
 await page.goto('http://127.0.0.1:'+server.address().port+'/?smoke=workshop',{waitUntil:'domcontentloaded'});
 await page.waitForSelector('#startWorkshopBtn',{state:'visible'});
 await page.click('#startWorkshopBtn');
 await page.locator('#inGameWorkshop').waitFor({state:'visible'});
 assert.match(await page.locator('.igw-hero h2').textContent(),/ANOMALIA/);
 assert.match(await page.locator('#igwMessage').textContent(),/Workshop|bibliothèque|navigateur/);
 await page.fill('#igwSearch','SUV');
 await page.locator('#igwCategories .igw-category').filter({hasText:'Véhicules'}).click();
 await page.click('#igwClose');
 assert.equal(await page.locator('#inGameWorkshop').isVisible(),false,'Back button must close Workshop');
 await page.click('#startWorkshopBtn');
 await page.keyboard.press('Escape');
 assert.equal(await page.locator('#inGameWorkshop').isVisible(),false,'Escape must close Workshop');
 assert.equal(errors.length,0,'Browser runtime errors: '+errors.join(' | '));
 console.log('PASS: Workshop opens inside ANOMALIA and closes correctly');
}finally{await browser?.close();await new Promise(resolve=>server.close(resolve));}
