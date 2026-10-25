'use strict';
const assert=require('node:assert/strict');
const {chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader']});
 const page=await browser.newPage({viewport:{width:1366,height:768},deviceScaleFactor:1,acceptDownloads:true});
 const errors=[];
 page.on('pageerror',error=>errors.push(error.message));
 try{
  await page.goto('http://127.0.0.1:4174/',{waitUntil:'networkidle'});
  await page.locator('#mapLauncher:not([hidden])').waitFor();
  await page.waitForFunction(()=>document.querySelectorAll('.mapPickerGrid .mapCard').length>=3);
  assert.equal(await page.locator('.mapPickerGrid .mapActionCard').count(),2,
    'the extra cards must be actionable import/link options, not invented maps');
  await page.locator('#mapResume').click();
  await page.locator('#mapLauncher[hidden]').waitFor();
  await page.locator('#menuFile').click();
  assert.equal(await page.getByRole('menuitem',{name:/Enregistrer sous/}).count(),1);
  assert.equal(await page.getByRole('menuitem',{name:/Importer un modèle GLB/}).count(),1);
  await page.getByRole('menuitem',{name:/Choisir une carte/}).click();
  await page.locator('#mapLauncher:not([hidden])').waitFor();
  await page.locator('#mapCreateNew').click();
  await page.locator('#mapLauncher[hidden]').waitFor();
  await page.locator('#saveScene').click();
  await page.locator('#openMapLibrary').click();
  await page.waitForFunction(()=>document.querySelectorAll('.mapPickerGrid .mapLocal').length>=2);
  const covers=await page.locator('.mapLocal .mapActualPreview').count();
  console.log('ANOMALIA Editor map flow successful:',{
    mapCount:await page.locator('.mapLocal').count(),realScenePreviews:covers,
    menuItems:'file/save/import/open',viewport:Boolean(await page.locator('#viewport canvas').count())
  });
  assert.equal(errors.length,0,'browser page errors: '+errors.join('; '));
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1});
