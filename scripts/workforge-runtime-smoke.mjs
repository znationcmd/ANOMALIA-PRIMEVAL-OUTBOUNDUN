import {chromium, _electron} from 'playwright';
import assert from 'node:assert/strict';
import {mkdir, writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';

// The Windows job supplies the installed executable; local validation uses Vite.
const output=resolve(process.env.WORKFORGE_EVIDENCE||'test-results/workforge');
await mkdir(output,{recursive:true});
let runtime;
const report={state:'FAILED',checks:[],installedExecutable:process.env.WORKFORGE_EXE||null};
try {
  let page;
  if(process.env.WORKFORGE_EXE){
    runtime=await _electron.launch({executablePath:process.env.WORKFORGE_EXE,timeout:120000});
    page=await runtime.firstWindow({timeout:120000});
  }else{
    runtime=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox','--enable-unsafe-swiftshader']});
    page=await runtime.newPage({viewport:{width:1440,height:900}});
    await page.goto(process.env.WORKFORGE_URL||'http://127.0.0.1:4173');
  }
  page.setDefaultTimeout(90000);
  const launch=page.locator('#workforgeBtn');
  await launch.waitFor({state:'visible'});
  await launch.click();
  const panel=page.locator('#workforgeRoot');
  await panel.waitFor({state:'visible'});
  assert.equal(await panel.getAttribute('role'),'dialog');
  report.checks.push('main_menu_opens_workforge');
  await page.screenshot({path:resolve(output,'main-menu-workforge.png')});
  await page.locator('#wfSearch').fill('aucun-resultat-test');
  assert.ok((await page.locator('#wfCards').innerText()).length>0);
  await page.keyboard.press('Escape');
  await panel.waitFor({state:'hidden'});
  assert.equal(await launch.evaluate(e=>document.activeElement===e),true);
  report.checks.push('search_escape_and_focus_return');
  await launch.click();
  await page.locator('#wfPlay').click();
  await panel.waitFor({state:'hidden'});
  await page.locator('#startScreen').waitFor({state:'hidden'});
  assert.equal(await page.locator('#workforgeHudBtn').count(),0);
  assert.equal(await launch.isVisible(),false);
  report.checks.push('play_closes_workforge_and_no_gameplay_entry');
  await page.screenshot({path:resolve(output,'gameplay-without-workforge.png')});
  report.state='PASSED';
}catch(error){report.error=error.stack;throw error;}
finally{
  await writeFile(resolve(output,'runtime.json'),JSON.stringify(report,null,2));
  await runtime?.close();
}
