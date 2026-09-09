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
 await navigator.serviceWorker.register('/sw.js');
 await navigator.serviceWorker.ready;
})();
// Attach a rejection handler immediately; the UI reports failure when saving its snapshot.
window.offlineShellReady.catch(()=>{});
