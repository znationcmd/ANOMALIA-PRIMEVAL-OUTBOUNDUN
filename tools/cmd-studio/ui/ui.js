'use strict';

const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];
const api = window.cmdStudio;
const names = {
  dashboard: 'Tableau de bord', search: 'Explorer les modèles',
  assets: 'Bibliothèque 3D', projects: 'Mes projets',
  tools: 'Outils connectés', settings: 'Paramètres'
};
let activePage = 'dashboard';
let resources = [];
let latestResults = 0;
let previewRequest = 0;

function el(tag, css = '', value = '') {
  const node = document.createElement(tag);
  if (css) node.className = css;
  if (value !== '') node.textContent = value;
  return node;
}
function icon(name) {
  const svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
  svg.setAttribute('aria-hidden', 'true');
  const use = document.createElementNS('http://www.w3.org/2000/svg','use');
  use.setAttribute('href', '#i-' + name);
  svg.appendChild(use);
  return svg;
}
function button(label, callback, kind='subtle', iconName=null) {
  const b=el('button','btn '+kind);
  b.type='button';
  if(iconName)b.append(icon(iconName));
  b.append(document.createTextNode(label));
  b.addEventListener('click',async()=> {
    b.disabled=true;
    try{await callback();}finally{b.disabled=false;}
  });
  return b;
}
function notice(text, bad=false) {
  const div=$('#notice');div.hidden=false;
  div.classList.toggle('error',bad);
  div.textContent=text;
}
function navigate(page) {
  if(!Object.prototype.hasOwnProperty.call(names,page))return;
  activePage=page;
  $$('.page').forEach(section=>section.hidden=section.id!==page);
  $$('.navItem').forEach(item=>item.classList.toggle('active',item.dataset.view===page));
  $('#headerTitle').textContent=names[page];
  if(page==='assets'&&window.CMDStudioViewer)window.CMDStudioViewer.resize();
}
async function perform(title,callback){
  notice(title+'…');
  try {
    const value=await callback();
    notice(title+' : terminé.');
    return value;
  } catch (error) {
    notice(title+' : '+(error?.message||String(error)),true);
    return null;
  }
}
function empty(parent,title,copy){
  const shell=el('div','emptyState');
  const glyph=el('span','emptyGlyph');glyph.append(icon('cube'));
  shell.append(glyph,el('h3','',title),el('p','',copy));
  parent.replaceChildren(shell);
  return shell;
}
function moneySize(bytes) {
  return bytes < 1048576 ? Math.round(bytes/1024)+' Ko' : (bytes/1048576).toFixed(1)+' Mo';
}
async function refresh(){
  try {
    const [status,settings,assets,projects]=await Promise.all([
      api.call('status'),api.call('settings'),api.call('assets'),api.call('projects')
    ]);
    resources=assets;
    $('#statAssets').textContent=status.assets;
    $('#statProjects').textContent=status.projects;
    $('#statBlender').textContent=status.blender?'Connecté':'Non configuré';
    $('#statUnreal').textContent=status.unreal?'Connecté':'Non configuré';
    $('#blenderTag').textContent=status.blender?'Prêt':'Non configuré';
    $('#unrealTag').textContent=status.unreal?'Prêt':'Non configuré';
    $('#blenderTag').classList.toggle('ready',status.blender);
    $('#unrealTag').classList.toggle('ready',status.unreal);
    $('#sidebarAssetCount').textContent=status.assets;
    $('#assetCount').textContent='('+status.assets+')';
    const active=projects.items.find(p=>p.path===projects.active);
    $('#projectBadge').querySelector('span').textContent=active?.name||'Aucun projet actif';
    $('#blenderPath').textContent=settings.blenderPath||'Non configuré';
    $('#unrealPath').textContent=settings.unrealPath||'Non configuré';
    $('#libraryPath').textContent=settings.libraryPath;
    renderAssets(assets);
    renderProjects(projects);
    paintAnomalia(projects.featured);
  } catch(e){notice('Impossible de charger les données locales : '+e.message,true);}
}
function assetCard(item) {
  const card=el('article','assetCard');
  const preview=el('div','assetPreview');
  const glyph=el('div','glyph');glyph.append(icon('cube'));
  preview.append(glyph);
  const body=el('div','assetBody');
  body.append(el('h3','',item.name));
  body.append(el('div','assetMeta',item.format.toUpperCase()+'  •  '+moneySize(item.size||0)+'  •  '+item.source));
  body.append(el('div','assetMeta','Licence : '+item.license));
  const actions=el('div','assetActions');
  if(['glb','png','jpg','jpeg'].includes(item.format))
    actions.append(button('Prévisualiser',()=>selectPreview(item),'subtle','play'));
  if(item.format!=='glb'&&['fbx','obj','blend','gltf','usd','usdz'].includes(item.format))
    actions.append(button('Convertir GLB',async()=>{
      const res=await perform('Conversion dans Blender',()=>api.call('convertBlender',{id:item.id}));
      if(res){await refresh();navigate('assets');}
    },'subtle','layers'));
  if(['fbx','obj','glb','gltf','usd'].includes(item.format))
    actions.append(button('Vers Unreal',()=>perform('Importation vers Unreal Engine',()=>api.call('importUnreal',{id:item.id})),'primary','arrow'));
  actions.append(button('Dossier',()=>perform('Ouverture du dossier',()=>api.call('openAsset',{id:item.id})),'subtle','folder'));
  body.append(actions);
  card.append(preview,body);
  return card;
}
function renderAssets(list) {
  const panel=$('#assetList');panel.replaceChildren();
  if(!list.length){
    const placeholder=empty(panel,'Une bibliothèque à construire','Importe ton premier modèle GLB, FBX, OBJ ou une texture. Tout reste dans ton espace privé sur ce PC.');
    placeholder.append(button('Importer un modèle',importLocal,'primary','download'));
    return;
  }
  for(const item of list)panel.append(assetCard(item));
}
async function selectPreview(item) {
  navigate('assets');
  const request=++previewRequest;
  $('#previewName').textContent=item.name;
  $('#previewFormat').textContent=item.format.toUpperCase();
  $('#previewLicense').textContent=item.license;
  $('#previewTriangles').textContent='Calcul en cours';
  $('#previewHint').textContent='Chargement de la ressource locale…';
  $('#previewHint').classList.remove('viewerError');
  try{
    const resource=await api.call('previewAsset',{id:item.id});
    if(request!==previewRequest)return;
    if(!window.CMDStudioViewer)throw Error('Visionneuse 3D indisponible. Vérifie l’installation.');
    const outcome=await window.CMDStudioViewer.show(resource);
    if(request!==previewRequest)return;
    $('#previewTriangles').textContent=outcome.triangles==null?'Texture 2D':outcome.triangles.toLocaleString('fr-FR')+' triangles';
    $('#previewHint').textContent=outcome.triangles==null?'Texture affichée sur un plan 3D.':'Modèle réel : rotation libre, zoom et éclairage PBR. L’aspect dépend des matériaux intégrés au GLB.';
    notice('Aperçu chargé : '+item.name);
  } catch(e){
    if(request!==previewRequest)return;
    $('#previewTriangles').textContent='Non disponible';
    $('#previewHint').textContent=e.message;
    $('#previewHint').classList.add('viewerError');
    notice('Prévisualisation impossible : '+e.message,true);
  }
}
function paintAnomalia(featured){
  const linked=Boolean(featured?.available);
  $('#anomaliaDashboardStatus').textContent=linked?'Projet Unreal local disponible':'Projet affiché · fichiers Unreal à associer';
  $('#anomaliaDashboardPath').textContent=linked?featured.path:'Sélectionne AnomaliaPrimeval.uproject sur ce PC';
  $('#anomaliaDashboardAction').textContent=linked?'Ouvrir dans Unreal':'Associer ANOMALIA';
  $('#anomaliaDashboard').classList.toggle('projectLinked',linked);
}
async function chooseAnomaliaProject(){
  const files=await api.pick('project');
  if(!files.length)return;
  // Don't silently assign an unrelated game to the permanent ANOMALIA card.
  if(!/[\\/]AnomaliaPrimeval\.uproject$/i.test(files[0])){
    notice('Choisis le fichier AnomaliaPrimeval.uproject du projet Unreal ANOMALIA.',true);
    return;
  }
  const result=await perform('Association des fichiers Unreal ANOMALIA',()=>api.call('addProject',{file:files[0]}));
  if(result){await refresh();navigate('projects');}
}
async function openAnomalia(){
  let feature;
  try{feature=(await api.call('projects')).featured;}
  catch(error){notice('Projet ANOMALIA : '+error.message,true);return;}
  if(!feature?.available){navigate('projects');await chooseAnomaliaProject();return;}
  let selected;
  if(feature.linked)selected=await perform('Sélection du projet ANOMALIA',()=>api.call('selectProject',{file:feature.path}));
  else selected=await perform('Association du projet ANOMALIA détecté',()=>api.call('addProject',{file:feature.path}));
  if(!selected)return;
  await refresh();
  try{
    await api.call('openTool',{tool:'unreal'});
    notice('Projet ANOMALIA ouvert dans Unreal Engine.');
  }catch(error){
    navigate('settings');
    notice('ANOMALIA associé, mais Unreal Engine doit être configuré : '+error.message,true);
  }
}
function renderProjects(data){
  const panel=$('#projectList');panel.replaceChildren();
  const feature=data.featured;
  const card=el('article','projectRow anomaliaProjectRow');
  const emblem=el('div','anomaliaProjectLogo');
  const mark=el('img');
  mark.src='generated/anomalia-logo.jpg';
  mark.alt='Logo ANOMALIA';
  mark.addEventListener('error',()=>mark.remove());
  emblem.append(mark);
  const details=el('div','anomaliaProjectInfo');
  details.append(el('span','sectionKicker','PROJET PRINCIPAL · UE5'),el('b','','ANOMALIA PRIMEVAL OUTBOUNDUN'),
    el('small','',feature?.available?feature.path:'Projet à associer à ses fichiers locaux .uproject'));
  const status=el('span','rendererTag',feature?.available?'DISPONIBLE SUR CE PC':'À ASSOCIER');
  const actions=el('div','anomaliaProjectActions');
  actions.append(button(feature?.available?'Ouvrir dans Unreal':'Associer ANOMALIA',
    feature?.available?openAnomalia:chooseAnomaliaProject,'primary','folder'));
  if(feature?.available)actions.append(button('Changer de dossier',chooseAnomaliaProject));
  card.append(emblem,details,status,actions);
  panel.append(card);
  for(const project of data.items.filter(p=>!/[\\/]AnomaliaPrimeval\.uproject$/i.test(p.path))){
    const other=el('article','projectRow');
    const details=el('div');
    details.append(el('b','',project.name),el('small','',project.path));
    const status=el('span','rendererTag',!project.available?'FICHIER ABSENT':project.path===data.active?'PROJET ACTIF':'ENREGISTRÉ');
    const actions=button('Utiliser',async()=>{const result=await perform('Sélection du projet',()=>api.call('selectProject',{file:project.path}));if(result)await refresh();});
    other.append(details,status,actions);
    panel.append(other);
  }
}
function secureThumb(src,parent){
  try{
    const url=new URL(src);
    if(url.protocol!=='https:'||!(/(^|\.)sketchfab\.com$/i.test(url.hostname)||url.hostname==='cdn.polyhaven.com'))return;
    const img=el('img');
    img.src=url.href;img.alt='Aperçu officiel du modèle';img.loading='lazy';img.referrerPolicy='no-referrer';
    img.onerror=()=>img.remove();
    parent.replaceChildren(img);
  }catch{ /* Preview is optional. */ }
}
function renderResults(list){
  const panel=$('#searchResults');panel.replaceChildren();
  $('#resultCount').textContent='('+list.length+')';
  if(!list.length)return empty(panel,'Aucun modèle trouvé','Essaie un autre mot-clé ou change de plateforme. Aucun résultat fictif n’est ajouté.');
  for(const item of list){
    const card=el('article','assetCard');
    const preview=el('div','assetPreview');
    const glyph=el('div','glyph');glyph.append(icon('cube'));preview.append(glyph);
    secureThumb(item.thumbnail,preview);
    const body=el('div','assetBody');
    body.append(el('h3','',item.name));
    body.append(el('div','assetMeta',item.provider==='polyhaven'?'Poly Haven • CC0':'Sketchfab • '+item.license));
    const actions=el('div','assetActions');
    if(item.downloadable)actions.append(button('Télécharger',async()=>{
      const saved=await perform('Téléchargement de '+item.name,()=>api.call('downloadPolyHaven',{id:item.id}));
      if(saved){await refresh();notice('Enregistré dans ta bibliothèque : '+saved.name);}
    },'primary','download'));
    actions.append(button('Fiche officielle',()=>perform('Ouverture de la fiche',()=>api.openExternal(item.url)),'subtle','external'));
    body.append(actions);card.append(preview,body);panel.append(card);
  }
}
async function runSearch() {
  const id=++latestResults;
  const panel=$('#searchResults');
  empty(panel,'Recherche en cours…','Interrogation du catalogue officiel, sans résultats simulés.');
  $('#resultCount').textContent='';
  const submit=$('#searchForm button[type="submit"]');
  submit.disabled=true;
  try{
    const list=await api.call('search',{provider:$('#provider').value,query:$('#query').value});
    if(id!==latestResults)return;
    renderResults(list);
    notice(list.length+' ressource(s) trouvée(s) dans '+($('#provider').value==='polyhaven'?'Poly Haven':'Sketchfab')+'.');
  }catch(e){
    if(id!==latestResults)return;
    empty(panel,'Recherche momentanément indisponible','Vérifie ta connexion Internet et réessaie.');
    notice(e.message,true);
  }finally{if(id===latestResults)submit.disabled=false;}
}
async function chooseExecutable(key,kind){
  const files=await api.pick(kind);if(!files.length)return;
  const result=await perform('Configuration du logiciel',()=>api.call('configure',{[key]:files[0]}));
  if(result)await refresh();
}
async function importLocal(){
  const files=await api.pick('asset');if(!files.length)return;
  const result=await perform('Importation de tes ressources',()=>api.call('import',{files}));
  if(result){await refresh();navigate('assets');notice(result.length+' ressource(s) enregistrée(s) localement.');}
}
async function chooseProject(){
  const files=await api.pick('project');if(!files.length)return;
  const result=await perform('Association du projet Unreal',()=>api.call('addProject',{file:files[0]}));
  if(result){await refresh();navigate('projects');}
}

