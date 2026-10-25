/**
 * ANOMALIA WorkForge, rendered inside the game's own UI on Windows and web.
 * The installed Windows game can display the real local ANOMALIA Tools catalogue.
 * A compiled plugin is never presented as already loaded into UE5.
 */
const CATEGORIES=['Tous','Véhicules','Armes','Bâtiments','Créatures','Survie','Cartes','Vêtements','Outils','Autres'];
const ICONS={Tous:'✦',Véhicules:'◈',Armes:'⌁',Bâtiments:'▣',Créatures:'◆',Survie:'✺',Cartes:'▤',Vêtements:'▥',Outils:'⚙',Autres:'⬡'};
function make(tag,cls='',label=''){
  const node=document.createElement(tag);
  if(cls)node.className=cls;
  if(label)node.textContent=label;
  return node;
}
export function createWorkshopPanel(){
 const page=document.getElementById('inGameWorkshop');
 if(!page)throw Error('Page WorkForge absente du jeu');
 const $=id=>page.querySelector('#'+id);
 let category='Tous',catalog={available:false,mods:[]},requestId=0,onlyFavorites=false;
 const favoriteKey='anomalia-workforge-favorites-v1';
 let favoriteIds=new Set();
 try{
   const saved=JSON.parse(localStorage.getItem(favoriteKey)||'[]');
   if(Array.isArray(saved))favoriteIds=new Set(saved.filter(id=>typeof id==='string'&&/^[a-z0-9][a-z0-9-]{1,100}$/.test(id)).slice(0,1000));
 }catch{favoriteIds=new Set();}
 function toggleFavorite(id){
   if(!/^[a-z0-9][a-z0-9-]{1,100}$/.test(String(id)))return;
   if(favoriteIds.has(id))favoriteIds.delete(id);else favoriteIds.add(id);
   try{localStorage.setItem(favoriteKey,JSON.stringify([...favoriteIds]));}
   catch{$('igwMessage').textContent='Les favoris sont disponibles dans cette session, mais le stockage local est inaccessible.';}
   counts();render();
 }
 function isOpen(){return !page.hidden;}
 function close(){page.hidden=true;}
 function counts(){
  $('igwCount').textContent=String(catalog.mods.length);
  $('igwSaved').textContent=String(catalog.mods.filter(m=>favoriteIds.has(m.id)).length);
  $('igwReady').textContent=String(catalog.mods.filter(m=>m.prepared).length);
 }
 function categories(){
  const host=$('igwCategories');host.replaceChildren();
  for(const name of CATEGORIES){
   const n=name==='Tous'?catalog.mods.length:catalog.mods.filter(m=>m.category===name).length;
   const button=make('button','igw-category'+(name===category?' active':''));
   button.type='button';
   button.append(make('span','igw-icon',ICONS[name]),make('strong','',name),make('small','',String(n)));
   button.onclick=()=>{category=name;categories();render();};
   host.append(button);
  }
 }
 function render(){
  const grid=$('igwGrid');grid.replaceChildren();
  const needle=$('igwSearch').value.trim().toLocaleLowerCase('fr');
  const mods=catalog.mods.filter(m=>(category==='Tous'||m.category===category)&&
   (!onlyFavorites||favoriteIds.has(m.id))&&
   (!needle||[m.title,m.category,m.version,m.description].some(v=>String(v||'').toLocaleLowerCase('fr').includes(needle))));
  $('igwVisible').textContent='('+mods.length+')';
  if(!mods.length){
   const empty=make('div','igw-empty');
   empty.append(make('span','igw-emptyIcon','✦'),
      make('h4','',catalog.mods.length?'Aucun résultat':'WorkForge est ouvert'),
      make('p','',catalog.mods.length?'Change ta recherche ou la catégorie.':
       'Aucun mod n’est encore publié dans ta bibliothèque locale. Crée un projet ANOMALIA Tools et ajoute-le à ta bibliothèque WorkForge pour qu’il apparaisse ici.'),
      make('p','igw-hint','Aucun faux mod affiché. Le chargeur des plugins Unreal Engine 5 reste à développer.'));
   grid.append(empty);
   return;
  }
  for(const mod of mods){
   const card=make('article','igw-card');
   const art=make('div','igw-art');
   art.append(make('span','igw-artIcon',ICONS[mod.category]||'✦'),
      make('small','',mod.category||'Autres'));
   const content=make('div','igw-cardBody');
   content.append(make('h4','',mod.title||'Mod ANOMALIA'),
      make('p','',mod.description||'Création ANOMALIA locale'),
      make('small','igw-version','Version '+(mod.version||'—')));
   const chips=make('div','igw-badges');
   chips.append(make('span','',mod.prepared?'Plugin préparé':'Sources du mod'),
      make('span','',mod.subscribed?'✓ Abonné':'Non abonné'));
   content.append(chips,make('p','igw-hint','État dans le jeu : plugin non chargé'));
   const actions=make('div','igw-cardActions');
   const favorite=make('button','igw-favorite',favoriteIds.has(mod.id)?'★ Retirer des favoris':'☆ Ajouter aux favoris');
   favorite.type='button';favorite.setAttribute('aria-pressed',String(favoriteIds.has(mod.id)));
   favorite.setAttribute('aria-label',favoriteIds.has(mod.id)?'Retirer '+mod.title+' des favoris':'Ajouter '+mod.title+' aux favoris');
   favorite.onclick=()=>toggleFavorite(mod.id);
   actions.append(favorite);
   content.append(actions);
   card.append(art,content);grid.append(card);
  }
 }
 async function refresh(){
  const id=++requestId;
  $('igwMessage').textContent='Lecture des mods locaux…';
  let result;
  try{
   result=window.anomaliaWorkshop?.list?await window.anomaliaWorkshop.list():
    {available:false,mods:[],message:'WorkForge est ouvert dans le jeu. Le navigateur ne peut pas lire la bibliothèque de mods Windows.'};
  }catch(error){
   result={available:false,mods:[],message:'Lecture impossible : '+(error?.message||'erreur locale')};
  }
  if(id!==requestId)return;
  catalog={available:!!result?.available,mods:Array.isArray(result?.mods)?result.mods.slice(0,200):[]};
  $('igwToolsState').textContent=catalog.available?'Bibliothèque détectée':'Non détectée';
  $('igwToolsState').className=catalog.available?'igw-green':'igw-warn';
  $('igwMessage').textContent=result?.message||'Catalogue local prêt.';
  counts();categories();render();
 }
 function open(){
  page.hidden=false;
  category='Tous';onlyFavorites=false;$('igwSearch').value='';$('igwFavorites').setAttribute('aria-pressed','false');
  categories();render();
  refresh();
  $('igwClose').focus();
 }
 $('igwClose').onclick=close;
 $('igwRefresh').onclick=refresh;
 $('igwFavorites').onclick=()=>{
   onlyFavorites=!onlyFavorites;
   $('igwFavorites').setAttribute('aria-pressed',String(onlyFavorites));
   $('igwFavorites').textContent=onlyFavorites?'★ Tous les mods':'☆ Mes favoris';
   render();
 };
 $('igwSearch').oninput=render;
 $('igwOpenTools').onclick=async()=>{
  if(!window.anomaliaServer?.openWorkshop){
   $('igwMessage').textContent='ANOMALIA Tools est une application Windows distincte. WorkForge reste ouvert dans le jeu.';
   return;
  }
  try{
   const outcome=await window.anomaliaServer.openWorkshop();
   $('igwMessage').textContent=outcome?.requested?
    'Ouverture d’ANOMALIA Tools demandée ; WorkForge reste ouvert dans le jeu.':
    'ANOMALIA Tools n’a pas pu être lancé, mais WorkForge reste utilisable.';
  }catch{
   $('igwMessage').textContent='ANOMALIA Tools n’a pas pu être lancé ; WorkForge reste ouvert.';
  }
 };
 document.addEventListener('keydown',event=>{
  if(isOpen()&&event.key==='Escape'){
   event.preventDefault();event.stopImmediatePropagation();close();
  }
 },true);
 return {open,close,isOpen,refresh};
}
