const assert = require('node:assert/strict');
const {spawn} = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {chromium} = require('playwright');

(async()=>{
 const root=path.resolve(__dirname,'..');
 const data=fs.mkdtempSync(path.join(os.tmpdir(),'recipe-menu-test-'));
 const port=18771;
 const server=spawn(process.env.BUNDLED_PYTHON||'python',['server.py','--port',String(port)],{cwd:root,env:{...process.env,RECIPE_DATA_DIR:data},windowsHide:true,stdio:'ignore'});
 let browser;
 try{
  for(let i=0;i<50;i++){
   try{const response=await fetch(`http://127.0.0.1:${port}/health`);if(response.ok)break}catch{}
   if(i===49)throw Error('Test server did not start');
   await new Promise(resolve=>setTimeout(resolve,100));
  }
  browser=await chromium.launch({headless:true,channel:'msedge'});
  for(const width of [390,1440]){
   const page=await browser.newPage({viewport:{width,height:844}});
   const errors=[];page.on('pageerror',error=>errors.push(error.message));
   await page.goto(`http://127.0.0.1:${port}/`);
   if(width===390){
    const menuButton=await page.locator('#menu-link').boundingBox(),addButton=await page.locator('#add').boundingBox();
    assert.ok(menuButton&&addButton);
    assert.ok(Math.abs(menuButton.y-addButton.y)<2);
   }
   await (width===390?page.locator('[data-nav="menu"]'):page.locator('#menu-link')).click();
   if(width===1440)await page.locator('#menu-next').click();
   await page.locator('#menu-days textarea').first().waitFor();
   assert.equal(await page.locator('#menu-days textarea').count(),7);
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
   await page.locator('#menu-days textarea').first().fill(`Pork butt + baked beans ${width}`);
   await page.locator('#menu-snacks').fill('Grapes\nCarrots and hummus');
   await page.locator('#menu-lunches').fill('Chicken + rice');
   await page.locator('#menu-sweet-treats').fill('Ice cream bars');
   page.once('dialog',dialog=>dialog.dismiss());
   await page.locator('#menu-next').click();
   assert.equal(await page.locator('#menu-days textarea').first().inputValue(),`Pork butt + baked beans ${width}`);
   await page.getByRole('button',{name:'Save weekly menu'}).click();
   await page.getByText('Saved for this week.').waitFor();
   assert.equal(await page.locator('#menu-display').isVisible(),true);
   assert.equal(await page.locator('#menu-form').isVisible(),false);
   assert.equal(await page.locator('#menu-display-content').getByText(`Pork butt + baked beans ${width}`).count(),1);
   assert.equal(await page.locator('#menu-display-content').getByText('Ice cream bars').count(),1);
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
   if(process.env.MENU_SCREENSHOT){fs.mkdirSync(path.join(root,'tmp'),{recursive:true});await page.screenshot({path:path.join(root,'tmp',`weekly-menu-${width}.png`),fullPage:true})}
   await page.reload();
   await (width===390?page.locator('[data-nav="menu"]'):page.locator('#menu-link')).click();
   if(width===1440)await page.locator('#menu-next').click();
   await page.locator('#menu-display').waitFor({state:'visible'});
   assert.equal(await page.locator('#menu-form').isVisible(),false);
   await page.getByRole('button',{name:'Edit menu'}).click();
   await page.locator('#menu-days textarea').first().waitFor();
   assert.equal(await page.locator('#menu-days textarea').first().inputValue(),`Pork butt + baked beans ${width}`);
   assert.equal(await page.locator('#menu-snacks').inputValue(),'Grapes\nCarrots and hummus');
   assert.equal(await page.locator('#menu-lunches').inputValue(),'Chicken + rice');
   assert.equal(await page.locator('#menu-sweet-treats').inputValue(),'Ice cream bars');
   await page.locator('#menu-next').click();
   await page.locator('#menu-days textarea').first().waitFor();
   assert.equal(await page.locator('#menu-days textarea').first().inputValue(),'');
   assert.equal(await page.locator('#menu-display').isVisible(),false);
   assert.deepEqual(errors,[]);
   await page.close();
  }
  const mobile=await browser.newPage({viewport:{width:390,height:844}});
  await mobile.goto(`http://127.0.0.1:${port}/menu`);
  await mobile.locator('#menu-display').waitFor({state:'visible'});
  assert.equal(await mobile.locator('#menu-link').isVisible(),true);
  assert.equal(await mobile.locator('.menu-display-day').count(),7);
  assert.equal(await mobile.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await mobile.close();
  const narrow=await browser.newPage({viewport:{width:320,height:700}});
  await narrow.goto(`http://127.0.0.1:${port}/menu`);
  await narrow.locator('#menu').waitFor({state:'visible'});
  const narrowMenu=await narrow.locator('#menu-link').boundingBox(),narrowAdd=await narrow.locator('#add').boundingBox();
  assert.ok(narrowMenu&&narrowAdd);
  assert.ok(Math.abs(narrowMenu.y-narrowAdd.y)<2);
  assert.equal(await narrow.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await narrow.close();
  console.log('Weekly menu browser check passed at 390px and 1440px.');
 }finally{
  await browser?.close();server.kill();
  if(path.dirname(data)===fs.realpathSync(os.tmpdir())&&path.basename(data).startsWith('recipe-menu-test-'))fs.rmSync(data,{recursive:true,force:true});
 }
})().catch(error=>{console.error(error);process.exitCode=1});
