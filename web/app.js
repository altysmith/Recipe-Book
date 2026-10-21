const $=s=>document.querySelector(s), form=$('#recipe-form');
let importEpoch=0;
let activeVideoJob=null;
let categories=[], recipes=[], current=null, editing={}, favorites=false, trash=false, dirty=false;
let menuWeek=null, menuDirty=false;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function message(text){const inEditor=!$('#editor').hidden;$('#status').textContent=inEditor?'':text;$('#import-status').textContent=inEditor?text:''}
class AccessRedirect extends Error{}
const redirected=r=>r.type==='opaqueredirect'||(r.status>=300&&r.status<400);
async function recoverAccess(error){
 if($('#editor').hidden===false||dirty)return false;
 let expired=error instanceof AccessRedirect;
 if(!expired){
  try{expired=redirected(await fetch('/health',{redirect:'manual',cache:'no-store',signal:AbortSignal.timeout(5000)}))}catch{}
 }
 if(!expired)return false;
 try{
  const last=Number(sessionStorage.getItem('recipe-access-recovery')||0);
  if(Date.now()-last<60000)return false;
  sessionStorage.setItem('recipe-access-recovery',String(Date.now()));
 }catch{return false}
 location.replace('/refresh');return true;
}
function connectionNotice(show){
 let notice=$('#connection-notice');
 if(!show){notice?.remove();return}
 if(notice)return;
 notice=document.createElement('div');notice.id='connection-notice';notice.className='notice';notice.setAttribute('role','status');
 const label=document.createElement('span');label.textContent='The live recipe book could not be reached. Your sign-in may have expired. ';
 const link=document.createElement('a');link.href='/refresh';link.textContent='Reconnect and load the latest website';
 notice.append(label,link);document.querySelector('.offline-bar').after(notice);
}
async function api(path,body){if(body&&!navigator.onLine)throw Error('Connect to save or import recipes. Your ingredient checklist still works offline.');const options=body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:AbortSignal.timeout(path==='/api/import-images'?100000:12000)}:{signal:AbortSignal.timeout(5000)};const r=await fetch(path,{...options,redirect:'manual'});if(redirected(r))throw new AccessRedirect('Lolo’s Kitchen sign-in is required.');const data=await r.json();if(!r.ok)throw Error(data.error||'Request failed');return data}
function show(id){if(dirty&&!confirm('Leave without saving your recipe changes?'))return false;if(menuDirty&&id!=='menu'&&!confirm('Leave without saving your weekly menu?'))return false;if(activeVideoJob)stopVideoJob();importEpoch++;dirty=false;if(id!=='menu')menuDirty=false;document.body.dataset.view=id;['library','detail','editor','menu'].forEach(x=>$('#'+x).hidden=x!==id);if(id==='editor'||id==='detail')document.querySelectorAll('[data-nav]').forEach(b=>b.removeAttribute('aria-current'));message('');window.scrollTo(0,0);return true}
function recipeImage(r){if(r.photo&&/^data:image\/jpeg;base64,[A-Za-z0-9+/=]+$/.test(r.photo))return `<img src="${r.photo}" alt="${esc(r.title)}">`;return r.id==='juicy-smoked-turkey-breast'?'<img src="/assets/turkey.png" alt="Smoked turkey breast from the original recipe">':'<span aria-hidden="true">✳</span>'}
function pdfLink(r){return r.original_pdf?'/'+r.original_pdf.split('/').map(encodeURIComponent).join('/'):null}
async function load(){
 let snapshot;
 try{snapshot=await recipeStorage.get('snapshot')}catch{}
 try{
  const fresh=await api('/api/recipes');
  if(!Array.isArray(fresh))throw Error('Invalid recipe response');
  recipes=fresh;
  connectionNotice(false);
  try{sessionStorage.removeItem('recipe-access-recovery')}catch{}
  try{
   await offlineShellReady;
   snapshot={recipes:fresh,savedAt:new Date().toISOString()};
   await recipeStorage.set('snapshot',snapshot);
   $('#offline-state').textContent='Saved on this device · Updated '+new Date(snapshot.savedAt).toLocaleString();
  }catch{$('#offline-state').textContent='Recipes loaded online. Offline storage is unavailable or full.'}
 }catch(error){
  if(await recoverAccess(error))return;
  connectionNotice(true);
  if(!snapshot)throw Error('No saved recipes on this device yet. Connect once to save your cookbook.');
  recipes=snapshot.recipes;
  $('#offline-state').textContent='Viewing saved recipes · Last updated '+new Date(snapshot.savedAt).toLocaleString()+' · Imports and edits need a connection.';
 }
if(!categories.length)categories=await api('/categories.json');
const selected=$('#tag').value;$('#tag').innerHTML='<option value="">All categories</option>'+categories.map(t=>`<option>${esc(t)}</option>`).join('');$('#tag').value=selected;render()}
function recipeMeta(r){return `${r.total_minutes?esc(r.total_minutes)+' min · ':''}${r.ingredients.length} ingredients`}
function bindRecipeActions(scope){scope.querySelectorAll('[data-open]').forEach(b=>b.onclick=()=>detail(b.dataset.open));scope.querySelectorAll('[data-fav]').forEach(b=>b.onclick=()=>favorite(b.dataset.fav))}
function shelfCard(r){return `<article class="shelf-card"><button class="shelf-art" data-open="${esc(r.id)}" aria-label="Open ${esc(r.title)}">${recipeImage(r)}</button><div class="shelf-card-body"><button class="shelf-open" data-open="${esc(r.id)}">${esc(r.title)}</button><p>${recipeMeta(r)}</p><button class="shelf-favorite" data-fav="${esc(r.id)}" aria-label="${r.favorite?'Unfavorite':'Favorite'} ${esc(r.title)}" aria-pressed="${!!r.favorite}">${r.favorite?'♥':'♡'}</button></div></article>`}
function showAllFromShelf(tag=''){favorites=false;trash=false;$('#favorites').setAttribute('aria-pressed','false');$('#search').value='';$('#tag').value=tag;render();$('.recipes-heading').scrollIntoView({behavior:'smooth',block:'start'})}
function renderBrowseShelves(){const host=$('#browse-shelves'),query=$('#search').value.trim(),tag=$('#tag').value;if(trash||favorites||query||tag){host.hidden=true;host.innerHTML='';return}const active=recipes.filter(r=>!r.deleted);if(!active.length){host.hidden=true;host.innerHTML='';return}const groups=[{title:'Recently added',recipes:active.slice(0,8)}];const categoryGroups=categories.map(title=>({title,recipes:active.filter(r=>(r.tags||[]).includes(title))})).filter(group=>group.recipes.length).slice(0,3);groups.push(...categoryGroups);host.hidden=false;host.innerHTML=groups.map(group=>`<section class="browse-shelf"><div class="browse-shelf-head"><h2>${esc(group.title)}</h2><button class="shelf-see-all" data-shelf-tag="${esc(group.title==='Recently added'?'':group.title)}">See all <span aria-hidden="true">→</span></button></div><div class="browse-shelf-row" tabindex="0" aria-label="${esc(group.title)} recipes">${group.recipes.slice(0,8).map(shelfCard).join('')}</div></section>`).join('');bindRecipeActions(host);host.querySelectorAll('[data-shelf-tag]').forEach(b=>b.onclick=()=>showAllFromShelf(b.dataset.shelfTag))}
function render(){const q=$('#search').value.toLowerCase(),tag=$('#tag').value;let list=recipes.filter(r=>!!r.deleted===trash&&(!favorites||r.favorite)&&(!tag||(r.tags||[]).includes(tag))&&[r.title,...r.ingredients.map(i=>i.text),...(r.tags||[])].join(' ').toLowerCase().includes(q));if($('#sort').value==='name')list.sort((a,b)=>a.title.localeCompare(b.title));if($('#sort').value==='time')list.sort((a,b)=>(a.total_minutes??Infinity)-(b.total_minutes??Infinity));renderFilterState(list.length);renderBrowseShelves();$('#count').textContent=`(${recipes.filter(r=>!r.deleted).length})`;$('#cards').innerHTML=list.map(r=>`<article class="recipe-card"><button class="card-art" data-open="${esc(r.id)}" aria-label="Open ${esc(r.title)}">${recipeImage(r)}</button><div class="card-body"><span class="chip">${esc((r.tags||[]).join(' · ')||'From your collection')}</span><button class="card-open" data-open="${esc(r.id)}"><h3>${esc(r.title)}</h3></button><p>${r.total_minutes?esc(r.total_minutes)+' min':'Time not specified'} · ${r.ingredients.length} ingredients</p><div class="card-bottom"><span class="small">${esc(r.author||'Your kitchen notebook')}</span><button data-fav="${esc(r.id)}" aria-label="${r.favorite?'Unfavorite':'Favorite'} ${esc(r.title)}" aria-pressed="${!!r.favorite}">${r.favorite?'♥':'♡'}</button></div></div></article>`).join('')||'<p class="empty">No recipes here yet. Add a recipe or try another search.</p>';bindRecipeActions($('#cards'))}
async function favorite(id){try{let r=recipes.find(x=>x.id===id);await api('/api/recipes',{...r,favorite:!r.favorite});await load();if(!$('#detail').hidden)detail(id)}catch(e){message(e.message)}}
async function detail(id){current=recipes.find(r=>r.id===id);if(!current)return;const r=current;if(!show('detail'))return;$('#detail').innerHTML=`<button class="back" id="home">← Recipe shelf</button><div class="detail-photo">${recipeImage(r)}</div><div class="detail-top"><p class="eyebrow">${esc((r.tags||[]).join(' · ')||'A RECIPE TO KEEP')}</p><h1>${esc(r.title)}</h1><p class="metadata">${esc(r.author||'Your kitchen')} · ${r.servings?esc(r.servings)+' servings':'Servings not specified'} · ${r.total_minutes?esc(r.total_minutes)+' minutes':'Total time not specified'}</p><div class="actions"><button id="edit">Edit recipe</button><button id="detail-fav">${r.favorite?'♥ Favorited':'♡ Favorite'}</button><button id="print">Print recipe</button><button id="trash-recipe">${r.deleted?'Restore recipe':'Move to trash'}</button>${pdfLink(r)?`<a href="${esc(pdfLink(r))}" target="_blank" rel="noopener">Original PDF ↗</a>`:''}${/^https?:\/\//i.test(r.source_url||'')?`<a href="${esc(r.source_url)}" target="_blank" rel="noopener">Source ↗</a>`:''}</div></div>${r.import?.status==='awaiting_user_review'?'<div class="notice">Imported recipe · Open Edit recipe to review and save your version.</div>':''}<div class="recipe-jump"><button id="jump-ingredients">Ingredients ↓</button><button id="jump-directions" ${r.instructions.length?'':'hidden'}>Directions ↓</button></div><div class="recipe-layout"><aside class="ingredient-box"><h2>What you’ll need</h2><span class="small">Checkmarks stay on this device.</span><button id="reset-checklist" type="button">Reset checklist</button>${r.ingredients.map(i=>`<label class="check"><input type="checkbox"><span>${esc(i.text)}</span></label>`).join('')}</aside><div><h2>${r.instructions.length?'Let’s make it':'Ingredient-only recipe'}</h2><ol class="steps">${r.instructions.map(i=>`<li>${esc(i.text)}</li>`).join('')}</ol>${r.timing_notes?.length?`<h2>Timing notes</h2><ul>${r.timing_notes.map(t=>`<li>${esc(t)}</li>`).join('')}</ul>`:''}${r.notes?`<h2>Kitchen notes</h2><p class="notes">${esc(r.notes)}</p>`:''}</div></div>`;$('#home').onclick=()=>show('library');$('#edit').onclick=()=>editor(r);$('#detail-fav').onclick=()=>favorite(id);$('#print').onclick=()=>window.print();$('#trash-recipe').onclick=async()=>{try{await api('/api/recipes',{...r,deleted:!r.deleted});await load();show('library');message(r.deleted?'Recipe restored.':'Recipe moved to Trash. You can restore it anytime.')}catch(e){message(e.message)}};$('#jump-ingredients').onclick=()=>$('.ingredient-box').scrollIntoView({behavior:'smooth'});$('#jump-directions').onclick=()=>$('.steps').scrollIntoView({behavior:'smooth'});
 const boxes=[...$('#detail').querySelectorAll('.check input')];
 const key='checklist:'+r.id;
 // Include the exact ingredient list in the saved state so edits cannot check the wrong line.
 const signature=JSON.stringify(r.ingredients.map(i=>i.text));
 boxes.forEach(b=>b.disabled=true);
 let saved;
 try{saved=await recipeStorage.get(key)}catch{message('Checklist storage is unavailable. Checkmarks will not survive reopening.')}
 boxes.forEach((b,i)=>{b.checked=saved?.signature===signature&&!!saved.checked[i];b.disabled=false});
 let pending=Promise.resolve();
 const persist=()=>{const state={signature,checked:boxes.map(b=>b.checked)};pending=pending.then(()=>recipeStorage.set(key,state)).catch(()=>message('Could not save checkmarks on this device.'))};
 boxes.forEach(b=>b.onchange=persist);
 const reset=boxes[0]?.closest('.ingredient-box').querySelector('#reset-checklist');
 if(reset)reset.onclick=()=>{boxes.forEach(b=>b.checked=false);persist()};
}
function editor(r={}){if(!show('editor'))return;editing=structuredClone(r);form.reset();if(!r.id&&!r.import)$('#video-url').value='';resetRecipePages();renderSourcePhotos(r.source_photos);$('#photo-url-status').textContent='';$('#photo-preview').hidden=!r.photo;$('#photo-preview').src=r.photo||'';$('#import-panel').hidden=!!(r.id||r.import);chooseImportMethod('website');form.hidden=!(r.id||r.import);$('#edit-heading').textContent=r.id?'A little fine-tuning.':r.import?'Review your recipe.':'Add a recipe.';['title','servings','total_minutes','author','source_url','notes'].forEach(k=>form.elements[k].value=r[k]??'');['ingredients','instructions'].forEach(k=>form.elements[k].value=(r[k]||[]).map(i=>i.text).join('\n'));$('#category-options').innerHTML='<legend>Categories</legend>'+categories.map(t=>`<label><input type="checkbox" name="category" value="${esc(t)}" ${(r.tags||[]).some(x=>x.toLowerCase()===t.toLowerCase())?'checked':''}>${esc(t)}</label>`).join('');$('#review-notice').hidden=!r.import;$('#review-notice').textContent=(r.import?.issues||[]).join('\n');$('#source-text').textContent=r.import?.raw_text||r.import?.raw_pages?.map(p=>p.text).join('\n\n')||'';$('#edit-pdf').hidden=!pdfLink(r);if(pdfLink(r))$('#edit-pdf').href=pdfLink(r);if(r.import&&!r.id)dirty=true;return true}
async function extract(body){message('Reading your recipe…');$('#extract').disabled=true;$('#extract-chatgpt').disabled=true;$('#pdf').disabled=true;try{const r=await api('/api/import',body);dirty=false;editor(r);message('Draft ready. Check the title, line breaks, ingredients, and directions before saving.')}catch(e){message(e.message)}finally{$('#extract').disabled=false;$('#extract-chatgpt').disabled=false;$('#pdf').disabled=false}}
$('#add').onclick=()=>editor();$('.brand').onclick=e=>{e.preventDefault();show('library')};$('#cancel').onclick=()=>show('library');$('#search').oninput=render;$('#sort').onchange=render;$('#tag').onchange=render;$('#favorites').onclick=()=>{favorites=!favorites;$('#favorites').setAttribute('aria-pressed',favorites);render()};$('#extract').onclick=()=>{if(!$('#paste').value.trim()){message('Paste your recipe text first.');$('#paste').focus();return}extract({text:$('#paste').value})};$('#extract-chatgpt').onclick=()=>{if(!$('#paste-chatgpt').value.trim()){message('Paste the ChatGPT recipe first.');$('#paste-chatgpt').focus();return}extract({text:$('#paste-chatgpt').value})};$('#pdf').onchange=async e=>{const file=e.target.files[0];if(!file)return;if(file.size>10_000_000){message('Choose a PDF smaller than 10 MB.');return}const reader=new FileReader();reader.onload=()=>extract({pdf:reader.result.split(',')[1]});reader.onerror=()=>message('Could not read this file.');reader.readAsDataURL(file)};
form.onsubmit=async e=>{e.preventDefault();const r={...editing};['title','servings','author','source_url','notes'].forEach(k=>r[k]=form.elements[k].value.trim());r.total_minutes=form.elements.total_minutes.value===''?null:Number(form.elements.total_minutes.value);r.tags=[...form.querySelectorAll('[name=category]:checked')].map(x=>x.value);['ingredients','instructions'].forEach(k=>r[k]=form.elements[k].value.split('\n').map(t=>t.trim()).filter(Boolean).map((text,i)=>({...((editing[k]||[]).find(x=>x.text===text)||{}),text,...(k==='instructions'?{number:i+1}:{})})));if(r.import){r.import={...r.import,status:'reviewed'};if(r.import.method==='instagram_reel')delete r.import.raw_text}$('#save').disabled=true;try{const saved=await api('/api/recipes',r);dirty=false;await load();detail(saved.id);message('Recipe saved to your recipe book.')}catch(e){message(e.message)}finally{$('#save').disabled=false}};
load().then(()=>{if(location.pathname==='/instagram'){editor();chooseImportMethod('video')}else if(location.pathname==='/menu')openMenu()}).catch(e=>message('Could not load the recipe book: '+e.message));
if(document.modelContext?.registerTool){
 const lifecycle=new AbortController();
 const register=tool=>{try{Promise.resolve(document.modelContext.registerTool(tool,{signal:lifecycle.signal})).catch(()=>{})}catch{}};
 register({name:'list_saved_recipes',description:'List saved recipe titles and IDs from this recipe book.',inputSchema:{type:'object',properties:{},additionalProperties:false},annotations:{readOnlyHint:true,untrustedContentHint:true},execute:async()=>{await load();return recipes.map(r=>({id:r.id,title:r.title}))}});
 register({name:'open_saved_recipe',description:'Open an existing recipe and ingredient checklist without editing it.',inputSchema:{type:'object',properties:{id:{type:'string'}},required:['id'],additionalProperties:false},annotations:{readOnlyHint:false,untrustedContentHint:true},execute:async input=>{if(!input||typeof input.id!=='string')throw Error('Recipe ID is required');await load();if(!recipes.some(r=>r.id===input.id))throw Error('Recipe not found');detail(input.id);return {opened:input.id}}});
 window.addEventListener('pagehide',()=>lifecycle.abort(),{once:true});
}