$$('[data-view]').forEach(b=>b.addEventListener('click',()=>navigate(b.dataset.view)));
$$('[data-go]').forEach(b=>b.addEventListener('click',()=>navigate(b.dataset.go)));
$('#projectBadge').addEventListener('click',()=>navigate('projects'));
$('#quickImport').addEventListener('click',importLocal);
$('#assetImport').addEventListener('click',importLocal);
$('#chooseProject').addEventListener('click',chooseProject);
$('#anomaliaDashboardAction').addEventListener('click',async()=>{
  const featured=(await api.call('projects')).featured;
  if(featured?.available)await openAnomalia();
  else await chooseAnomaliaProject();
});
const anomaliaLogo=$('#anomaliaDashboard .anomaliaArt img');
anomaliaLogo?.addEventListener('error',()=>anomaliaLogo.remove());
$('#chooseBlender').addEventListener('click',()=>chooseExecutable('blenderPath','blender'));
$('#chooseUnreal').addEventListener('click',()=>chooseExecutable('unrealPath','unreal'));
$('#launchBlender').addEventListener('click',()=>perform('Lancement de Blender',()=>api.call('openTool',{tool:'blender'})));
$('#launchUnreal').addEventListener('click',()=>perform('Lancement d’Unreal Engine',()=>api.call('openTool',{tool:'unreal'})));
$('#resetCamera').addEventListener('click',()=>window.CMDStudioViewer?.reset());
$('#searchForm').addEventListener('submit',e=>{e.preventDefault();runSearch();});
$('#discoverBtn').addEventListener('click',()=>{$('#query').value='';$('#provider').value='polyhaven';runSearch();});
$$('.suggest').forEach(b=>b.addEventListener('click',()=>{$('#query').value=b.dataset.query;runSearch();}));
$$('.category').forEach(b=>b.addEventListener('click',()=>{
  $$('.category').forEach(c=>c.classList.toggle('active',c===b));
  $('#query').value=b.dataset.term;
  runSearch();
}));
refresh();


