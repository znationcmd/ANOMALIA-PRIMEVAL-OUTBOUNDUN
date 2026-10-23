'use strict';
const fs=require('node:fs');
const path=require('node:path');
const os=require('node:os');
const crypto=require('node:crypto');

const ACCEPTED=new Set(['.glb','.gltf','.fbx','.obj','.usd','.usdz','.blend','.uasset','.umap','.png','.jpg','.jpeg','.webp','.tga']);
const IGNORE=new Set(['.git','.svn','node_modules','Binaries','Intermediate','Saved','DerivedDataCache','Build','dist','release','.vs','__pycache__']);
const MAX_ENTRIES=35000;
function category(name,kind){
  const s=name.toLowerCase();
  if(kind==='map')return 'Cartes et secteurs';
  if(/vehic|vehicle|car|auto|sedan|bmw|truck|camion|van|suv|moto|bike|kart|buggy|quad|train|metro|helico|helicopt|aircraft|plane|avion|boat|jet.?ski|zodiac|submarine|tank|armored|ambulance|police|fire.?engine/.test(s))return 'Véhicules';
  if(/hous|maison|home|villa|building|batiment|apartment|immeuble|hlm|residence|warehouse|garage|bunker|shop|hospital|hangar|military|caserne|station|school/.test(s))return 'Bâtiments';
  if(/road|route|street|highway|bridge|pont|tunnel|rail|railway|track|sidewalk|pavement/.test(s))return 'Routes et infrastructures';
  if(/tree|arbre|pine|foliage|grass|herbe|rock|rocher|vegetation|forest|bush|nature|jungle/.test(s))return 'Nature';
  if(/texture|material|albedo|normal|roughness|metallic|basecolor|diffuse|_n\.|_d\./.test(s))return 'Matériaux et textures';
  if(/weapon|gun|item|loot|food|nourriture|medical|medicine|vetement|cloth|money|argent|drug|drogue/.test(s))return 'Objets et équipements';
  return 'Autres ressources';
}
function kindFor(filename){
  const lower=filename.toLowerCase();
  if(lower.endsWith('.anomalia.json'))return 'map';
  const ext=path.extname(filename).toLowerCase();
  if(ext==='.umap')return 'unreal-map';
  if(ext==='.uasset')return 'unreal-asset';
  if(['.png','.jpg','.jpeg','.webp','.tga'].includes(ext))return 'texture';
  if(ext==='.glb')return 'glb';
  return 'source-3d';
}
function isInside(parent,file){
  const p=path.relative(parent,file);
  return p!==''&&!p.startsWith('..'+path.sep)&&p!=='..'&&!path.isAbsolute(p);
}
class GameLibrary{
  constructor(directory){
    this.base=path.resolve(directory);
    this.preferences=path.join(this.base,'game-library.json');
    this.root='';this.items=[];this.signature='';this.loading=false;this.index=new Map();
    try{
      const data=JSON.parse(fs.readFileSync(this.preferences,'utf8'));
      if(typeof data.root==='string'&&path.isAbsolute(data.root))this.root=path.resolve(data.root);
    }catch{}
  }
  setFolder(root){
    const p=path.resolve(root);
    const stat=fs.lstatSync(p);
    if(!stat.isDirectory()||stat.isSymbolicLink())throw Error('Sélectionne un dossier local normal.');
    const temp=this.preferences+'.'+crypto.randomUUID()+'.tmp';
    fs.mkdirSync(this.base,{recursive:true});
    try{
      fs.writeFileSync(temp,JSON.stringify({root:p},null,2),{mode:0o600});
      fs.renameSync(temp,this.preferences);
    }finally{if(fs.existsSync(temp))fs.rmSync(temp,{force:true});}
    this.root=p;this.signature='';this.items=[];this.index.clear();
  }
  getStatus(){
    const counts={};
    for(const o of this.items)counts[o.category]=(counts[o.category]||0)+1;
    return {configured:Boolean(this.root),folder:this.root,items:this.items,counts,
      total:this.items.length,syncedAt:this.syncedAt||null};
  }
  async scan(){
    if(this.loading)return {changed:false,...this.getStatus()};
    if(!this.root){this.items=[];this.index.clear();return {changed:false,...this.getStatus()};}
    this.loading=true;
    try{
      const root=await fs.promises.realpath(this.root);
      const stat=await fs.promises.lstat(root);
      if(!stat.isDirectory()||stat.isSymbolicLink())throw Error('Dossier de jeu indisponible.');
      const entries=[],stack=[{dir:root,depth:0}];
      let visited=0;
      while(stack.length && visited<MAX_ENTRIES){
        const {dir,depth}=stack.pop();
        let list;
        try{list=await fs.promises.readdir(dir,{withFileTypes:true});}
        catch{continue;}
        for(const file of list){
          if(visited++>=MAX_ENTRIES)break;
          if(file.isSymbolicLink())continue;
          const full=path.join(dir,file.name);
          if(file.isDirectory()){
            if(depth<12&&!IGNORE.has(file.name)&&!file.name.startsWith('.'))stack.push({dir:full,depth:depth+1});
          }else if(file.isFile()){
            const kind=kindFor(file.name);
            const ext=path.extname(file.name).toLowerCase();
            if(!ACCEPTED.has(ext) && kind!=='map')continue;
            let info;
            try{info=await fs.promises.stat(full);}catch{continue;}
            if(info.size<=0 || info.size>2*1024*1024*1024)continue;
            const relative=path.relative(root,full).split(path.sep).join('/');
            const item={id:crypto.createHash('sha256').update(relative.toLowerCase()).digest('hex').slice(0,24),
              name:file.name,relative,kind,category:category(relative,kind),
              bytes:info.size,mtimeMs:Math.round(info.mtimeMs),
              canPlace:kind==='glb'&&info.size<=14*1024*1024,
              canOpen:kind==='map'&&info.size<=45*1024*1024};
            entries.push(item);
          }
        }
      }
      entries.sort((a,b)=>a.category.localeCompare(b.category,'fr')||a.name.localeCompare(b.name,'fr'));
      const signature=crypto.createHash('sha256').update(entries.map(x=>x.id+':'+x.bytes+':'+x.mtimeMs).join('|')).digest('hex');
      const changed=signature!==this.signature;
      this.signature=signature;
      this.items=entries;
      this.index=new Map(entries.map(o=>[o.id,o]));
      this.syncedAt=new Date().toISOString();
      return {changed,...this.getStatus()};
    }finally{this.loading=false;}
  }
  async read(id){
    const item=this.index.get(id);
    if(!item)throw Error('Fichier absent du catalogue. Actualise la bibliothèque.');
    if(!item.canPlace&&!item.canOpen)throw Error('Cette ressource doit être convertie ou ouverte dans Unreal Engine avant son utilisation.');
    const root=await fs.promises.realpath(this.root);
    const full=await fs.promises.realpath(path.join(root,...item.relative.split('/')));
    if(!isInside(root,full))throw Error('Chemin non autorisé.');
    const info=await fs.promises.stat(full);
    const limit=item.canPlace?14*1024*1024:45*1024*1024;
    if(!info.isFile()||info.size>limit)throw Error('Ressource trop volumineuse.');
    const data=await fs.promises.readFile(full);
    if(item.canPlace&&data.subarray(0,4).toString()!=='glTF')throw Error('Signature GLB incorrecte.');
    return {name:item.name,kind:item.kind,data:item.canPlace?data.toString('base64'):data.toString('utf8'),bytes:data.length};
  }
}
module.exports={GameLibrary,category,kindFor,isInside,MAX_ENTRIES};
