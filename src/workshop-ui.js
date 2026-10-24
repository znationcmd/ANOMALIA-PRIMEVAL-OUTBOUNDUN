/**
 * ANOMALIA Workshop, rendered inside the game's own UI on Windows and web.
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
 if(!page)throw Error('Page Workshop absente du jeu');
 const $=id=>page.querySelector('#'+id);
 let category='Tous',catalog={available:false,mods:[]},requestId=0;
 function isOpen(){return !page.hidden;}
 function close(){page.hidden=true;}
 function counts(){
  $('igwCount').textContent=String(catalog.mods.length);
  $('igwSaved').textContent=String(catalog.mods.filter(m=>m.subscribed).length);
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
   (!needle||[m.title,m.category,m.version,m.description].some(v=>String(v||'').toLocaleLowerCase('fr').includes(needle))));
  $('igwVisible').textContent='('+mods.length+')';
  if(!mods.length){
   const empty=make('div','igw-empty');
   empty.append(make('span','igw-emptyIcon','✦'),
      make('h4','',catalog.mods.length?'Aucun résultat':'Ton Workshop est ouvert'),
      make('p','',catalog.mods.length?'Change ta recherche ou la catégorie.':
       'Aucun mod n’est encore publié dans ta bibliothèque locale. Crée un projet ANOMALIA Tools et ajoute-le au Workshop pour qu’il apparaisse ici.'),
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
   card.append(art,content);grid.append(card);
  }
 }
 async function refresh(){
  const id=++requestId;
  $('igwMessage').textContent='Lecture des mods locaux…';
  let result;
  try{
   result=window.anomaliaWorkshop?.list?await window.anomaliaWorkshop.list():
    {available:false,mods:[],message:'Le Workshop est ouvert dans le jeu. Sur le navigateur, la bibliothèque de mods Windows ne peut pas être lue.'};
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
  category='Tous';$('igwSearch').value='';
  categories();render();
  refresh();
  $('igwClose').focus();
 }
 $('igwClose').onclick=close;
 $('igwRefresh').onclick=refresh;
 $('igwSearch').oninput=render;
 $('igwOpenTools').onclick=async()=>{
  if(!window.anomaliaServer?.openWorkshop){
   $('igwMessage').textContent='ANOMALIA Tools est une application Windows distincte. Le Workshop reste ouvert dans le jeu.';
   return;
  }
  try{
   const outcome=await window.anomaliaServer.openWorkshop();
   $('igwMessage').textContent=outcome?.requested?
    'Ouverture d’ANOMALIA Tools demandée ; le Workshop intégré reste visible ici.':
    'ANOMALIA Tools n’a pas pu être lancé, mais le Workshop intégré fonctionne.';
  }catch{
   $('igwMessage').textContent='ANOMALIA Tools n’a pas pu être lancé ; le Workshop intégré reste ouvert.';
  }
 };
 document.addEventListener('keydown',event=>{
  if(isOpen()&&event.key==='Escape'){
   event.preventDefault();event.stopImmediatePropagation();close();
  }
 },true);
 return {open,close,isOpen,refresh};
}
