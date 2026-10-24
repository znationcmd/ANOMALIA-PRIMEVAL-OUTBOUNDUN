import {buildMapCatalog,filterMapCatalog} from './map-catalog.js';

// Écran de choix des cartes : aucun fond DayZ, aucune carte ou progression fictive.
// Les .umap se lancent dans Unreal Editor ; seules les scènes ANOMALIA JSON
// s'affichent dans le viewport 3D intégré.
export function createMapLauncher({listLocal,onOpenLocal,onNew,onResume,onImport,onLink,onOpenUnreal,notify}){
  const layer=document.createElement('section');
  layer.id='mapLauncher';
  layer.className='mapLauncher';
  layer.hidden=true;
  layer.setAttribute('aria-label','Choisir une carte ANOMALIA');
  layer.innerHTML=`
    <div class="mapHero"><div class="mapHeroNoise" aria-hidden="true"></div>
      <div class="mapHeroTop"><div class="mapIdentity"><span class="mapMonogram">A</span><div><strong>ANOMALIA <em>EDITOR</em></strong><small>WORLD AUTHORING STUDIO</small></div></div>
        <button id="mapLauncherClose" class="mapClose" type="button" aria-label="Fermer et retourner à l’éditeur">✕ <span>Retour à l’éditeur</span></button>
      </div>
      <div class="mapHeroContent"><span class="mapEyebrow">ANOMALIA PRIMEVAL OUTBOUNDUN / ÉDITEUR DE MONDES</span>
        <h1>Choisir une carte</h1><p>Ouvre une carte existante, récupère ton travail ou crée ton prochain monde.</p>
        <div class="mapHeroActions"><button id="mapCreateNew" type="button" class="mapPrimary">＋ Nouvelle carte</button>
          <button id="mapResume" type="button">↗ Reprendre la scène active</button>
          <button id="mapImportFile" type="button">⇧ Importer .anomalia.json</button></div>
      </div><div class="mapHeroBottom"><span>3D WORLD BUILDER</span><span>LOCAL / UE5</span></div>
    </div>
    <div class="mapPickerBody"><div class="mapPickerHeading"><div><small>BIBLIOTHÈQUE DE CARTES</small><h2>Mes mondes</h2></div><span id="mapCount" class="mapCount">Recherche des cartes…</span></div>
      <div class="mapPickerToolbar"><div class="mapFilters" role="group" aria-label="Filtrer les cartes">
        <button type="button" data-filter="all" class="active" aria-pressed="true">Toutes</button>
        <button type="button" data-filter="local" aria-pressed="false">Scènes locales</button>
        <button type="button" data-filter="ue5" aria-pressed="false">Cartes Unreal 5</button></div>
        <label class="mapSearchLabel"><span class="mapSearchIcon">⌕</span><input id="mapSearch" type="search" placeholder="Rechercher une carte ou un secteur…" autocomplete="off"></label>
        <button id="mapRefresh" class="mapRefresh" type="button" title="Actualiser les cartes">↻ Actualiser</button>
      </div>
      <div id="mapPickerGrid" class="mapPickerGrid"></div>
      <div class="mapFooter"><span id="mapPickerInfo">Tes projets sont privés et restent enregistrés sur cet appareil.</span>
        <button id="mapLinkUE5" type="button">◇ Lier le projet ANOMALIA Unreal Engine</button></div>
    </div>
    <div id="mapLoading" class="mapLoading" hidden role="status" aria-live="polite">
      <div class="mapLoadingPlate"><span class="mapLoadingIcon">A</span><span class="mapEyebrow">ANOMALIA WORLD EDITOR</span>
        <h2 id="mapLoadingTitle">Ouverture de la carte…</h2><p id="mapLoadingDescription">Préparation du projet</p>
        <div class="mapLoadingTrack"><div class="mapLoadingIndeterminate"></div></div>
        <small id="mapLoadingFootnote">Le chargement affiche un indicateur d’activité, sans inventer de pourcentage.</small>
        <button id="mapLoadingClose" type="button" hidden>Retour au choix des cartes</button>
      </div>
    </div>`;
  document.body.append(layer);
  const $=selector=>layer.querySelector(selector);
  const state={kind:'all',search:'',items:[],unreal:null,busy:false};
  const grid=$('#mapPickerGrid');
  const close=()=>{if(state.busy)return;layer.hidden=true;document.body.classList.remove('mapLauncherVisible');};
  function show(){
    layer.hidden=false;
    document.body.classList.add('mapLauncherVisible');
    refresh();
  }
  function busy(title,description){
    state.busy=true;
    $('#mapLoading').hidden=false;
    $('#mapLoadingTitle').textContent=title;
    $('#mapLoadingDescription').textContent=description;
    $('#mapLoadingClose').hidden=true;
    $('#mapLoadingFootnote').textContent='Chargement en cours · aucune progression simulée';
  }
  function endBusy(){
    state.busy=false;
    $('#mapLoading').hidden=true;
  }
  function showExternalLaunched(map){
    state.busy=false;
    $('#mapLoadingTitle').textContent='Carte transmise à Unreal Engine';
    $('#mapLoadingDescription').textContent=map+' s’ouvre dans une autre fenêtre Windows. La vue intégrée ne peut pas lire un fichier .umap.';
    $('#mapLoadingFootnote').textContent='ANOMALIA Editor reste disponible pour les scènes JSON et les modèles GLB.';
    $('#mapLoadingClose').hidden=false;
  }
  function card(entry){
    const button=document.createElement('button');
    button.className='mapCard '+(entry.type==='ue5'?'mapUE5':'mapLocal');
    button.type='button';button.title=entry.description;
    const cover=document.createElement('span');cover.className='mapCover';
    const category=document.createElement('span');category.className='mapCategory';
    category.textContent=entry.type==='ue5'?'UNREAL ENGINE 5':'SCÈNE ANOMALIA';
    const emblem=document.createElement('span');emblem.className='mapCoverEmblem';
    emblem.textContent=entry.type==='ue5'?'UE5':'A';
    const visualNote=document.createElement('span');visualNote.className='mapVisualNote';
    visualNote.textContent=entry.type==='ue5'?'Carte native détectée':'Scène enregistrée';
    cover.append(category,emblem,visualNote);
    const detail=document.createElement('span');detail.className='mapCardDetail';
    const name=document.createElement('strong');name.textContent=entry.title;name.title=entry.title;
    const description=document.createElement('small');description.textContent=entry.subtitle;description.title=entry.subtitle;
    const open=document.createElement('span');open.className='mapCardOpen';
    open.textContent=entry.type==='ue5'?'Ouvrir dans Unreal ↗':'Charger cette carte →';
    detail.append(name,description,open);button.append(cover,detail);
    button.addEventListener('click',async()=>openEntry(entry));
    return button;
  }
  function render(){
    const visible=filterMapCatalog(state.items,state.kind,state.search);
    grid.replaceChildren();
    $('#mapCount').textContent=state.items.length+' carte'+(state.items.length>1?'s':'')+' disponible'+(state.items.length>1?'s':'');
    for(const entry of visible.slice(0,250))grid.append(card(entry));
    if(!visible.length){
      const empty=document.createElement('div');empty.className='mapNoResults';
      const head=document.createElement('strong');head.textContent=state.items.length?'Aucune carte ne correspond à cette recherche.':'Aucune carte enregistrée pour le moment.';
      const note=document.createElement('p');
      note.textContent=state.items.length?'Modifie ton filtre ou actualise la bibliothèque.':'Crée une scène, importe ton projet .anomalia.json ou lie ton projet Unreal pour découvrir les cartes .umap.';
      empty.append(head,note);grid.append(empty);
    }
    const unreal=state.unreal;
    $('#mapPickerInfo').textContent=unreal?.linked?
      (unreal.mapCount||0)+' cartes Unreal détectées · .umap ouverts dans UE5, et non dans la vue Three.js.':
      'Les cartes Unreal nécessitent le projet .uproject et UE5 sur Windows. Les scènes locales restent privées.';
  }
  async function refresh(){
    try{
      const [locals,unreal]=await Promise.all([
        listLocal().catch(()=>[]),
        window.anomaliaDesktop?.unreal?.status?.().catch(()=>null)??Promise.resolve(null)
      ]);
      state.unreal=unreal;
      state.items=buildMapCatalog(locals,unreal);
      render();
    }catch(e){notify('Bibliothèque de cartes : '+e.message,true);}
  }
  async function openEntry(entry){
    if(state.busy)return;
    if(entry.type==='ue5'){
      busy('Lancement d’Unreal Engine',entry.title+' · demande d’ouverture de la vraie carte .umap');
      try{await onOpenUnreal(entry.key);showExternalLaunched(entry.title);}
      catch(e){endBusy();notify('Unreal Engine : '+e.message,true);}
      return;
    }
    busy('Chargement de '+entry.title,'Restauration des objets 3D et du relief enregistré…');
    try{await onOpenLocal(entry.key);endBusy();close();}
    catch(e){endBusy();notify('Ouverture impossible : '+e.message,true);}
  }
  async function runLocal(action,title,description){
    if(state.busy)return;
    busy(title,description);
    try{
      const done=await action();
      endBusy();
      if(done!==false)close();
    }catch(e){endBusy();notify('Opération impossible : '+e.message,true);}
  }
  $('#mapLauncherClose').addEventListener('click',close);
  $('#mapLoadingClose').addEventListener('click',endBusy);
  $('#mapCreateNew').addEventListener('click',()=>runLocal(onNew,'Création du monde','Préparation de la nouvelle scène ANOMALIA…'));
  $('#mapResume').addEventListener('click',()=>runLocal(onResume,'Ouverture de la scène','Restauration de ta vue de travail…'));
  $('#mapImportFile').addEventListener('click',()=>{if(!state.busy)onImport();});
  $('#mapLinkUE5').addEventListener('click',async()=>{
    if(state.busy)return;
    try{await onLink();await refresh();}
    catch(e){notify('Liaison Unreal : '+e.message,true);}
  });
  $('#mapRefresh').addEventListener('click',refresh);
  $('#mapSearch').addEventListener('input',e=>{state.search=e.target.value;render();});
  for(const control of layer.querySelectorAll('[data-filter]')){
    control.addEventListener('click',()=>{
      state.kind=control.dataset.filter;
      for(const btn of layer.querySelectorAll('[data-filter]')){
        const active=btn===control;btn.classList.toggle('active',active);btn.setAttribute('aria-pressed',String(active));
      }
      render();
    });
  }
  return {show,close,refresh,isVisible:()=>!layer.hidden};
}
