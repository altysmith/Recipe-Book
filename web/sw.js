const SHELL='recipe-shell-v12';
const FILES=['/','/instagram','/style-v12.css','/app-v12.js','/offline-v12.js','/style.css','/app.js','/offline.js','/categories.json','/assets/turkey.png'];
self.addEventListener('install',event=>event.waitUntil((async()=>{
 const cache=await caches.open(SHELL);await cache.addAll(FILES);await self.skipWaiting();
})()));
self.addEventListener('activate',event=>event.waitUntil((async()=>{
 for(const key of await caches.keys())if(key.startsWith('recipe-shell-')&&key!==SHELL)await caches.delete(key);
 await self.clients.claim();
})()));
self.addEventListener('fetch',event=>{
 const url=new URL(event.request.url);
 if(event.request.method!=='GET'||url.origin!==self.location.origin)return;
 // Never cache API responses or writes: IndexedDB owns the validated recipe snapshot.
 if(!FILES.includes(url.pathname))return;
 event.respondWith((async()=>{
  const cache=await caches.open(SHELL);
  const saved=await cache.match(url.pathname);
  return saved||fetch(event.request);
 })());
});
