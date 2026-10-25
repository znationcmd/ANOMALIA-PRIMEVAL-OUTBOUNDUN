// Renderer-only navigation, real UE5 file conversions and honest compatibility panels.
// Never performs a conversion when the target format is unsupported.
const UTILITY_TITLES={
 terrainProcessor:'Terrain Processor',bankrev:'BankRev',imagepaa:'Image To PAA · TGA',
 cfgconvert:'Cfg Convert',dsutils:'DS Utils',texview:'Tex View',navmesh:'Nav Mesh Generator'
};
export function setupToolsUtilities({api,getProjectId,getFiles,getProjects,refreshFiles,showTab,showModal,notify}){
 let selected='terrainProcessor';
 const $=selector=>document.querySelector(selector);
 const $$=selector=>[...document.querySelectorAll(selector)];
 const nodeText=(id,value)=>{const el=$('#'+id);if(el)el.textContent=value;};
 function setOptions(id,choices){
   const select=$('#'+id);
   if(!select)return;
   const previous=select.value;
   select.replaceChildren();
   if(!choices.length){select.add(new Option('Aucun fichier compatible dans ce projet',''));select.disabled=true;return;}
   select.disabled=false;
   for(const file of choices)select.add(new Option(file.path,file.path));
   if(choices.some(f=>f.path===previous))select.value=previous;
 }
 function refreshSources(){
   const files=getFiles().filter(f=>f.type==='file');
   setOptions('utilTerrainSource',files.filter(f=>/^Content\/Terrain\/.+\.png$/i.test(f.path)));
   setOptions('utilTextureSource',files.filter(f=>/^Content\/Textures\/.+\.png$/i.test(f.path)));
   setOptions('utilConfigSource',files.filter(f=>/^Config\/.+\.(json|ini|cfg)$/i.test(f.path)));
 }
 function select(key){
   if(!UTILITY_TITLES[key])key='terrainProcessor';
   selected=key;
   nodeText('utilityTitle',UTILITY_TITLES[key]);
   for(const panel of $$('[data-util-panel]'))panel.hidden=panel.dataset.utilPanel!==key;
   for(const button of $$('[data-util-select]')){
     const active=button.dataset.utilSelect===key;
     button.classList.toggle('active',active);button.setAttribute('aria-pressed',String(active));
   }
   for(const button of $$('.sidebar .nav[data-utility]')){
     button.classList.toggle('active',button.dataset.utility===key);
   }
   refreshSources();
   const page=$('#utilities');
   if(page)page.scrollIntoView({block:'start'});
 }
 async function operate(method,payload,button){
   const projectId=getProjectId();
   if(!projectId){notify('Crée ou sélectionne un projet avant la conversion.',true);showModal();return;}
   if(!payload.source){notify('Aucun fichier source compatible. Importe ou génère d’abord le fichier.',true);return;}
   button.disabled=true;
   nodeText('utilityResult','Traitement du fichier du projet en cours…');
   try{
     const result=await api.call(method,{...payload,projectId});
     nodeText('utilityResult',result.path+'\n'+(result.note||'Fichier créé sur ton espace de travail local. Le fichier source a été conservé.'));
     await refreshFiles();
     refreshSources();
     notify('Fichier créé : '+result.path);
   }catch(error){
     nodeText('utilityResult','Échec : '+error.message);
     notify('Conversion impossible : '+error.message,true);
   }finally{button.disabled=false;}
 }
 $('#utilTerrainRun')?.addEventListener('click',e=>operate('processTerrain',
   {source:$('#utilTerrainSource').value,mode:$('#utilTerrainMode').value},e.currentTarget));
 $('#utilTextureRun')?.addEventListener('click',e=>operate('convertTexture',
   {source:$('#utilTextureSource').value},e.currentTarget));
 $('#utilConfigRun')?.addEventListener('click',e=>operate('convertConfig',
   {source:$('#utilConfigSource').value},e.currentTarget));
 for(const button of $$('[data-util-select]'))button.onclick=()=>select(button.dataset.utilSelect);
 for(const button of $$('[data-util-go]'))button.onclick=()=>showTab(button.dataset.utilGo);
 async function refreshStatus(){
   try{
     const v=await api.call('overview');
     const projects=getProjects();
     const files=getFiles();
     nodeText('utilStatusTools','Disponible · ANOMALIA Tools '+v.version+' (application locale)');
     nodeText('utilStatusWorkdrive',v.workspace+'\n'+projects.length+' projet(s) privé(s) enregistrés.');
     nodeText('utilStatusAssets',getProjectId()?files.filter(f=>f.type==='file'&&f.path.startsWith('Content/')).length+
       ' fichier(s) dans Content pour le projet actif.':'Aucun projet actif.');
     nodeText('utilStatusUnreal','Non vérifié automatiquement. L’outil Addon Builder peut contrôler un chemin UE5 configuré.');
   }catch(err){nodeText('utilStatusTools','Indisponible : '+err.message);}
 }
 $('#utilRefreshStatus')?.addEventListener('click',refreshStatus);
 const menus={
  file:[['Nouveau projet',()=>showModal()],['Explorer les projets',()=>showTab('home')],
    ['Workbench',()=>showTab('workbench')],['Publisher / export',()=>showTab('publisher')]],
  view:[['Vue d’ensemble',()=>showTab('home')],['Afficher les utilitaires',()=>{showTab('utilities');select('terrainProcessor');}],
    ['Statut des modules',()=>showTab('systemStatus')],['Voir mises à jour',()=>showTab('updates')]],
  settings:[['Paramètres Unreal / plugin',()=>showTab('addon')],['Ressources et modèles',()=>showTab('objects')],
    ['Mises à jour',()=>showTab('updates')]],
  tools:[['Workbench',()=>showTab('workbench')],['Object Builder',()=>showTab('objects')],
    ['Terrain Builder',()=>showTab('terrain')],['Terrain Processor',()=>{showTab('utilities');select('terrainProcessor');}],
    ['Central Economy',()=>showTab('economy')],['Addon Builder',()=>showTab('addon')],
    ['Tex View',()=>{showTab('utilities');select('texview');}],['Publisher',()=>showTab('publisher')]],
  help:[['Statut / informations de version',()=>showTab('systemStatus')],
    ['Mises à jour automatiques',()=>showTab('updates')]]
 };
 const dropdown=$('#toolsMenuDropdown');
 let anchor=null;
 function closeMenu(){dropdown.hidden=true;anchor?.setAttribute('aria-expanded','false');anchor=null;}
 for(const button of $$('[data-tools-menu]')){
   button.setAttribute('aria-expanded','false');
   button.onclick=()=>{
     if(anchor===button&&!dropdown.hidden){closeMenu();return;}
     closeMenu();anchor=button;button.setAttribute('aria-expanded','true');
     dropdown.replaceChildren();
     const items=menus[button.dataset.toolsMenu]||[];
     for(const [label,handler] of items){
       const opt=document.createElement('button');opt.type='button';
       opt.setAttribute('role','menuitem');opt.textContent=label;
       opt.onclick=()=>{closeMenu();handler();};
       dropdown.append(opt);
     }
     dropdown.style.left=button.offsetLeft+'px';
     dropdown.hidden=false;
     dropdown.querySelector('button')?.focus();
   };
 }
 document.addEventListener('pointerdown',event=>{
   if(!dropdown.hidden&&!event.target.closest('.toolsMenuBar'))closeMenu();
 });
 document.addEventListener('keydown',event=>{
   if(event.key==='Escape'&&!dropdown.hidden){closeMenu();anchor?.focus();}
 });
 return {select,refreshStatus,refreshSources};
}
