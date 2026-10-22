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
const SHELL_VERSION='recipe-shell-v29';
let shellUpdatePending=false;
function shellUpdateUrl(){
 const view=document.querySelector('#menu')?.hidden===false?'menu':document.querySelector('#groceries')?.hidden===false?'groceries':'';
 const params=new URLSearchParams({version:SHELL_VERSION});
 if(view)params.set('view',view);
 return '/refresh?'+params;
}
function loadShellUpdate(){location.replace(shellUpdateUrl())}
function showShellUpdate(){
 if(document.querySelector('#shell-update'))return;
 const notice=document.createElement('div');
 notice.id='shell-update';notice.className='offline-bar';notice.setAttribute('role','status');
 const label=document.createElement('span');
 label.textContent='A website update is ready. Save your changes before loading it.';
 const button=document.createElement('button');
 button.type='button';button.textContent='Load website update';button.onclick=loadShellUpdate;
 notice.append(label,button);
 document.querySelector('.offline-bar')?.after(notice);
}
function handleShellUpdate(){
 const editingMenu=document.querySelector('#menu')?.hidden===false&&document.querySelector('#menu-form')?.hidden===false;
 const groceryDraftOpen=document.querySelector('#groceries')?.hidden===false&&!!document.querySelector('#grocery-input')?.value.trim();
 if(navigator.onLine&&document.querySelector('#editor')?.hidden!==false&&!editingMenu&&!groceryDraftOpen)loadShellUpdate();
 else showShellUpdate();
}
window.offlineShellReady = (async()=>{
 if(!('serviceWorker' in navigator))throw Error('Offline opening is unavailable in this browser.');
 // /refresh is outside every saved shell, including older cache-first workers.
 navigator.serviceWorker.addEventListener('controllerchange',()=>{
  if(!shellUpdatePending){shellUpdatePending=true;handleShellUpdate()}
 });
 const registration=await navigator.serviceWorker.register('/sw.js',{updateViaCache:'none'});
 let checking=false;
 async function checkForUpdate(){
  if(checking||shellUpdatePending||document.hidden||!navigator.onLine)return;
  checking=true;
  try{
   // API routes bypass the service worker. This also detects changes when an
   // installed iPhone app stays open and Safari does not check its worker.
   const response=await fetch('/api/site-version',{cache:'no-store',redirect:'manual',signal:AbortSignal.timeout(5000)});
   if(response.ok&&response.headers.get('content-type')?.includes('application/json')){
    const {shell}=await response.json();
    if(shell&&shell!==SHELL_VERSION){shellUpdatePending=true;handleShellUpdate();return}
   }
   await registration.update();
  }catch{}finally{checking=false}
 }
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)checkForUpdate()});
 window.addEventListener('pageshow',checkForUpdate);
 window.addEventListener('online',checkForUpdate);
 setInterval(checkForUpdate,60000);
 checkForUpdate();
 await navigator.serviceWorker.ready;
})();
// Attach a rejection handler immediately; the UI reports failure when saving its snapshot.
window.offlineShellReady.catch(()=>{});
