// Run with NODE_PATH pointing at the bundled playwright package.
const assert = require('node:assert/strict');
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');

const web = path.join(__dirname, '..', 'web');
let revision = 1;
let workerRevision = 1;
let reportedShell = 'recipe-shell-v28';
let refreshRequests = 0;
const server = http.createServer((request, response) => {
  const name = new URL(request.url, 'http://localhost').pathname;
  response.setHeader('Cache-Control', 'no-store');
  if (name === '/api/site-version') {
    response.setHeader('Content-Type', 'application/json');
    return response.end(JSON.stringify({shell: reportedShell}));
  }
  if (['/', '/instagram', '/menu', '/refresh'].includes(name)) {
    if (name === '/refresh') { refreshRequests++; reportedShell = 'recipe-shell-v28'; }
    response.setHeader('Content-Type', 'text/html');
    return response.end(`<!doctype html><html><body data-revision="${revision}"><main><div class="offline-bar">Recipes</div><section id="editor" hidden></section></main><script src="/offline-v28.js" defer></script><script>addEventListener('load',()=>{if(location.pathname==='/refresh')history.replaceState(null,'','/')})</script></body></html>`);
  }
  if (name === '/sw.js') {
    response.setHeader('Content-Type', 'text/javascript');
    return response.end(fs.readFileSync(path.join(web, 'sw.js')) + `\n// test revision ${workerRevision}\n`);
  }
  if (name === '/offline-v28.js') {
    response.setHeader('Content-Type', 'text/javascript');
    return response.end(fs.readFileSync(path.join(web, 'offline.js')));
  }
  if (name === '/categories.json') return response.end('[]');
  if (name === '/assets/turkey.png') return response.end('image');
  if (['/app-v28.js', '/style-v28.css'].includes(name)) return response.end('');
  if (['/manifest.webmanifest', '/apple-touch-icon.png', '/icon-192.png', '/icon-512.png'].includes(name)) return response.end(fs.readFileSync(path.join(web, name.slice(1))));
  response.statusCode = 404; response.end('Not found');
});

(async () => {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  let browser;
  try {
    browser = await chromium.launch({headless:true, channel:'msedge'});
    const context = await browser.newContext({serviceWorkers:'allow'});
    const page = await context.newPage();
    await page.goto(base);
    await page.waitForFunction(() => !!navigator.serviceWorker.controller);
    assert.equal(await page.locator('body').getAttribute('data-revision'), '1');
    assert.equal(await page.evaluate(async()=>{
      const cache=await caches.open('recipe-shell-v28');
      return !!(await cache.match('/refresh'));
    }),false,
      'sign-in recovery must bypass the service worker cache');

    revision = 2;
    await page.reload();
    assert.equal(await page.locator('body').getAttribute('data-revision'), '2', 'online reload must fetch new HTML');

    await context.setOffline(true);
    await page.reload();
    assert.equal(await page.locator('body').getAttribute('data-revision'), '2', 'offline reload must use saved shell');
    await context.setOffline(false);

    await page.locator('#editor').evaluate(element => element.hidden = false);
    workerRevision = 2;
    await page.evaluate(async () => (await navigator.serviceWorker.getRegistration()).update());
    await page.locator('#shell-update').waitFor();
    assert.equal(await page.locator('body').getAttribute('data-revision'), '2', 'open editor must not auto reload');
    assert.equal(await page.getByRole('button', {name:'Load website update'}).isVisible(), true);
    const priorRefreshes = refreshRequests;
    revision = 3;
    reportedShell = 'recipe-shell-v29';
    await page.getByRole('button', {name:'Load website update'}).click();
    await page.waitForFunction(() => document.body.dataset.revision === '3');
    assert.equal(refreshRequests, priorRefreshes + 1, 'updates must use the uncached refresh route');
    assert.equal(await page.locator('body').getAttribute('data-revision'), '3');
    reportedShell = 'recipe-shell-v29';
    revision = 4;
    await page.evaluate(() => document.dispatchEvent(new Event('visibilitychange')));
    await page.waitForFunction(() => document.body.dataset.revision === '4');
    assert.ok(refreshRequests >= priorRefreshes + 2, 'a version check must detect an update without a worker change');
    console.log('Shell online refresh, offline fallback, and edit protection passed');
    await context.close();
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
