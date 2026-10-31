const assert = require('node:assert/strict');
const {spawn} = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {chromium} = require('playwright');

const photoBase64 = '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAoHBwgHBgoICAgLCgoLDhgQDg0NDh0VFhEYIx8lJCIfIiEmKzcvJik0KSEiMEExNDk7Pj4+JS5ESUM8SDc9Pjv/2wBDAQoLCw4NDhwQEBw7KCIoOzs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozv/wAARCAACAAIDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwCtRRRXzh9ef//Z';
const recipe = {
 id:'test-recipe',title:'Sunday Soup',author:'Lolo',servings:'4',
 total_minutes:35,tags:['Soups & Stews'],favorite:false,deleted:false,
 ingredients:[{text:'2 cups broth'},{text:'1 carrot'}],
 instructions:[{text:'Warm the broth.'},{text:'Add the carrot.'}],
 timing_notes:['Simmer 20 minutes.'],notes:'Serve with bread.',
 photo:'',source_photos:['private-photo-data'],
};
const expected = 'Sunday Soup\nServes 4 · Total time: 35 minutes\n\nIngredients\n• 2 cups broth\n• 1 carrot\n\nDirections\n1. Warm the broth.\n2. Add the carrot.\n\nTiming notes\n• Simmer 20 minutes.\n\nKitchen notes\nServe with bread.';

(async()=>{
 const root=path.resolve(__dirname,'..');
 const data=fs.mkdtempSync(path.join(os.tmpdir(),'recipe-share-test-'));
 const port=18773;
 const server=spawn(process.env.BUNDLED_PYTHON||'python',['server.py','--port',String(port)],{cwd:root,env:{...process.env,RECIPE_DATA_DIR:data},windowsHide:true,stdio:'ignore'});
 let browser;
 try{
  for(let i=0;i<50;i++){
   try{if((await fetch(`http://127.0.0.1:${port}/health`)).ok)break}catch{}
   if(i===49)throw Error('Test server did not start');
   await new Promise(resolve=>setTimeout(resolve,100));
  }
  browser=await chromium.launch({headless:true,channel:'msedge'});
  for(const [width,native] of [[390,true],[1440,false]]){
   const sample={...recipe,photo:native?'data:image/jpeg;base64,'+photoBase64:''};
   const page=await browser.newPage({viewport:{width,height:844},isMobile:width===390});
   const errors=[];page.on('pageerror',error=>errors.push(error.message));
   await page.addInitScript(hasShare=>{
    window.shared=null;window.copied=null;
    Object.defineProperty(navigator,'share',{configurable:true,value:hasShare?async data=>{window.shared=data}:undefined});
    Object.defineProperty(navigator,'canShare',{configurable:true,value:hasShare?data=>!!data.files:undefined});
    Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async text=>{window.copied=text}}});
   },native);
   await page.route('**/api/recipes',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify([sample])}));
   await page.goto(`http://127.0.0.1:${port}/`);
   await page.getByRole('button',{name:'Open Sunday Soup'}).first().click();
   const share=page.getByRole('button',{name:'Share recipe'});
   assert.equal(await share.isVisible(),true);
   await share.click();
   if(native){
    await page.waitForFunction(()=>window.shared!==null);
    assert.deepEqual(await page.evaluate(()=>window.shared),{title:'Sunday Soup',text:expected});
    assert.equal(await page.evaluate(()=>window.copied),null);
    const photoShare=page.getByRole('button',{name:'Share photo'});
    assert.equal(await photoShare.isVisible(),true);
    await photoShare.click();
    await page.waitForFunction(()=>window.shared?.files?.length===1);
    const attachment=await page.evaluate(async()=>{
     const share=window.shared,file=share.files?.[0];
     return {keys:Object.keys(share),name:file?.name,type:file?.type,bytes:[...new Uint8Array(await file.arrayBuffer())]};
    });
    assert.deepEqual(attachment.keys,['files'],'photo share must not include text because iPhone may drop the image');
    assert.equal(attachment.name,'recipe-photo.jpg');
    assert.equal(attachment.type,'image/jpeg');
    assert.deepEqual(attachment.bytes,[...Buffer.from(photoBase64,'base64')]);
    await page.evaluate(()=>Object.defineProperty(navigator,'canShare',{configurable:true,value:()=>false}));
    await photoShare.click();
    await page.getByText('This browser cannot attach the photo.',{exact:false}).waitFor();
   }else{
    assert.equal(await page.getByRole('button',{name:'Share photo'}).count(),0);
    await page.getByText('Recipe copied. Paste it into a text message.').waitFor();
    assert.equal(await page.evaluate(()=>window.copied),expected);
   }
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
   assert.deepEqual(errors,[]);
   await page.close();
  }
  console.log('Recipe share and copy checks passed at 390px and 1440px.');
 }finally{
  await browser?.close();server.kill();
  if(path.dirname(data)===fs.realpathSync(os.tmpdir())&&path.basename(data).startsWith('recipe-share-test-'))fs.rmSync(data,{recursive:true,force:true});
 }
})().catch(error=>{console.error(error);process.exitCode=1});
