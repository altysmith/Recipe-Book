const assert = require('node:assert/strict');
const {spawn} = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {chromium} = require('playwright');

(async()=>{
 const root=path.resolve(__dirname,'..');
 const data=fs.mkdtempSync(path.join(os.tmpdir(),'recipe-groceries-test-'));
 const port=18772;
 const server=spawn(process.env.BUNDLED_PYTHON||'python',['server.py','--port',String(port)],{cwd:root,env:{...process.env,RECIPE_DATA_DIR:data},windowsHide:true,stdio:'ignore'});
 let browser;
 try{
  for(let i=0;i<50;i++){
   try{if((await fetch(`http://127.0.0.1:${port}/health`)).ok)break}catch{}
   if(i===49)throw Error('Test server did not start');
   await new Promise(resolve=>setTimeout(resolve,100));
  }
  browser=await chromium.launch({headless:true,channel:'msedge'});
  const first=await browser.newPage({viewport:{width:390,height:844}});
  const second=await browser.newPage({viewport:{width:1440,height:900}});
  const errors=[];
  for(const page of [first,second]){page.on('pageerror',error=>errors.push(error.message));await page.goto(`http://127.0.0.1:${port}/`)}
  await first.locator('[data-nav="groceries"]').click();
  await second.locator('#grocery-link').click();
  await first.locator('#grocery-input').fill('Milk');
  await first.getByRole('button',{name:'Add item'}).click();
  await first.getByText('Saved for both of you.').waitFor();
  await second.getByRole('button',{name:'Refresh list'}).click();
  await second.locator('.grocery-row').first().getByText('Milk').waitFor();
  await Promise.all([
   second.waitForResponse(response=>response.url().endsWith('/api/groceries')&&response.request().method()==='POST'),
   second.locator('.grocery-row input').check(),
  ]);
  await first.getByRole('button',{name:'Refresh list'}).click();
  await first.waitForFunction(()=>document.querySelector('.grocery-row input')?.checked===true);
  assert.equal(await first.locator('.grocery-row input').isChecked(),true);
  first.once('dialog',dialog=>dialog.accept());
  await first.getByRole('button',{name:'Clear checked items'}).click();
  await first.getByText('Your list is empty.').waitFor();
  await first.locator('#grocery-input').fill('Eggs');
  await first.getByRole('button',{name:'Add item'}).click();
  first.once('dialog',dialog=>dialog.accept());
  await first.getByRole('button',{name:'Start a new list'}).click();
  await first.getByText('Your list is empty.').waitFor();
  assert.equal(await first.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  assert.deepEqual(errors,[]);
  console.log('Shared grocery browser check passed at 390px and 1440px.');
 }finally{
  await browser?.close();server.kill();
  if(path.dirname(data)===fs.realpathSync(os.tmpdir())&&path.basename(data).startsWith('recipe-groceries-test-'))fs.rmSync(data,{recursive:true,force:true});
 }
})().catch(error=>{console.error(error);process.exitCode=1});
