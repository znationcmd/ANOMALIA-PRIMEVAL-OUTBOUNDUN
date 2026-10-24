'use strict';
const fs=require('node:fs');
const path=require('node:path');
const {shell}=require('electron');
const {spawn}=require('node:child_process');
const {discoverInstalledProject}=require('./installed-project.cjs');
const IGNORE=new Set(['Intermediate','Saved','Binaries','DerivedDataCache','Build','node_modules','.git']);
const MAX_MAPS=250;
class UnrealBridge{
 constructor(userData){
  this.file=path.join(userData,'unreal-project-link.json');
  this.linked='';
  try{const x=JSON.parse(fs.readFileSync(this.file,'utf8'));if(typeof x.project==='string')this.linked=x.project;}catch{}
 }
 async inspectProject(projectPath){
  if(process.platform!=='win32')throw Error('Le véritable Unreal Editor doit être lancé depuis Windows.');
  if(typeof projectPath!=='string'||!projectPath.toLowerCase().endsWith('.uproject'))throw Error('Sélectionne un fichier .uproject.');
  const real=await fs.promises.realpath(projectPath);
  const info=await fs.promises.lstat(real);
  if(!info.isFile()||info.isSymbolicLink()||info.size>1024*1024)throw Error('Fichier projet Unreal non valide.');
  const raw=await fs.promises.readFile(real,'utf8'),config=JSON.parse(raw.replace(/^\uFEFF/,''));
  if(!config||typeof config!=='object'||!Array.isArray(config.Modules))throw Error('Fichier .uproject invalide ou incomplet.');
  const content=path.join(path.dirname(real),'Content');
  const maps=[];
  let examined=0;
  const stack=[content];
  while(stack.length&&examined<20000&&maps.length<MAX_MAPS){
    const dir=stack.pop();
    let entries;
    try{entries=await fs.promises.readdir(dir,{withFileTypes:true});}catch{continue;}
    for(const entry of entries){
      if(examined++>=20000)break;
      if(entry.isSymbolicLink())continue;
      const full=path.join(dir,entry.name);
      if(entry.isDirectory()&&!IGNORE.has(entry.name))stack.push(full);
      else if(entry.isFile()&&entry.name.toLowerCase().endsWith('.umap')){
        maps.push(path.relative(content,full).split(path.sep).join('/'));
        if(maps.length>=MAX_MAPS)break;
      }
    }
  }
  maps.sort((a,b)=>a.localeCompare(b,'fr'));
  return {linked:true,project:real,projectName:path.basename(real,'.uproject'),
    engine:typeof config.EngineAssociation==='string'?config.EngineAssociation:'Non précisé',
    maps,mapCount:maps.length,mapLimitReached:maps.length===MAX_MAPS,
    note:'Les fichiers .umap doivent être ouverts dans Unreal Engine. ANOMALIA Editor ne les convertit pas en scènes Three.js.'};
 }
 async status(){
  try{
   const installed=discoverInstalledProject();
   if(installed)return {...await this.inspectProject(installed.project),...installed};
  }catch(error){return {linked:false,maps:[],mapCount:0,warning:error.message};}
  if(!this.linked)return {linked:false,maps:[],mapCount:0};
  try{return await this.inspectProject(this.linked);}
  catch{return {linked:false,maps:[],mapCount:0,warning:'Le projet Unreal lié est inaccessible. Relie le fichier .uproject.'};}
 }
 async link(filename){
  const data=await this.inspectProject(filename);
  const tmp=this.file+'.tmp';
  await fs.promises.mkdir(path.dirname(this.file),{recursive:true});
  await fs.promises.writeFile(tmp,JSON.stringify({project:data.project},null,2),{mode:0o600});
  await fs.promises.rename(tmp,this.file);
  this.linked=data.project;
  return data;
 }
 async launch(selectedMap){
  const data=await this.status();
  if(!data.linked)throw Error('Liaison du projet UE5 requise.');
  if(data.automatic){
   const relative=selectedMap||data.mapPackage.replace('/Game/','')+'.umap';
   if(typeof relative!=='string'||!(/^[A-Za-z0-9_\/-]+\.umap$/.test(relative))||!data.maps.includes(relative))throw Error('Carte absente du projet actif.');
   const map='/Game/'+relative.slice(0,-5);
   if(typeof data.engineRoot!=='string'||!path.isAbsolute(data.engineRoot))throw Error('Moteur Unreal installé introuvable.');
   const editor=path.join(data.engineRoot,'Engine','Binaries','Win64','UnrealEditor.exe');
   if(!(await fs.promises.stat(editor)).isFile())throw Error('Unreal Editor est absent.');
   // No shell expansion. Map arguments are drawn exclusively from the scanned project.
   await new Promise((resolve,reject)=>{
    const child=spawn(editor,[data.project,map,'-d3d11','-sm5'],{shell:false,detached:true,stdio:'ignore',cwd:data.projectRoot});
    child.once('error',reject);child.once('spawn',()=>{child.unref();resolve();});
   });
   return {launched:true,projectName:data.projectName,engine:data.engine,mapPackage:map,commit:data.commit};
  }
  if(selectedMap)throw Error('Le choix de carte nécessite le projet installé synchronisé.');
  // Open the actual Unreal project through the registered Epic/Unreal Windows file handler.
  // Never interpret raw user-provided commands or paths as shell arguments.
  const error=await shell.openPath(data.project);
  if(error)throw Error('Ouverture Unreal impossible : '+error+'. Vérifie Unreal Engine et l’association des fichiers .uproject.');
  return {launched:true,projectName:data.projectName,engine:data.engine};
 }
}
module.exports={UnrealBridge};
