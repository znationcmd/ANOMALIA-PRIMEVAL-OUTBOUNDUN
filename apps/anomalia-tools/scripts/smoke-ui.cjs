'use strict';
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader']});
 const page=await browser.newPage({viewport:{width:1366,height:768},deviceScaleFactor:1});
 const errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.addInitScript(()=>{
  const id='visual-test-project';
  window.anomaliaTools={
   call:async (method,params)=>{
    if(method==='listProjects')return [{id,name:'Projet ANOMALIA',description:'Atelier de validation',createdAt:'2026-10-25T00:00:00Z'}];
    if(method==='listFiles')return [{type:'folder',path:'Content/Terrain'},{type:'folder',path:'Content/Models'},{type:'folder',path:'Content/Textures'}];
    if(method==='overview')return {version:'0.2.6',workspace:'C:/ANOMALIA/Workdrive',projects:1,modules:[]};
    if(method==='getEconomy')return {items:[]};
    if(method==='getNativeModStatus')return {ready:false,detail:'Unreal non configuré'};
    if(method==='listWorkshopMods')return [];
    return {saved:false};
   },
   onNavigate:()=>()=>{},
   chooseAssets:async()=>[],openFolder:async()=>'',exportPackage:async()=>({cancelled:true}),
   updates:{status:async()=>({currentVersion:'0.2.6',phase:'a-jour',message:'ANOMALIA Tools à jour',progress:0}),
     subscribe:()=>()=>{},check:async()=>({phase:'a-jour'}),install:async()=>({})}
  };
 });
 try{
  await page.goto('http://127.0.0.1:4175/',{waitUntil:'networkidle'});
  await page.locator('#appSidebarVersion').waitFor();
  await page.screenshot({path:'screenshots/anomalia-tools-dashboard-1366x768.png',fullPage:false});
  const nav=page.locator('.sidebarNav');
  const before=await nav.evaluate(x=>({visible:x.clientHeight,full:x.scrollHeight}));
  assert.ok(before.full>before.visible,'sidebar must overflow at laptop resolution');
  await nav.evaluate(el=>{el.scrollTop=el.scrollHeight;});
  const final=await nav.evaluate(x=>x.scrollTop);
  assert.ok(final>0,'sidebar must scroll to its last buttons');
  console.log('Renderer errors at startup',JSON.stringify(errors));
  console.log('Navigation binding',await page.evaluate(()=>({
    title:document.querySelector('#pageTitle')?.textContent,
    root:document.querySelector('#systemStatus')?.outerHTML.slice(0,150),
    navHandler:typeof document.querySelector('[data-tab="systemStatus"]')?.onclick
  })));
  await page.locator('[data-tab="systemStatus"]').click();
  console.log('Status after click',await page.evaluate(()=>({
    title:document.querySelector('#pageTitle')?.textContent,
    hidden:document.querySelector('#systemStatus')?.hidden,
    style:getComputedStyle(document.querySelector('#systemStatus')).display,
    errors:window.__errors || null
  })));
  assert.equal(await page.locator('#systemStatus').isVisible(),true);
  await page.locator('[data-utility="terrainProcessor"]').click();
  assert.equal(await page.locator('#utilities').isVisible(),true);
  assert.equal(await page.locator('#utility-terrainProcessor').isVisible(),true);
  const names=['bankrev','imagepaa','cfgconvert','dsutils','texview','navmesh'];
  for(const name of names){
   await page.locator('[data-utility="'+name+'"]').click();
   assert.equal(await page.locator('#utility-'+name).isVisible(),true,name);
  }
  await page.locator('[data-tools-menu="tools"]').click();
  assert.equal(await page.locator('#toolsMenuDropdown').isVisible(),true);
  await page.locator('[role="menuitem"]').first().click();
  assert.equal(await page.locator('#workbench').isVisible(),true);
  await page.locator('[data-utility="imagepaa"]').click();
  await page.screenshot({path:'screenshots/anomalia-tools-utilities-1366x768.png',fullPage:false});
  console.log('Visual/UI checks: sidebar scroll, status, all utility pages, menus passed',before,final);
  assert.deepEqual(errors,[],'renderer runtime errors');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
