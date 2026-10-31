const assert = require('node:assert/strict');
const {spawn} = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {chromium} = require('playwright');

(async()=>{
 const root=path.resolve(__dirname,'..');
 const data=fs.mkdtempSync(path.join(os.tmpdir(),'recipe-autosave-test-'));
 const port=18784;
 const server=spawn(process.env.BUNDLED_PYTHON||'python',['server.py','--port',String(port)],{cwd:root,env:{...process.env,RECIPE_DATA_DIR:data},windowsHide:true,stdio:'ignore'});
 let browser;
 try{
  for(let i=0;i<50;i++){
   try{if((await fetch(`http://127.0.0.1:${port}/health`)).ok)break}catch{}
   if(i===49)throw Error('Test server did not start');
   await new Promise(resolve=>setTimeout(resolve,100));
  }
  browser=await chromium.launch({headless:true,channel:'msedge'});
  const page=await browser.newPage({viewport:{width:390,height:844},isMobile:true});
  const errors=[];page.on('pageerror',error=>errors.push(error.message));
  await page.goto(`http://127.0.0.1:${port}/`);
  await page.getByRole('button',{name:'Add a recipe'}).click();
  await page.getByRole('button',{name:'Type recipe yourself'}).click();
  await page.locator('[name=title]').fill('Autumn soup');
  assert.match(await page.locator('#recipe-save-status').innerText(),/Draft kept on this device/);
  await page.reload();
  await page.getByRole('button',{name:'Add a recipe'}).click();
  assert.equal(await page.locator('[name=title]').inputValue(),'Autumn soup');
  assert.equal(await page.locator('#recipe-form').isVisible(),true);
  await page.locator('[name=ingredients]').fill('2 cups broth');
  await page.waitForFunction(()=>document.querySelector('#recipe-save-status')?.textContent.includes('Saved automatically'));
  let recipes=await (await fetch(`http://127.0.0.1:${port}/api/recipes`)).json();
  assert.equal(recipes.length,1);
  assert.equal(recipes[0].title,'Autumn soup');
  assert.equal(recipes[0].ingredients[0].text,'2 cups broth');
  await page.route('**/api/recipes',route=>route.request().method()==='POST'?route.abort():route.continue());
  await page.locator('[name=instructions]').fill('Simmer for 15 minutes.');
  await page.waitForFunction(()=>document.querySelector('#recipe-save-status')?.textContent.includes('Could not sync yet'));
  await page.reload();
  await page.getByRole('button',{name:'Add a recipe'}).click();
  assert.equal(await page.locator('[name=instructions]').inputValue(),'Simmer for 15 minutes.');
  await page.unroute('**/api/recipes');
  await page.locator('[name=instructions]').fill('Simmer for 20 minutes.');
  await page.waitForFunction(()=>document.querySelector('#recipe-save-status')?.textContent.includes('Saved automatically'));
  recipes=await (await fetch(`http://127.0.0.1:${port}/api/recipes`)).json();
  assert.equal(recipes.length,1);
  assert.equal(recipes[0].instructions[0].text,'Simmer for 20 minutes.');
  await page.getByRole('button',{name:'Back to recipe book'}).click();
  await page.getByRole('button',{name:'Add a recipe'}).click();
  await page.getByRole('button',{name:'Paste or type text'}).click();
  await page.locator('#paste').fill('Soup\n2 cups broth\nSimmer until hot');
  await page.reload();
  await page.getByRole('button',{name:'Add a recipe'}).click();
  assert.equal(await page.locator('#paste').inputValue(),'Soup\n2 cups broth\nSimmer until hot');
  await page.getByRole('button',{name:'Create recipe draft'}).click();
  await page.getByRole('heading',{name:'Review your recipe.'}).waitFor();
  recipes=await (await fetch(`http://127.0.0.1:${port}/api/recipes`)).json();
  assert.equal(recipes.length,1,'imported text still opens for review before it is shared');
  await page.locator('[name=title]').fill('Restored soup');
  await page.locator('[name=ingredients]').fill('2 cups broth');
  await page.waitForFunction(()=>document.querySelector('#recipe-save-status')?.textContent.includes('Saved automatically'));
  recipes=await (await fetch(`http://127.0.0.1:${port}/api/recipes`)).json();
  assert.equal(recipes.length,2);
  assert.equal(errors.length,0,errors.join('\n'));
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'mobile editor must not overflow');
  console.log('Recipe autosave: incomplete draft, server sync, failed sync recovery, import review, text recovery, and 390px layout passed.');
 }finally{
  if(browser)await browser.close();
  server.kill();
  fs.rmSync(data,{recursive:true,force:true});
 }
})().catch(error=>{console.error(error);process.exitCode=1});
