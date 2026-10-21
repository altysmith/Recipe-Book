// Server recipes are read-only snapshots. Checklists are independent device state.
window.recipeStorage = (() => {
 const opened = new Promise((resolve,reject)=>{
  const request=indexedDB.open('little-recipe-box',1);
  request.onupgradeneeded=()=>request.result.createObjectStore('data');
  request.onsuccess=()=>resolve(request.result);request.onerror=()=>reject(request.error);
 });
 async function get(key){const db=await opened;return new Promise((resolve,reject)=>{const r=db.transaction('data').objectStore('data').get(key);r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)})}
 async function set(key,value){const db=await opened;return new Promise((resolve,reject)=>{const tx=db.transaction('data','readwrite');tx.objectStore('data').put(value,key);tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error);tx.onabort=()=>reject(tx.error)})}
 return {get,set};
})();
window.offlineShellReady = (async()=>{
 if(!('serviceWorker' in navigator))throw Error('Offline opening is unavailable in this browser.');
 // A new worker can take control after an old cache served this page. Reload a
 // browsing view so its new HTML and scripts appear without another manual refresh.
 // Keep an open editor intact and offer a deliberate update instead.
 navigator.serviceWorker.addEventListener('controllerchange',()=>{
  const menuOpen=document.querySelector('#menu')?.hidden===false;
  const editingMenu=menuOpen&&document.querySelector('#menu-form')?.hidden===false;
  if(document.querySelector('#editor')?.hidden!==false&&!editingMenu){
   if(menuOpen&&location.pathname!=='/menu')location.replace('/menu');
   else location.reload();
   return;
  }
  if(document.querySelector('#shell-update'))return;
  const notice=document.createElement('div');
  notice.id='shell-update';notice.className='offline-bar';notice.setAttribute('role','status');
  const label=document.createElement('span');
  label.textContent='A website update is ready. Save your changes before loading it.';
  const button=document.createElement('button');
  button.type='button';button.textContent='Load website update';button.onclick=()=>location.reload();
  notice.append(label,button);
  document.querySelector('.offline-bar')?.after(notice);
 });
 const registration=await navigator.serviceWorker.register('/sw.js',{updateViaCache:'none'});
 if(navigator.onLine)registration.update().catch(()=>{});
 await navigator.serviceWorker.ready;
})();
// Attach a rejection handler immediately; the UI reports failure when saving its snapshot.
window.offlineShellReady.catch(()=>{});