function paintUpdateState(s){
  if(!s)return;
  $('#updateVersion').textContent='v'+(s.version||'—');
  $('#updateFeed').value=s.feedUrl||'';
  $('#updateEnabled').checked=s.enabled===true;
  $('#updateStatus').dataset.phase=s.phase||'configuration';
  $('#updateStatusTitle').textContent={
    configuration:'Configuration requise',veille:'Surveillance active',verification:'Vérification',
    disponible:'Nouvelle version',telechargement:'Téléchargement sécurisé',
    prete:'Mise à jour prête', 'a-jour':'Version à jour', erreur:'Erreur',
    desactivee:'Mises à jour désactivées',developpement:'Version développeur'
  }[s.phase]||'Mises à jour';
  $('#updateStatusText').textContent=s.message||'';
  $('#updateInstall').hidden=s.phase!=='prete';
  $('#updateProgressTrack').hidden=s.phase!=='telechargement'&&s.phase!=='prete';
  $('#updateProgressBar').style.width=Math.max(0,Math.min(100,Number(s.progress||0)))+'%';
  $('#updateToken').placeholder=s.hasToken?
    'Clé privée conservée et chiffrée — laisse vide pour la garder':
    'Clé privée fournie par ton serveur de mises à jour';
}
async function updateStatusInit(){
  try{
    paintUpdateState(await api.updates.status());
    api.updates.subscribe(paintUpdateState);
  }catch(e){notice('Statut des mises à jour indisponible : '+e.message,true);}
}
$('#updateConfigure').addEventListener('submit',async e=>{
  e.preventDefault();
  const payload={
    url:$('#updateFeed').value.trim(),
    enabled:$('#updateEnabled').checked
  };
  const key=$('#updateToken').value;
  if(key)payload.token=key;
  const submit=$('#updateConfigure button[type="submit"]');
  submit.disabled=true;
  try{
    const result=await api.updates.configure(payload);
    $('#updateToken').value='';
    paintUpdateState(result);
    notice('Configuration privée des mises à jour enregistrée.');
  }catch(err){notice('Configuration des mises à jour : '+err.message,true);}
  finally{submit.disabled=false;}
});
$('#updateCheck').addEventListener('click',async()=>{
  const b=$('#updateCheck');b.disabled=true;
  try{
    paintUpdateState(await api.updates.check());
  }catch(err){notice('Vérification des mises à jour : '+err.message,true);}
  finally{b.disabled=false;}
});
$('#updateInstall').addEventListener('click',async()=>{
  if(!window.confirm('Installer la nouvelle version de CMD Studio maintenant ? Tes projets locaux resteront conservés.'))return;
  try{await api.updates.install();}
  catch(err){notice('Installation impossible : '+err.message,true);}
});
updateStatusInit();
