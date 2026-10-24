'use strict';
// Local ANOMALIA Workshop: real user projects and compiled plugins only.
// No remote uploads, no imaginary community records, no claim that UE5 loaded a plugin.
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const {filesFor}=require('./native-mods.cjs');
const CATEGORIES=new Set(['Véhicules','Armes','Bâtiments','Créatures','Survie','Cartes','Vêtements','Outils','Autres']);
const MAX_FILES=2400,MAX_BYTES=512*1024*1024;

function safeId(value){
  if(typeof value!=='string'||!/^[a-z0-9][a-z0-9-]{1,100}$/.test(value))throw Error('Identifiant de mod non valide');
  return value;
}
function ordinary(file){
  return fs.existsSync(file)&&fs.lstatSync(file).isFile()&&!fs.lstatSync(file).isSymbolicLink();
}
function readJSON(file,fallback){
  if(!ordinary(file))return fallback;
  try{return JSON.parse(fs.readFileSync(file,'utf8'))}catch{return fallback;}
}
function atomicJSON(file,data){
  fs.mkdirSync(path.dirname(file),{recursive:true});
  const tmp=file+'.'+crypto.randomUUID()+'.tmp';
  try{fs.writeFileSync(tmp,JSON.stringify(data,null,2)+'\n',{flag:'wx'});fs.renameSync(tmp,file);}
  finally{if(fs.existsSync(tmp))fs.rmSync(tmp,{force:true});}
}
function treeFiles(root){
  if(!fs.existsSync(root)||!fs.statSync(root).isDirectory()||fs.lstatSync(root).isSymbolicLink())throw Error('Dossier plugin compilé manquant ou interdit');
  const files=[];let size=0;
  function visit(folder,prefix='',depth=0){
    if(depth>12)throw Error('Arborescence trop profonde');
    for(const d of fs.readdirSync(folder,{withFileTypes:true})){
      if(d.isSymbolicLink())throw Error('Le mod contient un lien symbolique interdit');
      const rel=prefix?prefix+'/'+d.name:d.name;
      if(d.isDirectory())visit(path.join(folder,d.name),rel,depth+1);
      else if(d.isFile()){
        const f=path.join(folder,d.name);
        size+=fs.statSync(f).size;files.push({rel,bytes:fs.statSync(f).size,sha256:crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex')});
        if(size>MAX_BYTES||files.length>MAX_FILES)throw Error('Mod trop volumineux pour la bibliothèque locale');
      }
    }
  }
  visit(root);return {files,bytes:size};
}
class Workshop{
  constructor(tools){
    this.tools=tools;
    this.root=path.join(tools.root,'_workshop');
    this.installed=path.join(this.root,'installed');
    this.stateFile=path.join(this.root,'library.json');
  }
  state(){
    const data=readJSON(this.stateFile,{});
    return {subscriptions:Array.isArray(data.subscriptions)?data.subscriptions:[],
      installed:data.installed&&typeof data.installed==='object'&&!Array.isArray(data.installed)?data.installed:{},
      profiles:data.profiles&&typeof data.profiles==='object'&&!Array.isArray(data.profiles)?data.profiles:{},
      activeProfile:typeof data.activeProfile==='string'?data.activeProfile:null};
  }
  save(data){atomicJSON(this.stateFile,{schema:'anomalia-workshop-local',version:1,...data});}
  published(projectId){
    const root=this.tools.getProjectPath(safeId(projectId));
    const info=readJSON(path.join(root,'Config','workshop.json'),null);
    return info?.schema==='anomalia-workshop-entry'&&info.projectId===projectId?info:null;
  }
  publish({projectId,title,description='',category='Autres',version='0.1.0'}={}){
    const root=this.tools.getProjectPath(safeId(projectId));
    const project=readJSON(path.join(root,'anomalia.project.json'),{});
    const name=String(title||project.name||'').trim();
    if(!name||name.length>90)throw Error('Titre invalide (90 caractères maximum)');
    if(typeof description!=='string'||description.length>650)throw Error('Description trop longue');
    if(!CATEGORIES.has(category))throw Error('Catégorie invalide');
    if(!/^\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?$/.test(version))throw Error('Version au format X.Y.Z requise');
    const previous=this.published(projectId);
    const entry={schema:'anomalia-workshop-entry',version:1,projectId,title:name,description,category,
      modVersion:version,author:'Création locale',visibility:'local-only',
      createdAt:previous?.createdAt||new Date().toISOString(),updatedAt:new Date().toISOString()};
    atomicJSON(path.join(root,'Config','workshop.json'),entry);
    return {published:true,visibility:'local-only',entry};
  }
  list(){
    const state=this.state();
    const result=[];
    for(const p of this.tools.listProjects()){
      const entry=this.published(p.id);
      if(!entry)continue;
      const root=this.tools.getProjectPath(p.id),mod=filesFor(root,p.id);
      const compiled=ordinary(path.join(mod.output,mod.name+'.uplugin'))&&
        ordinary(path.join(root,'Dist',mod.name+'-native-build.json'));
      const installed=state.installed[p.id]||null;
      result.push({id:p.id,title:entry.title,description:entry.description,category:entry.category,
        author:entry.author,version:entry.modVersion,updatedAt:entry.updatedAt,
        compiled,subscribed:state.subscriptions.includes(p.id),
        prepared:Boolean(installed),active:Boolean(installed?.enabled),
        installedVersion:installed?.version||null,plugin:mod.name,
        delivery:compiled?'Plugin UE5 compilé (jeu non vérifié)':'Sources uniquement',
        visibility:'local-only'});
    }
    return {entries:result,projects:this.tools.listProjects(),
      profiles:Object.entries(state.profiles).map(([id,p])=>({id,name:p.name,mods:p.mods.filter(x=>result.some(e=>e.id===x)),createdAt:p.createdAt})),
      activeProfile:state.activeProfile&&state.profiles[state.activeProfile]?state.activeProfile:null,
      stats:{total:result.length,subscribed:result.filter(e=>e.subscribed).length,
        prepared:result.filter(e=>e.prepared).length},
      connection:{tools:true,game:false,editor:false,community:false,
        message:'Bibliothèque de mods locale synchronisée avec ANOMALIA Tools. Le chargeur du jeu et la plateforme communautaire ne sont pas encore connectés.'},
      categories:[...CATEGORIES]};
  }
  createProfile({name}={}){
    if(typeof name!=='string'||!name.trim()||name.trim().length>60)throw Error('Nom de profil invalide (60 caractères maximum)');
    const state=this.state();
    if(Object.keys(state.profiles).length>=32)throw Error('Limite de 32 profils locaux atteinte');
    const id='profile-'+crypto.randomUUID();
    state.profiles[id]={name:name.trim(),mods:[],createdAt:new Date().toISOString()};
    if(!state.activeProfile)state.activeProfile=id;
    this.save(state);
    return {id,name:state.profiles[id].name,activeProfile:state.activeProfile,
      gameLoaded:false,note:'Profil créé dans ANOMALIA Tools uniquement. Le jeu ne charge pas encore automatiquement ces mods.'};
  }
  activateProfile({profileId}={}){
    const state=this.state();
    if(typeof profileId!=='string'||!Object.hasOwn(state.profiles,profileId))throw Error('Profil local introuvable');
    state.activeProfile=profileId;
    this.save(state);
    return {activeProfile:profileId,gameLoaded:false,
      note:'Profil actif dans la bibliothèque locale, non transmis au chargeur Unreal.'};
  }
  setProfileMod({profileId,projectId,value=true}={}){
    safeId(projectId);
    if(typeof value!=='boolean')throw Error('Action de profil invalide');
    const state=this.state();
    if(typeof profileId!=='string'||!Object.hasOwn(state.profiles,profileId))throw Error('Profil local introuvable');
    if(value&&!this.published(projectId))throw Error('Mod local introuvable');
    const profile=state.profiles[profileId];
    profile.mods=profile.mods.filter(id=>id!==projectId);
    if(value)profile.mods.push(projectId);
    this.save(state);
    return {profileId,projectId,inProfile:value,gameLoaded:false};
  }
  deleteProfile({profileId}={}){
    const state=this.state();
    if(typeof profileId!=='string'||!Object.hasOwn(state.profiles,profileId))throw Error('Profil local introuvable');
    delete state.profiles[profileId];
    if(state.activeProfile===profileId)state.activeProfile=Object.keys(state.profiles)[0]||null;
    this.save(state);
    return {deleted:true,activeProfile:state.activeProfile};
  }
  subscribe({projectId,value=true}={}){
    safeId(projectId);
    if(!this.published(projectId))throw Error('Mod non publié dans le Workshop local');
    const state=this.state();
    state.subscriptions=state.subscriptions.filter(x=>x!==projectId);
    if(value)state.subscriptions.push(projectId);
    this.save(state);
    return {subscribed:Boolean(value)};
  }
  install({projectId}={}){
    safeId(projectId);
    const entry=this.published(projectId);
    if(!entry)throw Error('Publie le mod dans le Workshop local avant de le préparer');
    const source=filesFor(this.tools.getProjectPath(projectId),projectId);
    const descriptor=path.join(source.output,source.name+'.uplugin');
    const record=path.join(this.tools.getProjectPath(projectId),'Dist',source.name+'-native-build.json');
    if(!ordinary(descriptor)||!ordinary(record))
      throw Error('Mod non compilé : lance RunUAT BuildPlugin dans Addon Builder avant installation');
    const evidence=readJSON(record,{});
    if(evidence.schema!=='anomalia-native-build'||evidence.plugin!==source.name||
       evidence.projectId!==projectId||evidence.platform!=='Win64')
      throw Error('Preuve de compilation native invalide');
    const info=treeFiles(source.output);
    if(info.files.length<2)throw Error('Plugin compilé incomplet');
    const target=path.join(this.installed,source.name),temp=target+'-staging-'+crypto.randomUUID();
    const backup=target+'-backup-'+crypto.randomUUID();
    fs.mkdirSync(this.installed,{recursive:true});
    if(fs.existsSync(target)&&fs.lstatSync(target).isSymbolicLink())throw Error('Emplacement cible symbolique interdit');
    let hadBackup=false;
    try{
      fs.cpSync(source.output,temp,{recursive:true,errorOnExist:true,force:false});
      const staged=treeFiles(temp);
      if(staged.files.length!==info.files.length||staged.files.some((x,i)=>x.rel!==info.files[i].rel||x.sha256!==info.files[i].sha256))
        throw Error('Intégrité du mod copié incorrecte');
      if(fs.existsSync(target)){fs.renameSync(target,backup);hadBackup=true;}
      fs.renameSync(temp,target);
      const state=this.state();
      state.installed[projectId]={plugin:source.name,version:entry.modVersion,enabled:state.installed[projectId]?.enabled??true,
        installedAt:new Date().toISOString(),bytes:info.bytes};
      this.save(state);
      if(hadBackup)fs.rmSync(backup,{recursive:true,force:true});
      return {prepared:true,plugin:source.name,version:entry.modVersion,
        gameLoaded:false,folder:target,
        message:'Plugin compilé copié dans la bibliothèque locale. Il ne sera jouable qu’après activation du chargeur de mods dans ANOMALIA.'};
    }catch(e){
      if(fs.existsSync(temp))fs.rmSync(temp,{recursive:true,force:true});
      if(hadBackup&&fs.existsSync(backup)){
        if(fs.existsSync(target))fs.rmSync(target,{recursive:true,force:true});
        fs.renameSync(backup,target);
      }
      throw e;
    }
  }
  exportHostingManifest({projectId}={}){
    safeId(projectId);
    const mod=this.published(projectId);
    if(!mod)throw Error('Ajoute ce mod au Workshop local avant export CMD Hosting');
    const project=this.tools.getProjectPath(projectId);
    const p=filesFor(project,projectId);
    const descriptor=path.join(p.output,p.name+'.uplugin');
    const report=path.join(project,'Dist',p.name+'-native-build.json');
    if(!ordinary(descriptor)||!ordinary(report))throw Error('Compile ce plugin Unreal avant de préparer sa fiche CMD Hosting');
    const proof=readJSON(report,{});
    if(proof.schema!=='anomalia-native-build'||proof.projectId!==projectId||
      proof.plugin!==p.name||proof.platform!=='Win64')throw Error('Rapport de compilation UE5 invalide');
    const info=treeFiles(p.output);
    if(info.files.length<2)throw Error('Plugin compilé incomplet');
    // No local paths, auth tokens, binaries, or remotely deployable URLs in the hand-off.
    return {schema:'anomalia-hosting-mod-handoff',version:1,target:'cmd-hosting',
      game:'anomalia-primeval-outboundun',source:'anomalia-tools-workshop',
      mod:{id:projectId,name:mod.title,version:mod.modVersion,category:mod.category,plugin:p.name,
        platform:'Win64',files:info.files.map(f=>({path:f.rel,size:f.bytes,sha256:f.sha256})),
        totalBytes:info.bytes},
      generatedAt:new Date().toISOString(),
      deployment:{ready:false,mode:'manifest-only',requires:'Dedicated ANOMALIA UE5 server agent and approved mod loader'},
      note:'Manifeste de transfert sans binaire. CMD Hosting ne peut pas installer ce plugin sur un serveur tant que le chargeur ANOMALIA et un agent dédié ne sont pas validés.'};
  }
  toggle({projectId,enabled}={}){
    safeId(projectId);
    if(typeof enabled!=='boolean')throw Error('État du mod invalide');
    const state=this.state();
    if(!state.installed[projectId])throw Error('Prépare ce mod avant de pouvoir changer son état');
    state.installed[projectId].enabled=enabled;
    this.save(state);
    return {enabled,gameLoaded:false,note:'État enregistré dans la bibliothèque locale, non transmis au jeu.'};
  }
}
module.exports={Workshop,treeFiles,CATEGORIES};
