/**
 * WorkForge — same browser-based game UI is used by Electron Windows app.
 * This is a local mapping-mod manager, not a remote marketplace.
 */
const KEY = "anomalia-workshop-map-mods-v1";
const CATEGORIES = ["Tous les mods","Véhicules","Créatures","Bâtiments","Cartes","Armes","Survie","Gameplay","Outils"];
const ICONS = ["▦","🚙","🦖","▤","◈","⌖","♨","♟","⚙"];
function readMods(){
  try{
    const v=JSON.parse(localStorage.getItem(KEY)||"[]");
    return Array.isArray(v)?v.filter(m=>m&&typeof m.id==="string"&&typeof m.name==="string"):[];}
  catch{return [];}
}
const escapeText = s => String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
export function mountWorkForge({openMods,onPlay}={}){
  if(document.getElementById("workforgeRoot"))return;
  const shell=document.createElement("section");
  shell.id="workforgeRoot";shell.className="wf-root hidden";shell.setAttribute("role","dialog");
  shell.setAttribute("aria-modal","true");shell.setAttribute("aria-label","WorkForge — Mods et créations");
  shell.innerHTML=\`
    <div class="wf-top"><div class="wf-logo">Ⓐ <span>ANOMALIA’Z <small>PRIGIMALIA</small></span></div>
      <strong class="wf-heading">⚙ WORKFORGE <small>MODS & CRÉATIONS</small></strong>
      <label class="wf-search"><span class="sr-only">Recherche</span><input id="wfSearch" placeholder="Rechercher un mod ou une création…"></label>
      <button id="wfPlay">▶ JOUER</button><button id="wfClose" aria-label="Fermer WorkForge">✕</button>
    </div>
    <div class="wf-body">
      <nav class="wf-nav" aria-label="Navigation WorkForge">
      <button data-wf-nav="home" class="active">⌂ Accueil</button>
      <button data-wf-nav="mods">⚒ WorkForge</button>
      <button data-wf-nav="installed">▦ Mes mods</button>
      <button data-wf-nav="creations">✧ Créations</button>
      <button data-wf-nav="settings">⚙ Paramètres</button>
      <div class="wf-nav-note">SURVIVRE<br>EXPLORER<br>CONSTRUIRE<br>CRÉER</div>
      </nav>
      <main class="wf-main">
        <header class="wf-hero"><div class="wf-hero-shade">
          <p class="wf-kicker">ANOMALIA’Z PRIGIMALIA</p>
          <h2>WORKFORGE</h2>
          <p>MODS & CRÉATIONS</p>
          <p class="wf-hero-copy">Explorez, créez, gérez et partagez vos créations.</p>
          <div class="wf-metrics"><span><b id="wfTotal">0</b> mods locaux</span><span><b id="wfActive">0</b> activés</span><span><b id="wfDisabled">0</b> désactivés</span></div>
        </div></header>
        <div class="wf-categories" id="wfCategories"></div>
        <div class="wf-section-title"><h3 id="wfSectionTitle">Mes mods</h3><select id="wfSort" aria-label="Trier"><option value="name">Nom</option><option value="recent">Version</option><option value="active">Activés en premier</option></select></div>
        <div class="wf-cards" id="wfCards"></div>
        <p class="wf-disclaimer">WorkForge local — seuls les mods de mapping JSON validés sont pris en charge. Le catalogue communautaire en ligne, les notes et les téléchargements nécessitent encore un serveur réel.</p>
      </main>
      <aside class="wf-side">
        <div class="wf-panel"><h3>● WORKFORGE LOCAL</h3><p>Application et interface du jeu</p><hr>
        <div>Connexion catalogue <strong>Non configurée</strong></div>
        <div>Mods installés <strong id="wfSideTotal">0</strong></div>
        <div>Mises à jour distantes <strong>Non disponibles</strong></div>
        <button id="wfManage" class="wf-primary">Gérer mes mods →</button></div>
        <div class="wf-panel"><h3>CRÉATIONS</h3><p>Importez des mappings réalisés avec les outils ANOMALIA’Z.</p><button id="wfImport" class="wf-primary">Importer un mapping JSON</button></div>
        <div class="wf-panel"><h3>COMPATIBILITÉ</h3><p>Le moteur vérifie les identifiants, versions et emplacements des objets avant l'installation.</p></div>
      </aside>
    </div>\`;
  document.body.append(shell);
  const $=id=>shell.querySelector("#"+id);
  let category="Tous les mods";
  let view="home";
  let lastFocus=null;
  const render=()=>{
    const mods=readMods();
    $("wfTotal").textContent=String(mods.length);
    $("wfActive").textContent=String(mods.filter(m=>m.enabled).length);
    $("wfDisabled").textContent=String(mods.filter(m=>!m.enabled).length);
    $("wfSideTotal").textContent=String(mods.length);
    $("wfCategories").replaceChildren();
    CATEGORIES.forEach((cat,i)=>{
      const button=document.createElement("button");
      button.type="button";button.className="wf-category"+(cat===category?" active":"");
      button.innerHTML=\`<span>\${ICONS[i]}</span><b>\${escapeText(cat)}</b>\`;
      button.onclick=()=>{category=cat;render();};
      $("wfCategories").append(button);
    });
    const search=$("wfSearch").value.trim().toLocaleLowerCase("fr");
    const filtered=mods.filter(m=>{
      const kind=(m.category||"Cartes").toLocaleLowerCase("fr");
      return (category==="Tous les mods"||kind===category.toLocaleLowerCase("fr"))
        && (!search||(m.name+" "+m.id+" "+(m.type||"")).toLocaleLowerCase("fr").includes(search));
    });
    const sort=$("wfSort").value;
    filtered.sort((a,b)=>sort==="active"?Number(!!b.enabled)-Number(!!a.enabled):sort==="recent"?String(b.version).localeCompare(String(a.version),undefined,{numeric:true}):a.name.localeCompare(b.name,"fr"));
    $("wfSectionTitle").textContent=view==="installed"?"Mes mods installés":view==="creations"?"Mes créations":"Mods disponibles sur cet appareil";
    $("wfCards").replaceChildren();
    if(!filtered.length){
      const empty=document.createElement("div");empty.className="wf-empty";
      empty.textContent=mods.length?"Aucun mod ne correspond à la recherche ou à cette catégorie.":"Aucun mod installé. Importe un mod de mapping JSON pour commencer.";
      $("wfCards").append(empty);
    }
    filtered.forEach(mod=>{
      const card=document.createElement("article");card.className="wf-card";
      card.innerHTML=\`<div class="wf-card-art">◇</div><div class="wf-card-body">
      <h4>\${escapeText(mod.name)}</h4><p>\${escapeText(mod.id)} · v\${escapeText(mod.version)}</p>
      <div class="wf-card-status">\${mod.enabled?"● ACTIVÉ":"○ DÉSACTIVÉ"} · MAPPING LOCAL</div></div>\`;
      const btn=document.createElement("button");btn.textContent=mod.enabled?"Désactiver":"Activer";btn.className="wf-primary";
      btn.onclick=()=>{const next=readMods().map(m=>m.id===mod.id?{...m,enabled:!m.enabled}:m);try{localStorage.setItem(KEY,JSON.stringify(next));window.dispatchEvent(new Event("anomalia-workforge-change"));render();}catch{btn.textContent="Stockage indisponible";btn.disabled=true;}};
      card.append(btn);$("wfCards").append(card);
    });
  };
  const show=()=>{lastFocus=document.activeElement;shell.classList.remove("hidden");render();$("wfClose").focus();};
  const hide=()=>{shell.classList.add("hidden");lastFocus?.focus?.();};
  const goMods=()=>{hide();openMods?.();};
  $("wfClose").onclick=hide;
  $("wfPlay").onclick=()=>{hide();onPlay?.();};
  $("wfImport").onclick=goMods;$("wfManage").onclick=goMods;
  $("wfSearch").oninput=render;$("wfSort").onchange=render;
  shell.querySelectorAll("[data-wf-nav]").forEach(b=>b.onclick=()=>{
    view=b.dataset.wfNav;b.parentElement.querySelectorAll("button").forEach(x=>x.classList.toggle("active",x===b));
    if(view==="settings"){goMods();return;}
    if(view==="mods")category="Tous les mods";
    render();
  });
  shell.addEventListener("keydown",event=>{if(event.key==="Escape"){event.preventDefault();hide();}if(event.key==="Tab"){const items=Array.from(shell.querySelectorAll("button,input,select")).filter(x=>x.offsetParent!==null);if(items.length){const first=items[0],last=items.at(-1);if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}}}});
  window.addEventListener("storage",render);
  return {show,hide,render};
}
