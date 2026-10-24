'use strict';
/**
 * Read-only, bounded bridge from ANOMALIA Tools' user workspace to the installed game.
 * No file modifications, arbitrary-path input, executables, or remote URLs.
 */
const fs=require('node:fs');
const path=require('node:path');

const CATEGORIES=new Set(['Véhicules','Armes','Bâtiments','Créatures','Survie','Cartes','Vêtements','Outils','Autres']);
function safeFile(file,maxBytes=64*1024){
  try{
    const s=fs.lstatSync(file);
    if(!s.isFile()||s.isSymbolicLink()||s.size>maxBytes)return null;
    return fs.readFileSync(file,'utf8');
  }catch{return null;}
}
function safeJSON(file,maxBytes){
  const contents=safeFile(file,maxBytes);
  if(contents===null)return null;
  try{return JSON.parse(contents);}catch{return null;}
}
function directory(file){
  try{const s=fs.lstatSync(file);return s.isDirectory()&&!s.isSymbolicLink();}
  catch{return false;}
}
function clean(value,max=120){return typeof value==='string'?value.slice(0,max):'';}
function listLocalWorkshop(appDataDir){
  if(typeof appDataDir!=='string'||!path.isAbsolute(appDataDir))throw Error('Dossier utilisateur invalide');
  const toolsDir=path.join(appDataDir,'ANOMALIA Tools');
  const workspace=path.join(toolsDir,'private-workspaces');
  const empty={available:false,mods:[],source:'ANOMALIA Tools — bibliothèque locale',
    connectedToGame:false,message:'Aucune bibliothèque locale ANOMALIA Tools détectée sur cet ordinateur.'};
  if(!directory(toolsDir)||!directory(workspace))return empty;
  const libraryFolder=path.join(workspace,'_workshop');
  const state=directory(libraryFolder)?safeJSON(path.join(libraryFolder,'library.json'),256*1024):null;
  const subscriptions=new Set(Array.isArray(state?.subscriptions)?
    state.subscriptions.filter(s=>typeof s==='string'&&/^[a-z0-9][a-z0-9-]{1,100}$/.test(s)).slice(0,1000):[]);
  const installed=(state?.installed&&typeof state.installed==='object'&&!Array.isArray(state.installed))?state.installed:{};
  const mods=[];
  // User-generated project names are untrusted. Never traverse a symlink.
  for(const d of fs.readdirSync(workspace,{withFileTypes:true}).slice(0,400)){
    if(mods.length>=200)break;
    const id=d.name;
    if(!d.isDirectory()||!/^[a-z0-9][a-z0-9-]{1,100}$/.test(id))continue;
    const folder=path.join(workspace,id),configDir=path.join(folder,'Config');
    if(!directory(folder)||!directory(configDir))continue;
    const project=safeJSON(path.join(folder,'anomalia.project.json'),64*1024);
    const entry=safeJSON(path.join(configDir,'workshop.json'),64*1024);
    if(project?.schema!=='anomalia-tools-project'||entry?.schema!=='anomalia-workshop-entry'||
       entry.projectId!==id)continue;
    const install=Object.hasOwn(installed,id)&&installed[id]&&typeof installed[id]==='object'?installed[id]:null;
    mods.push({
      id,title:clean(entry.title,90)||clean(project.name,90)||id,
      description:clean(entry.description,650),author:'Création locale',
      category:CATEGORIES.has(entry.category)?entry.category:'Autres',
      version:clean(entry.modVersion,45)||'0.1.0',
      subscribed:subscriptions.has(id),
      prepared:Boolean(install),
      enabled:Boolean(install?.enabled),
      // "prepared" is not "loaded": the UE5 game mod loader is not integrated.
      loadedInGame:false,
      updatedAt:clean(entry.updatedAt,35)
    });
  }
  mods.sort((a,b)=>b.updatedAt.localeCompare(a.updatedAt));
  return {available:true,mods,source:'ANOMALIA Tools — bibliothèque locale',
    connectedToGame:false,message:'Projets trouvés dans ANOMALIA Tools. Le chargement des mods UE5 dans le jeu reste à développer.'};
}
module.exports={listLocalWorkshop};
