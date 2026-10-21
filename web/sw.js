const SHELL='recipe-shell-v20';
const FILES=['/','/instagram','/style-v20.css','/app-v20.js','/offline-v20.js','/categories.json','/assets/turkey.png','/manifest.webmanifest','/apple-touch-icon.png','/icon-192.png','/icon-512.png'];
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
  // Fetch current shell files online; use the saved copy when offline or slow.
  // Recipe API responses are never stored in this cache.
  const controller=new AbortController();
  const timeout=setTimeout(()=>controller.abort(),5000);
  try{
   const response=await fetch(event.request,{signal:controller.signal});
   if(response.ok)try{await cache.put(url.pathname,response.clone())}catch{} // A full cache must not break online browsing.
   return response;
  }catch(error){
   const saved=await cache.match(url.pathname);
   if(saved)return saved;
   throw error;
  }finally{clearTimeout(timeout)}
 })());
});
