// Optional browser smoke test: TEST_URL=http://127.0.0.1:8783 node tests/video_browser.cjs
const assert = require('node:assert/strict');
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({headless: true, channel:'msedge'});
  try {
    for (const width of [390, 1440]) {
      const page = await browser.newPage({viewport:{width,height:844}});
      const errors=[];page.on('pageerror', e=>errors.push(e.message));
      await page.goto((process.env.TEST_URL || 'http://127.0.0.1:8783')+'/instagram');
      await page.getByRole('button',{name:'Instagram Reel'}).waitFor();
      assert.equal(await page.locator('[data-import-pane="video"]').isVisible(),true);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
      await page.goto(process.env.TEST_URL || 'http://127.0.0.1:8783/');
      await page.getByRole('button',{name:'+ Add a recipe'}).click();
      await page.getByRole('button',{name:'Instagram Reel'}).click();
      assert.equal(await page.locator('[data-import-pane="video"]').isVisible(),true);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
      await page.locator('#video-url').fill('https://www.instagram.com/reel/AbCd12345/?igsh=test');
      let polling=0;
      await page.route('**/api/import-video', async route=>route.fulfill({status:202,contentType:'application/json',body:JSON.stringify({job_id:'x'.repeat(24),token:'secret',state:'queued'})}));
      await page.route('**/api/import-video/jobs/*', async route=>{
        if(route.request().method()==='POST')return route.fulfill({contentType:'application/json',body:'{"state":"canceled"}'});
        polling++;
        const job=polling===1?{state:'downloading'}:{state:'failed',error:'Instagram prevented this video from being downloaded. Try another public Reel.'};
        return route.fulfill({contentType:'application/json',body:JSON.stringify(job)});
      });
      await page.locator('#import-video').click();
      await page.getByText('Retrieving video and caption…').waitFor();
      await page.getByText('Instagram prevented this video from being downloaded.',{exact:false}).waitFor();
      assert.equal(await page.locator('#import-video').isEnabled(),true);
      assert.equal(await page.locator('#video-url').inputValue(),'https://www.instagram.com/reel/AbCd12345/?igsh=test',
        'a failed import keeps the link for retry');
      await page.unrouteAll();
      await page.route('**/api/import-video', async route=>route.fulfill({status:202,contentType:'application/json',body:JSON.stringify({job_id:'y'.repeat(24),token:'secret',state:'queued'})}));
      const draft={title:'Pasta',ingredients:[{text:'1 cup pasta'}],instructions:[{text:'Boil pasta.',number:1}],tags:[],author:'cookalice',source_url:'https://www.instagram.com/reel/AbCd12345/',import:{method:'instagram_reel',status:'awaiting_user_review',raw_text:'Original caption\n1 cup pasta\n\nAudio transcript\nBoil pasta.\n\nOn-screen text\n(none)',issues:['Review quantity.']}};
      await page.route('**/api/import-video/jobs/*', async route=>route.fulfill({contentType:'application/json',body:JSON.stringify({state:'completed',result:draft})}));
      await page.getByRole('button',{name:'Website link'}).click();
      await page.locator('#recipe-url').fill('https://www.instagram.com/reel/AbCd12345/?igsh=test');
      await page.locator('#import-url').click();
      await page.getByRole('heading',{name:'Review your recipe.'}).waitFor();
      assert.equal(await page.locator('#source-text').textContent(),draft.import.raw_text);
      assert.equal((await page.request.get((process.env.TEST_URL || 'http://127.0.0.1:8783')+'/api/recipes')).ok(),true);
      await page.locator('[name="title"]').fill('My pasta');
      await page.locator('#save').click();
      await page.getByRole('heading',{name:'My pasta'}).waitFor();
      const rows=await (await page.request.get((process.env.TEST_URL || 'http://127.0.0.1:8783')+'/api/recipes')).json();
      assert(rows.some(r=>r.title==='My pasta'&&r.source_url===draft.source_url&&r.import.status==='reviewed'&&!r.import.raw_text));
      await page.getByRole('button',{name:'+ Add a recipe'}).click();
      await page.getByRole('button',{name:'Instagram Reel'}).click();
      assert.equal(await page.locator('#video-url').inputValue(),'','a new import starts with an empty Reel link');
      await page.route('**/api/recipes',route=>route.fulfill({status:302,headers:{Location:'/login'},body:''}));
      await page.locator('#sync-recipes').click();
      await page.getByRole('link',{name:'Reconnect and load the latest website'}).waitFor();
      assert.equal(new URL(page.url()).pathname,'/', 'open editor must not auto navigate away');
      await page.unroute('**/api/recipes');
      await page.locator('#sync-recipes').click();
      await page.locator('#connection-notice').waitFor({state:'detached'});
      await page.route('**/api/recipes', route=>route.fulfill({status:503,contentType:'text/html',body:'Unavailable'}));
      await page.locator('#sync-recipes').click();
      await page.getByRole('link',{name:'Reconnect and load the latest website'}).waitFor();
      assert.equal(await page.getByRole('link',{name:'Reconnect and load the latest website'}).getAttribute('href'),'/refresh');
      await page.unroute('**/api/recipes');
      await page.locator('#sync-recipes').click();
      await page.locator('#connection-notice').waitFor({state:'detached'});
      assert.deepEqual(errors,[]);
      await page.close();
    }
    const auth=await browser.newPage();
    await auth.route('**/api/recipes',route=>route.fulfill({status:302,headers:{Location:'/login'},body:''}));
    await auth.route('**/refresh',route=>route.fulfill({status:200,contentType:'text/html',body:'<h1>Sign in</h1>'}));
    await auth.goto(process.env.TEST_URL || 'http://127.0.0.1:8783/');
    await auth.getByRole('heading',{name:'Sign in'}).waitFor();
    assert.equal(new URL(auth.url()).pathname,'/refresh');
    await auth.close();
    console.log('Browser video flow passed at 390px and 1440px');
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1});