function renderFilterState(count){
 const tag=$('#tag').value, query=$('#search').value.trim();
 $('#favorites').setAttribute('aria-pressed',favorites);
 if(!$('#library').hidden)document.querySelectorAll('[data-nav]').forEach(b=>{if(b.dataset.nav===(favorites?'favorites':query?'search':'home'))b.setAttribute('aria-current','page');else b.removeAttribute('aria-current')});
 $('#clear-filters').hidden=!(query||tag||favorites);
 $('#show-trash').textContent=trash?'Back to cookbook':'Trash';
 $('.recipes-heading').textContent=trash?'Trash':'All recipes';
 $('#filter-summary').textContent=count+' '+(count===1?'recipe':'recipes')+(trash?' in Trash':'')+(favorites?' · Favorites':'')+(tag?' · '+tag:'')+(query?' · Search: “'+query+'”':'');
}
const menuDayNames=['Saturday','Sunday','Monday','Tuesday','Wednesday','Thursday','Friday'];
function saturdayOf(date){const day=new Date(date.getFullYear(),date.getMonth(),date.getDate());day.setDate(day.getDate()-(day.getDay()+1)%7);return day}
function menuKey(date){return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`}
function menuHasContent(menu){return [...menu.days,menu.snacks,menu.lunches,menu.sweet_treats].some(value=>value.trim())}
function renderMenuDisplay(menu){
 const dayRows=menuDayNames.map((name,index)=>{
  const meal=menu.days[index].trim();
  return `<div class="menu-display-day"><h3>${name}</h3><p>${meal?esc(meal):'<span class="menu-empty">—</span>'}</p></div>`;
 }).join('');
 const extraRows=[['Snacks',menu.snacks],['Lunches',menu.lunches],['Sweet treats',menu.sweet_treats]].map(([title,value])=>{
  const lines=value.split(/\r?\n/).map(line=>line.trim()).filter(Boolean);
  return `<section class="menu-display-extra"><h3>${title}</h3>${lines.length?lines.map(line=>`<p>${esc(line)}</p>`).join(''):'<p class="menu-empty">—</p>'}</section>`;
 }).join('');
 $('#menu-display-content').innerHTML=`<div class="menu-display-days">${dayRows}</div><div class="menu-display-extras">${extraRows}</div>`;
 $('#menu-display').hidden=false;$('#menu-form').hidden=true;$('#menu-intro').hidden=true;
}
async function openMenu(week=saturdayOf(new Date())){
 if(menuDirty&&!confirm('Leave without saving your weekly menu?'))return;
 if($('#menu').hidden&&!show('menu'))return;
 document.querySelectorAll('[data-nav]').forEach(b=>{if(b.dataset.nav==='menu')b.setAttribute('aria-current','page');else b.removeAttribute('aria-current')});
 menuWeek=week;menuDirty=false;$('#menu-status').textContent='Loading menu…';
 const end=new Date(week);end.setDate(end.getDate()+6);
 $('#menu-heading').textContent=`${week.toLocaleDateString(undefined,{month:'short',day:'numeric'})} – ${end.toLocaleDateString(undefined,{month:'short',day:'numeric',year:'numeric'})}`;
 $('#menu-form').hidden=true;$('#menu-display').hidden=true;
 try{
  const menu=await api('/api/weekly-menu/'+menuKey(week));
  if(menuKey(menuWeek)!==menu.week_start)return;
  $('#menu-days').innerHTML=menuDayNames.map((name,day)=>{const date=new Date(week);date.setDate(date.getDate()+day);return `<label class="menu-day"><span>${name} <small>${date.toLocaleDateString(undefined,{month:'short',day:'numeric'})}</small></span><textarea data-day="${day}" maxlength="1000" rows="2" placeholder="Add this day's menu">${esc(menu.days[day])}</textarea></label>`}).join('');
  $('#menu-snacks').value=menu.snacks;
  $('#menu-lunches').value=menu.lunches;
  $('#menu-sweet-treats').value=menu.sweet_treats;
  if(menuHasContent(menu))renderMenuDisplay(menu);
  else{$('#menu-form').hidden=false;$('#menu-intro').hidden=false}
  $('#menu-status').textContent='';
 }catch(error){$('#menu-status').textContent=error.message||'Could not load this menu.'}
}
$('#menu-edit').onclick=()=>{$('#menu-display').hidden=true;$('#menu-form').hidden=false;$('#menu-intro').hidden=false;$('#menu-status').textContent='';$('#menu-days textarea').focus()};
$('#menu-form').addEventListener('input',()=>{menuDirty=true;$('#menu-status').textContent='Unsaved changes'});
$('#menu-form').onsubmit=async event=>{
 event.preventDefault();const button=$('#menu-form button[type=submit]');button.disabled=true;$('#menu-status').textContent='Saving…';
 const days=Array(7).fill('');
 $('#menu-days').querySelectorAll('textarea').forEach(input=>{days[Number(input.dataset.day)]=input.value});
 const weekKey=menuKey(menuWeek);
 try{const saved=await api('/api/weekly-menu',{week_start:weekKey,days,snacks:$('#menu-snacks').value,lunches:$('#menu-lunches').value,sweet_treats:$('#menu-sweet-treats').value});if(menuKey(menuWeek)!==weekKey)return;menuDirty=false;if(menuHasContent(saved))renderMenuDisplay(saved);$('#menu-status').textContent='Saved for this week.'}
 catch(error){$('#menu-status').textContent=error.message||'Could not save the menu.'}
 finally{button.disabled=false}
};
$('#menu-prev').onclick=()=>{const week=new Date(menuWeek);week.setDate(week.getDate()-7);openMenu(week)};
$('#menu-next').onclick=()=>{const week=new Date(menuWeek);week.setDate(week.getDate()+7);openMenu(week)};
$('#menu-today').onclick=()=>openMenu(saturdayOf(new Date()));
$('#menu-link').onclick=()=>openMenu();
$('#clear-filters').onclick=()=>{favorites=false;$('#tag').value='';$('#search').value='';render();$('#search').focus()};
document.querySelectorAll('[data-nav]').forEach(b=>b.onclick=()=>{
 const action=b.dataset.nav;
 if(action==='menu'){openMenu();return}
 if(action==='add'){editor();return}
 if(!show('library'))return;trash=false;favorites=action==='favorites';$('#favorites').setAttribute('aria-pressed',favorites);$('#tag').value='';$('#search').value='';render();
 if(action==='search'){$('#search').focus();$('#search').scrollIntoView({block:'center'})}
});

$('#sync-recipes').onclick=async()=>{const b=$('#sync-recipes');b.disabled=true;try{await load()}catch(e){message(e.message)}finally{b.disabled=false}};
window.addEventListener('offline',()=>{$('#offline-state').textContent='Offline · Reading saved recipes. Checkmarks stay on this device.'});
window.addEventListener('online',()=>load().catch(e=>message(e.message)));
$('#import-url').onclick=async()=>{
 const button=$('#import-url'), input=$('#recipe-url');
 if(!input.value.trim()||!input.checkValidity()){input.reportValidity();message('Enter a complete website URL starting with https://');return}
 try{
  const link=new URL(input.value.trim());
  if(link.protocol==='https:'&&['instagram.com','www.instagram.com'].includes(link.hostname)&&/^\/reel\/[A-Za-z0-9_-]{5,64}\/?$/.test(link.pathname)){
   $('#video-url').value=input.value.trim();chooseImportMethod('video');$('#import-video').click();return;
  }
 }catch{}
 button.disabled=true;message('Reading the recipe website…');$('#url-candidates').hidden=true;
 try{
  const result=await api('/api/import-url',{url:input.value.trim()});
  if(result.candidates.length===1){await openImportedRecipe(result.candidates[0])}
  else{
   const box=$('#url-candidates');box.hidden=false;box.innerHTML='<p>Choose the recipe to import:</p>'+result.candidates.map((r,i)=>`<button type="button" data-candidate="${i}">${esc(r.title||'Untitled recipe')}</button>`).join('');
   box.querySelectorAll('button').forEach(b=>b.onclick=async()=>{box.hidden=true;await openImportedRecipe(result.candidates[Number(b.dataset.candidate)])});
   message('Several recipes were found. Choose one above.');
  }
 }catch(e){message(e.message)}finally{button.disabled=false}
};

form.addEventListener('input',()=>{dirty=true});
$('#paste').addEventListener('input',()=>{dirty=true});
$('#paste-chatgpt').addEventListener('input',()=>{dirty=true});
window.addEventListener('beforeunload',e=>{if(dirty||menuDirty){e.preventDefault();e.returnValue=''}});
$('#show-trash').onclick=()=>{trash=!trash;$('#show-trash').textContent=trash?'Back to cookbook':'Trash';favorites=false;$('#search').value='';$('#tag').value='';render()};
$('#recipe-photo').onchange=async e=>{
 const file=e.target.files[0];if(!file)return;
 if(file.size>20_000_000){message('Choose a photo smaller than 20 MB.');return}
 const url=URL.createObjectURL(file);const img=new Image();
 try{await new Promise((resolve,reject)=>{img.onload=resolve;img.onerror=reject;img.src=url});
  const scale=Math.min(1,1400/Math.max(img.width,img.height));const canvas=document.createElement('canvas');canvas.width=Math.round(img.width*scale);canvas.height=Math.round(img.height*scale);canvas.getContext('2d').drawImage(img,0,0,canvas.width,canvas.height);
  editing.photo=canvas.toDataURL('image/jpeg',0.82);$('#photo-preview').src=editing.photo;$('#photo-preview').hidden=false;dirty=true;
 }catch{message('This photo format could not be read. Try JPEG or PNG.')}finally{URL.revokeObjectURL(url)}
};
$('#remove-photo').onclick=()=>{editing.photo=null;$('#photo-preview').hidden=true;dirty=true};

async function openImportedRecipe(recipe){
 if(recipe.image_url){message('Downloading the recipe photo…');try{const result=await api('/api/import-photo',{url:recipe.image_url});if(result.photo)recipe.photo=result.photo;else recipe.import.issues.push(result.warning)}catch{recipe.import.issues.push('The photo could not be downloaded. You can add one manually.')}}
 editor(recipe);message('Website recipe ready to review. Choose categories and save when ready.');
}

$('#download-photo').onclick=async()=>{
 const input=$('#photo-url'),button=$('#download-photo'),status=$('#photo-url-status');
 let url;try{url=new URL(input.value.trim());if(!['http:','https:'].includes(url.protocol))throw Error()}catch{status.textContent='Paste a complete direct image link starting with https://';input.focus();return}
 const target=editing;
 button.disabled=true;$('#save').disabled=true;$('#recipe-photo').disabled=true;$('#remove-photo').disabled=true;
 status.textContent='Downloading photo…';
 try{
  const result=await api('/api/import-photo',{url:url.href});
  if(editing!==target)return;
  if(!result.photo)throw Error('This image could not be downloaded. Try a direct image link or upload a photo file.');
  editing.photo=result.photo;$('#photo-preview').src=result.photo;$('#photo-preview').hidden=false;dirty=true;
  status.textContent='Photo ready. Save the recipe to keep it.';input.value='';
 }catch(error){if(editing===target)status.textContent=error.message}
 finally{button.disabled=false;$('#save').disabled=false;$('#recipe-photo').disabled=false;$('#remove-photo').disabled=false}
};

function chooseImportMethod(method){document.querySelectorAll('[data-method]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.method===method)));document.querySelectorAll('[data-import-pane]').forEach(p=>p.hidden=p.dataset.importPane!==method);form.hidden=method!=='manual';}
document.querySelectorAll('[data-method]').forEach(b=>b.onclick=()=>{if(activeVideoJob&&b.dataset.method!=='video')stopVideoJob();chooseImportMethod(b.dataset.method);message('')});

function stopVideoJob(){
 const job=activeVideoJob;activeVideoJob=null;$('#cancel-video').hidden=true;$('#import-video').disabled=false;
 if(job)fetch(`/api/import-video/jobs/${job.id}/cancel`,{method:'POST',headers:{'Content-Type':'application/json','X-Import-Token':job.token},body:'{}',keepalive:true}).catch(()=>{});
}
$('#cancel-video').onclick=()=>{stopVideoJob();importEpoch++;message('Video import canceled.');};
window.addEventListener('pagehide',()=>{if(activeVideoJob)stopVideoJob()});
$('#import-video').onclick=async()=>{
 const input=$('#video-url'),button=$('#import-video');
 if(!input.value.trim()||!input.checkValidity()){input.reportValidity();message('Paste a complete Instagram Reel URL.');return;}
 if(!navigator.onLine){message('Connect to import a video. Your saved recipes still work offline.');return;}
 button.disabled=true;message('Checking video link…');
 const epoch=importEpoch;
 try{
  const created=await api('/api/import-video',{url:input.value.trim()});
  if(epoch!==importEpoch)return;
  activeVideoJob={id:created.job_id,token:created.token};$('#cancel-video').hidden=false;
  const labels={queued:'Waiting for the video importer…',downloading:'Retrieving video and caption…',transcribing:'Extracting audio and transcribing speech…',extracting_text:'Reading on-screen text…',interpreting:'Organizing recipe…'};
  const deadline=Date.now()+20*60*1000;
  while(activeVideoJob&&epoch===importEpoch&&Date.now()<deadline){
   const response=await fetch(`/api/import-video/jobs/${activeVideoJob.id}`,{headers:{'X-Import-Token':activeVideoJob.token},cache:'no-store',signal:AbortSignal.timeout(10000)});
   const job=await response.json();if(!response.ok)throw Error(job.error||'Video import status could not be read.');
   if(!activeVideoJob||epoch!==importEpoch)return;
   if(job.state==='completed'){
    activeVideoJob=null;$('#cancel-video').hidden=true;button.disabled=false;
    dirty=false;editor(job.result);message('Video draft ready. Check the evidence and edit any missing details before saving.');return;
   }
   if(job.state==='failed'||job.state==='canceled')throw Error(job.error||'Video import canceled.');
   message(labels[job.state]||'Processing video…');
   await new Promise(resolve=>setTimeout(resolve,2000));
  }
  if(activeVideoJob&&epoch===importEpoch)throw Error('Video import timed out. Try a shorter Reel.');
 }catch(error){if(epoch===importEpoch)message(error.message||'Video import failed.');}
 finally{if(epoch===importEpoch&&activeVideoJob)stopVideoJob();button.disabled=false;}
};

let recipePages=[];
function renderSourcePhotos(pages){
 const box=$('#source-photos');box.replaceChildren();
 for(const [i,src] of (Array.isArray(pages)?pages:[]).entries()){
  if(typeof src!=='string'||!/^data:image\/jpeg;base64,[A-Za-z0-9+/=]+$/.test(src))continue;
  const details=document.createElement('details'),summary=document.createElement('summary'),img=document.createElement('img');
  summary.textContent=`Original recipe photo · page ${i+1}`;img.src=src;img.alt=`Original recipe page ${i+1}`;
  details.append(summary,img);box.append(details);
 }
}
function resetRecipePages(){recipePages=[];$('#recipe-pages').value='';$('#page-previews').replaceChildren();$('#import-images').disabled=true;}
$('#recipe-pages').onchange=async e=>{
 const files=[...e.target.files];recipePages=[];$('#page-previews').replaceChildren();$('#import-images').disabled=true;
 if(!files.length)return;
 if(files.length>4){message('Choose up to 4 photos at a time.');return;}
 const controls=[...$('#import-panel').querySelectorAll('button,input'),$('#cancel')];
 const states=controls.map(c=>c.disabled);controls.forEach(c=>c.disabled=true);
 try{
  for(const [index,file] of files.entries()){
   if(file.size>20_000_000)throw Error('Each photo must be smaller than 20 MB.');
   message(`Preparing photo ${index+1} of ${files.length}…`);
   const url=URL.createObjectURL(file),img=new Image();
   try{
    await new Promise((resolve,reject)=>{img.onload=resolve;img.onerror=()=>reject(Error('This photo format could not be opened. Try a JPEG or PNG screenshot.'));img.src=url;});
    let scale=Math.min(1,2000/Math.max(img.width,img.height)),page='';
    for(let attempt=0;attempt<5;attempt++){
     const canvas=document.createElement('canvas');canvas.width=Math.max(1,Math.round(img.width*scale));canvas.height=Math.max(1,Math.round(img.height*scale));
     const ctx=canvas.getContext('2d');ctx.fillStyle='white';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.drawImage(img,0,0,canvas.width,canvas.height);
     page=canvas.toDataURL('image/jpeg',0.82);
     if(page.length<=2_500_000)break;
     scale*=0.78;
    }
    if(page.length>2_500_000)throw Error('This photo is still too detailed. Use a screenshot or crop to the recipe and try again.');
    recipePages.push(page);
   }finally{URL.revokeObjectURL(url);}
  }
  for(const [i,src] of recipePages.entries()){
   const figure=document.createElement('figure'),img=document.createElement('img'),caption=document.createElement('figcaption');
   img.src=src;img.alt=`Selected recipe page ${i+1}`;caption.textContent=`Page ${i+1} · ${files[i].name}`;figure.append(img,caption);$('#page-previews').append(figure);
  }
  dirty=true;message('Photos ready. Check the page order, then choose Read recipe photos.');
 }catch(error){recipePages=[];message(error.message);}
 finally{controls.forEach((c,i)=>c.disabled=states[i]);$('#import-images').disabled=!recipePages.length;}
};
$('#import-images').onclick=async()=>{
 if(!recipePages.length)return;
 const epoch=importEpoch;
 const controls=[...$('#import-panel').querySelectorAll('button,input'),$('#cancel')];
 const states=controls.map(c=>c.disabled);controls.forEach(c=>c.disabled=true);
 message('Reading your recipe photos… This can take about a minute.');
 try{const result=await api('/api/import-images',{images:recipePages});if(epoch!==importEpoch)return;dirty=false;editor(result);message('Draft ready. Compare the recipe with the original photos, then save.');}
 catch(error){message(error.name==='TimeoutError'?'Reading timed out. Try fewer photos at once. Your photos are still selected.':error.message);}
 finally{controls.forEach((c,i)=>c.disabled=states[i]);$('#import-images').disabled=!recipePages.length;}
};
