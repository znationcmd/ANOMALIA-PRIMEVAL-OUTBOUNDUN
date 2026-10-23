'use strict';
const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];
const api = window.cmdStudio;
const names = { dashboard: "Vue d'ensemble", assets: 'Bibliothèque 3D', search: 'Recherche 3D', projects: 'Mes jeux', tools: 'Outils connectés', settings: 'Paramètres' };
let config = {};
let activePage = 'dashboard';
let resources = [];

function element(tag, className = '', content = '') {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (content !== '') el.textContent = content;
  return el;
}
function showNotice(message, error = false) {
  const n = $('#notice');
  n.hidden = false; n.textContent = message;
  n.classList.toggle('error', error);
}
function navigate(page) {
  if (!Object.hasOwn(names,page)) return;
  activePage = page;
  $$('.page').forEach(section => section.hidden = section.id !== page);
  $$('.navItem').forEach(button => button.classList.toggle('active', button.dataset.view === page));
  $('#headerTitle').textContent = names[page];
}
async function perform(label, callback) {
  showNotice(label + '…');
  try { const result = await callback(); showNotice(label + ' : opération terminée.'); return result; }
  catch (e) { showNotice(e.message || String(e), true); return null; }
}
function empty(parent, message) {
  parent.replaceChildren(element('div','empty',message));
}
async function refresh() {
  try {
    const [status, settings, assets, projects] = await Promise.all([
      api.call('status'), api.call('settings'), api.call('assets'), api.call('projects')
    ]);
    config = settings;
    resources = assets;
    $('#statAssets').textContent = status.assets;
    $('#statProjects').textContent = status.projects;
    $('#statBlender').textContent = status.blender ? 'Prêt' : 'Absent';
    $('#statUnreal').textContent = status.unreal ? 'Prêt' : 'Absent';
    $('#blenderTag').textContent = status.blender ? 'Configuré' : 'Non configuré';
    $('#unrealTag').textContent = status.unreal ? 'Configuré' : 'Non configuré';
    $('#projectBadge').textContent = projects.items.find(p => p.path === projects.active)?.name || 'Aucun projet';
    $('#blenderPath').textContent = settings.blenderPath || 'Non configuré';
    $('#unrealPath').textContent = settings.unrealPath || 'Non configuré';
    $('#libraryPath').textContent = settings.libraryPath;
    renderAssets(assets);
    renderProjects(projects);
  } catch (e) { showNotice('Initialisation impossible : ' + e.message, true); }
}
function actionButton(label, fn, primary = false) {
  const btn = element('button','btn' + (primary ? ' primary' : ''),label);
  btn.addEventListener('click', async () => { btn.disabled = true; try { await fn(); } finally { btn.disabled = false; } });
  return btn;
}
function renderAssets(assets) {
  const panel = $('#assetList'); panel.replaceChildren();
  if (!assets.length) return empty(panel, 'Ta bibliothèque est vide. Ajoute un fichier 3D local ou recherche un modèle Poly Haven.');
  for (const item of assets) {
    const card = element('article','assetCard');
    const preview = element('div','assetPreview');
    preview.append(element('span','glyph','◈'));
    const body = element('div','assetBody');
    body.append(element('h3','',item.name));
    const mb = (item.size / 1048576).toFixed(1);
    body.append(element('div','assetMeta',item.format.toUpperCase() + ' · ' + mb + ' Mo · ' + item.source));
    body.append(element('div','assetMeta','Licence : ' + item.license));
    const actions = element('div','assetActions');
    actions.append(actionButton('Dossier', () => perform('Ouverture du dossier', () => api.call('openAsset',{id:item.id}))));
    if (item.format !== 'glb' && ['fbx','obj','blend','gltf','usd','usdz'].includes(item.format))
      actions.append(actionButton('→ GLB', async () => { const result = await perform('Conversion Blender', () => api.call('convertBlender',{id:item.id})); if(result) refresh(); }));
    if (['fbx','obj','glb','gltf','usd'].includes(item.format))
      actions.append(actionButton('→ Unreal', () => perform('Importation Unreal', () => api.call('importUnreal',{id:item.id})), true));
    body.append(actions);card.append(preview,body);panel.append(card);
  }
}
function renderProjects(data) {
  const panel = $('#projectList'); panel.replaceChildren();
  if (!data.items.length) return empty(panel, "Aucun projet Unreal n'est enregistré. Ajoute le fichier AnomaliaPrimeval.uproject.");
  for(const project of data.items) {
    const row = element('article','projectRow');
    const info = element('div');
    info.append(element('b','',project.name),element('small','',project.path));
    row.append(info,element('span','tag',project.path === data.active ? 'Projet actif' : 'Enregistré'));
    panel.append(row);
  }
}
function safeImage(src, parent) {
  try {
    const url = new URL(src);
    if (url.protocol !== 'https:' || !/(\.sketchfab\.com$|^cdn\.polyhaven\.com$)/i.test(url.hostname)) return;
    const image = element('img'); image.src = url.href; image.alt = '';
    image.loading = 'lazy'; image.referrerPolicy = 'no-referrer';
    parent.replaceChildren(image);
  } catch { /* thumbnail optional */ }
}
function renderResults(results) {
  const panel = $('#searchResults'); panel.replaceChildren();
  if (!results.length) return empty(panel,'Aucun résultat pour cette recherche.');
  for (const item of results) {
    const card = element('article','assetCard');
    const preview = element('div','assetPreview');
    preview.append(element('span','glyph','◈'));
    safeImage(item.thumbnail,preview);
    const body = element('div','assetBody');
    body.append(element('h3','',item.name),element('div','assetMeta',item.provider + ' · ' + item.license));
    const actions = element('div','assetActions');
    if (item.downloadable) {
      actions.append(actionButton('↓ Télécharger', async () => {
        const saved = await perform('Téléchargement de ' + item.name, () => api.call('downloadPolyHaven',{id:item.id}));
        if (saved) await refresh();
      }, true));
    }
    actions.append(actionButton('Voir la fiche ↗', () => perform('Ouverture de la fiche', () => api.openExternal(item.url))));
    body.append(actions);card.append(preview,body);panel.append(card);
  }
}
async function chooseExecutable(key,kind) {
  const chosen = await api.pick(kind);
  if (!chosen.length) return;
  const result = await perform('Configuration ' + key, () => api.call('configure',{[key]:chosen[0]}));
  if (result) await refresh();
}
async function importLocal() {
  const files = await api.pick('asset');
  if (!files.length) return;
  const result = await perform('Importation des ressources',() => api.call('import',{ files }));
  if (result) { await refresh();navigate('assets');showNotice(result.length + ' fichier(s) contrôlé(s) et enregistré(s).'); }
}
async function chooseProject() {
  const files = await api.pick('project');
  if (!files.length) return;
  const result = await perform('Ajout du projet',() => api.call('addProject',{file:files[0]}));
  if (result) { await refresh();navigate('projects'); }
}
$$('[data-view]').forEach(btn=>btn.addEventListener('click',()=>navigate(btn.dataset.view)));
$$('[data-go]').forEach(btn=>btn.addEventListener('click',()=>navigate(btn.dataset.go)));
$('#quickImport').addEventListener('click',importLocal);
$('#assetImport').addEventListener('click',importLocal);
$('#chooseProject').addEventListener('click',chooseProject);
$('#chooseBlender').addEventListener('click',()=>chooseExecutable('blenderPath','blender'));
$('#chooseUnreal').addEventListener('click',()=>chooseExecutable('unrealPath','unreal'));
$('#launchBlender').addEventListener('click',()=>perform('Lancement Blender',()=>api.call('openTool',{tool:'blender'})));
$('#launchUnreal').addEventListener('click',()=>perform('Lancement Unreal',()=>api.call('openTool',{tool:'unreal'})));
$('#searchForm').addEventListener('submit',async e=>{
  e.preventDefault();
  const panel=$('#searchResults');
  empty(panel,'Recherche dans le catalogue…');
  try {
    const result=await api.call('search',{ provider: $('#provider').value,query: $('#query').value });
    renderResults(result);
    showNotice(result.length + ' résultat(s) trouvé(s).');
  } catch(e) { empty(panel,'Recherche impossible.');showNotice(e.message,true); }
});
refresh();
