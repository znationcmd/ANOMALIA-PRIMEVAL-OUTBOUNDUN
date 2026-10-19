import {ITEM_DEFS,EQUIPMENT_SLOTS,capacity,weight,warmth,protection,equip,unequip,consume} from './systems.js';
import {SLOT_LABELS,compartments,itemSize,syncInventory,moveStack,takeInHands,splitStack,mergeStacks,dropStack,nearbyDrops,pickupDrop,sortInventory} from './inventory.js';
import {survivorPreview} from './survivor-preview.js';
const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const paths={
 weapon:'M4 10h17v5H11v8H7v-8H4z M15 6h7v3h-7z',
 ammo:'M7 9V5l3-3 3 3v4z M7 11h6v14H7z M18 9V5l3-3 3 3v4z M18 11h6v14h-6z',
 drink:'M12 3h8v5l3 4v15H9V12l3-4z M12 17h8',
 food:'M5 13c0-8 8-11 11-5 5-5 12-1 11 5-1 7-9 13-11 14-2-1-10-7-11-14z',
 raw:'M4 19c2-9 8-13 15-12 8 2 8 11 3 16-5 5-13 5-18-4z M16 12c-5 0-7 6-3 8 5 3 10-8 3-8z',
 medical:'M5 8h22v19H5z M11 8V4h10v4 M14 12h4v4h4v4h-4v4h-4v-4h-4v-4h4z',
 material:'M4 10l12-6 12 6v15l-12 5L4 25z M4 10l12 6 12-6 M16 16v14',
 clothing:'M10 5l6 3 6-3 8 7-5 6-4-3v15H11V15l-4 3-5-6z',
 tool:'M5 28L23 5l5 4L10 31z M13 6c6-4 11-4 17 0',
 key:'M12 14a7 7 0 1 1 3-7l14 14-4 4-3-3-3 1-2-4z',
 saddle:'M6 9l6 3h8l6-3v12l-7 5h-6l-7-5z',
 taming:'M6 10l9-5 11 6-2 14H8z M11 15h10 M11 20h10',
};
export function itemIcon(id){const k=ITEM_DEFS[id]?.kind|| (id.startsWith('key_')?'key':'material');return `<svg class="item-icon" viewBox="0 0 32 34" aria-hidden="true"><path d="${paths[k]||paths.material}"/></svg>`}
export function inventoryInterface({state,panel,body,title,save,notice,open,recipes,actions,siteInfo}){
 let selection=null,search='',category='all',tab='inventory',sort='name',disposePreview=null,lastClickId=null,lastClickTime=0;
 function cleanup(){disposePreview?.();disposePreview=null;panel.classList.remove('inventory-mode');body.onclick=null;body.oninput=null;body.ondragstart=null;body.ondragover=null;body.ondrop=null;body.ondblclick=null;body.oncontextmenu=null;}
 function stackButton(t,ground=false){
  const [w,h]=itemSize(t.id,t.rotated),def=ITEM_DEFS[t.id],label=def?.label||t.id;
  if(search&&!label.toLowerCase().includes(search.toLowerCase()))return '';
  if(category!=='all'&&def?.kind!==category)return '';
  return `<button class="cargo-item ${selection===t.uid?'selected':''} ${ground?'ground-item':''}" ${ground?'':'draggable="true"'} data-stack="${escape(t.uid)}" ${ground?'data-ground="1"':`style="grid-column:${t.x+1}/span ${w};grid-row:${t.y+1}/span ${h}"`} title="${escape(label)} · ${((def?.weight||.03)*t.count).toFixed(2)} kg">${itemIcon(t.id)}<span class="cargo-name">${escape(label)}</span><b>×${t.count}</b></button>`;
 }
 function grid(c){const cells=Array.from({length:c.width*c.height},(_,i)=>`<div class="cargo-cell" data-container="${c.id}" data-x="${i%c.width}" data-y="${Math.floor(i/c.width)}" style="grid-column:${i%c.width+1};grid-row:${Math.floor(i/c.width)+1}"></div>`).join('');return `<section class="cargo-container"><h3>${escape(c.label)} <small>${state.inventoryStacks.filter(t=>t.container===c.id).reduce((n,t)=>{const [w,h]=itemSize(t.id,t.rotated);return n+w*h},0)} / ${c.width*c.height}</small></h3><div class="cargo-grid" data-container="${c.id}" style="--cols:${c.width};--rows:${c.height}">${cells}${state.inventoryStacks.filter(t=>t.container===c.id).map(t=>stackButton(t)).join('')}</div></section>`}
 function render(){
  disposePreview?.();disposePreview=null;syncInventory(state);panel.classList.add('inventory-mode');title.textContent='ANOMALIA · ÉQUIPEMENT';
  const wt=weight(state),cap=capacity(state),selected=state.inventoryStacks.find(t=>t.uid===selection)||nearbyDrops(state).find(t=>t.uid===selection),hand=state.inventoryStacks.find(t=>t.container==='hands'),near=siteInfo?.();
  body.innerHTML=`<nav class="inventory-tabs">${[['inventory','Inventaire'],['craft','Fabrication'],['survival','Survie'],['creatures','Créatures']].map(([id,label])=>`<button data-tab="${id}" class="${tab===id?'active':''}">${label}</button>`).join('')}<span class="carry ${wt>cap?'overweight':''}">${wt.toFixed(1)} / ${cap.toFixed(1)} kg</span></nav>
  <div class="inventory-toolbar"><label>Rechercher<input id="inventorySearch" value="${escape(search)}" placeholder="Nom d’un objet…"></label><label>Catégorie<select id="inventoryCategory">${[['all','Tous'],['weapon','Armes'],['ammo','Munitions'],['clothing','Vêtements'],['food','Nourriture'],['drink','Boissons'],['medical','Soins'],['material','Matériaux'],['tool','Outils'],['key','Clés'],['taming','Apprivoisement']].map(([v,l])=>`<option value="${v}" ${category===v?'selected':''}>${l}</option>`).join('')}</select></label><button data-action="sort">Trier : ${sort==='name'?'nom':'poids'}</button><button data-action="merge">Regrouper les piles</button><button data-action="take-all">Tout récupérer</button><button data-action="drop-all">Tout déposer</button></div>
  ${tab==='inventory'?`<div class="survival-inventory"><section class="vicinity"><h3>À PROXIMITÉ <small>5 m</small></h3><div class="ground-grid">${nearbyDrops(state).map(t=>stackButton(t,true)).join('')||'<p class="inventory-empty">Aucun objet posé au sol.</p>'}</div>${near?`<div class="nearby-site"><b>${escape(near.label)}</b><p>${near.locked?'Clé requise':near.collected?'Déjà fouillé':'Accessible'}</p><button data-action="site" ${near.locked||near.collected?'disabled':''}>Ouvrir / fouiller</button></div>`:''}<p class="inventory-tip">Glisse un objet ici pour le poser au sol. Double-clique sur un objet pour le récupérer.</p><div class="drop-zone" data-container="ground">DÉPOSER AU SOL</div></section>
  <section class="survivor-column"><h3>SURVIVANT <small>Équipement actuel</small></h3><div id="survivorPreview" aria-label="Aperçu 3D de votre équipement"></div><p class="preview-hint">Glisser pour tourner</p><section class="hands-panel"><h3>MAINS</h3><div class="hands-drop" data-container="hands">${hand?`<button data-stack="${hand.uid}" class="hands-item" draggable="true">${itemIcon(hand.id)}<span>${escape(ITEM_DEFS[hand.id]?.label||hand.id)} × ${hand.count}</span></button>`:'Glisser un objet dans les mains'}</div></section><div class="survivor-stats">${[['Santé',state.health],['Endurance',state.stamina],['Nourriture',state.hunger],['Eau',state.thirst]].map(([l,n])=>`<div><span>${l}</span><meter min="0" max="100" value="${n}"></meter><b>${Math.round(n)}</b></div>`).join('')}</div></section>
  <section class="equipment-column"><h3>ÉQUIPEMENT</h3><div class="equipment-slots">${EQUIPMENT_SLOTS.map(slot=>`<div class="equipment-card" data-container="equip:${slot}"><span>${SLOT_LABELS[slot]}</span>${state.equipment[slot]?`${itemIcon(state.equipment[slot])}<b>${escape(ITEM_DEFS[state.equipment[slot]]?.label)}</b><button data-unequip="${slot}">Retirer</button>`:'<b>Vide</b>'}</div>`).join('')}</div>${compartments(state).map(grid).join('')}${state.inventoryStacks.some(t=>t.container==='overflow')?`<section class="overflow"><h3>À RANGER · objets conservés</h3><div class="ground-grid">${state.inventoryStacks.filter(t=>t.container==='overflow').map(t=>stackButton(t,true)).join('')}</div></section>`:''}</section></div>`:''}
  ${tab==='craft'?`<section class="crafting-grid">${recipes.map(r=>`<article class="recipe-card">${itemIcon(r.id)}<div><h3>${escape(r.label)}</h3><p>${Object.entries(r.cost).map(([id,n])=>`${n} ${escape(ITEM_DEFS[id]?.label||id)} <b class="${(state.inventory[id]||0)>=n?'enough':'missing'}">(${state.inventory[id]||0})</b>`).join(' · ')}</p><button data-recipe="${r.id}" ${Object.entries(r.cost).some(([id,n])=>(state.inventory[id]||0)<n)?'disabled':''}>Fabriquer</button></div></article>`).join('')}</section>`:''}
  ${tab==='survival'?`<section class="survival-detail"><h3>ÉTAT DU SURVIVANT</h3><p>Température : ${Number(state.temperature).toFixed(1)} °C · Chaleur : ${warmth(state)} · Protection : ${protection(state)}</p><p>Maladie : ${escape(state.illness||'Aucune')}</p><p>Les aliments crus nécessitent une cuisson près d’un feu.</p><div class="inventory-toolbar">${[['fish','Pêcher'],['campfire','Construire un feu'],['cook-meat','Cuire la viande'],['cook-fish','Cuire le poisson'],['tranq','Mode fléchettes']].map(([a,l])=>`<button data-action="${a}">${l}</button>`).join('')}</div></section>`:''}
  ${tab==='creatures'?`<section class="creature-grid"><h3>CRÉATURES APPRIVOISÉES</h3>${state.tamed.length?state.tamed.map(t=>`<article><h3>${escape(t.name||t.type)}</h3><p>${t.hasSaddle?'Sellé':'Sans selle'}</p></article>`).join(''):'<p>Aucune créature apprivoisée. Endors un dinosaure avec les fléchettes, puis nourris-le avec les croquettes adaptées.</p>'}</section>`:''}
  <section class="item-details">${selected?`<div>${itemIcon(selected.id)}<b>${escape(ITEM_DEFS[selected.id]?.label||selected.id)}</b><span>${((ITEM_DEFS[selected.id]?.weight||.03)*selected.count).toFixed(2)} kg · ×${selected.count}</span></div><label>Quantité<input id="inventoryAmount" type="number" min="1" max="${selected.count}" value="1"></label><button data-action="hands">Mains</button><button data-action="use">Utiliser / équiper</button><button data-action="split">Séparer</button><button data-action="half">Moitié</button><button data-action="rotate">Tourner</button><button data-action="transfer">Transférer</button><label>Raccourci<select id="quickSlot">${Array.from({length:10},(_,i)=>`<option value="${i}">${(i+1)%10}</option>`).join('')}</select></label><button data-action="quick">Assigner</button>`:'Sélectionne un objet pour afficher ses actions. Glisser-déposer · double-clic : mains / récupérer.'}</section>
  <div class="inventory-quickbar">${Array.from({length:10},(_,i)=>`<button data-quick="${i}" data-container="quick:${i}"><kbd>${(i+1)%10}</kbd>${state.quickbar[i]?itemIcon(state.quickbar[i]):''}<span>${escape(ITEM_DEFS[state.quickbar[i]]?.label||'Vide')}</span></button>`).join('')}</div>`;
  if(tab==='inventory')disposePreview=survivorPreview(body.querySelector('#survivorPreview'),state);
  bind();open();
 }
 const result=r=>{if(r?.message)notice(r.message);save();render()};
 function action(name){
  syncInventory(state);const t=state.inventoryStacks.find(t=>t.uid===selection),ground=nearbyDrops(state).find(t=>t.uid===selection),amount=Math.max(1,Math.floor(Number(body.querySelector('#inventoryAmount')?.value)||1));
  if(name==='sort'){sort=sort==='name'?'weight':'name';return result(sortInventory(state,sort))}
  if(name==='merge')return result(mergeStacks(state));
  if(name==='take-all'){let n=0;for(const d of [...nearbyDrops(state)]){if(pickupDrop(state,d.uid).ok)n++}return result({message:n+' pile(s) récupérée(s).'})}
  if(name==='drop-all'){for(const t of [...state.inventoryStacks])dropStack(state,t.uid,t.count);return result({message:'Objets déposés au sol.'})}
  if(name==='site'){actions.site();return result()}
  if(actions[name])return result(actions[name]());
  if(name==='transfer')return result(ground?pickupDrop(state,ground.uid):t?dropStack(state,t.uid,amount):{message:'Sélectionne un objet.'});
  if(!t)return notice('Sélectionne un objet de ton inventaire.');
  if(name==='hands')return result(takeInHands(state,t.uid));
  if(name==='split'||name==='half')return result(splitStack(state,t.uid,name==='half'?Math.floor(t.count/2):amount));
  if(name==='rotate')return result(moveStack(state,t.uid,t.container,t.x,t.y,true));
  if(name==='use'){const def=ITEM_DEFS[t.id];return result(def?.kind==='clothing'?equip(state,t.id):def?.kind==='weapon'||def?.kind==='tool'?takeInHands(state,t.uid):consume(state,t.id))}
  if(name==='quick'){state.quickbar[Number(body.querySelector('#quickSlot').value)]=t.id;return result({message:'Raccourci assigné.'})}
 }
 function bind(){
  body.onclick=e=>{const b=e.target.closest('button');if(!b)return;
   if(b.dataset.stack){const id=b.dataset.stack,now=performance.now();selection=id;
    if(lastClickId===id&&now-lastClickTime<350){lastClickId=null;const ground=nearbyDrops(state).find(t=>t.uid===id);return result(ground?pickupDrop(state,id):takeInHands(state,id))}
    lastClickId=id;lastClickTime=now;return render()}

   if(b.dataset.tab){tab=b.dataset.tab;return render()}
   if(b.dataset.action)return action(b.dataset.action);
   if(b.dataset.unequip){unequip(state,b.dataset.unequip);return result({message:'Équipement retiré.'})}
   if(b.dataset.recipe){return result(actions.craft(b.dataset.recipe))}
   if(b.dataset.quick!==undefined){const id=state.quickbar[+b.dataset.quick],t=state.inventoryStacks.find(t=>t.id===id);if(t)return result(takeInHands(state,t.uid))}
  };
  body.oninput=e=>{if(e.target.id==='inventorySearch'){const pos=e.target.selectionStart;search=e.target.value;render();const field=body.querySelector('#inventorySearch');field.focus();field.setSelectionRange(pos,pos)}else if(e.target.id==='inventoryCategory'){category=e.target.value;render()}};
  body.oncontextmenu=e=>{const b=e.target.closest('[data-stack]');if(b){e.preventDefault();selection=b.dataset.stack;render()}};
  body.ondblclick=null;
  body.ondragstart=e=>{const b=e.target.closest('[data-stack]');if(b){e.dataTransfer.setData('text/plain',b.dataset.stack);e.dataTransfer.effectAllowed='move'}};
  body.ondragover=e=>{if(e.target.closest('[data-container]'))e.preventDefault()};
  body.ondrop=e=>{e.preventDefault();const dest=e.target.closest('[data-container]');if(!dest)return;const id=e.dataTransfer.getData('text/plain'),t=state.inventoryStacks.find(t=>t.uid===id);if(!t)return;
   const c=dest.dataset.container;
   if(c==='ground')return result(dropStack(state,id,t.count));
   if(c==='hands')return result(takeInHands(state,id));
   if(c.startsWith('quick:')){state.quickbar[+c.split(':')[1]]=t.id;return result({message:'Raccourci assigné.'})}
   if(c.startsWith('equip:')){if(ITEM_DEFS[t.id]?.slot!==c.split(':')[1])return notice('Emplacement incompatible.');return result(equip(state,t.id))}
   result(moveStack(state,id,c,Number(dest.dataset.x)||0,Number(dest.dataset.y)||0));
  };
 }
 return {show:render,cleanup};
}
