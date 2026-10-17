// Run with NODE_PATH pointing at the bundled playwright package.
const assert = require('node:assert/strict');
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');

const web = path.join(__dirname, '..', 'web');
let revision = 1;
let workerRevision = 1;
const server = http.createServer((request, response) => {
  const name = new URL(request.url, 'http://localhost').pathname;
  response.setHeader('Cache-Control', 'no-store');
  if (['/', '/instagram', '/refresh'].includes(name)) {
    response.setHeader('Content-Type', 'text/html');
    return response.end(`<!doctype html><html><body data-revision="${revision}"><main><div class="offline-bar">Recipes</div><section id="editor" hidden></section></main><script src="/offline-v13.js" defer></script></body></html>`);
  }
  if (name === '/sw.js') {
    response.setHeader('Content-Type', 'text/javascript');
    return response.end(fs.readFileSync(path.join(web, 'sw.js')) + `\n// test revision ${workerRevision}\n`);
  }
  if (name === '/offline-v13.js') {
    response.setHeader('Content-Type', 'text/javascript');
    return response.end(fs.readFileSync(path.join(web, 'offline.js')));
  }
  if (name === '/categories.json') return response.end('[]');
  if (name === '/assets/turkey.png') return response.end('image');
  if (['/app-v13.js', '/style-v13.css'].includes(name)) return response.end('');
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
    console.log('Shell online refresh, offline fallback, and edit protection passed');
    await context.close();
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
