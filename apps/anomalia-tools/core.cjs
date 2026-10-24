'use strict';
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const {pipeline}=require('node:stream/promises');
const {PNG}=require('pngjs');
const yazl=require('yazl');
const native=require('./native-mods.cjs');
const {Workshop}=require('./workshop.cjs');
const SOURCE_EXT=new Set(['.js','.ts','.json','.xml','.ini','.cfg','.cpp','.h','.hpp','.cs','.txt','.md','.py','.uproject','.uplugin']);
const ASSET_EXT=new Set(['.glb','.gltf','.fbx','.obj','.usd','.png','.jpg','.jpeg','.webp','.tga','.wav','.ogg','.json','.xml','.ini']);
const PREVIEW_EXT=new Set(['.glb','.png','.jpg','.jpeg','.webp']);
function safeName(value){
  return String(value||'Projet').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9 _.-]/gi,'').trim().slice(0,55)||'Projet';
}
function atomicJSON(filename,data){
  const temp=filename+'.'+crypto.randomUUID()+'.tmp';
  fs.mkdirSync(path.dirname(filename),{recursive:true});
  try{fs.writeFileSync(temp,JSON.stringify(data,null,2),'utf8');fs.renameSync(temp,filename);}
  finally{if(fs.existsSync(temp))fs.rmSync(temp,{force:true});}
}
function readJSON(filename,fallback){
  try{return JSON.parse(fs.readFileSync(filename,'utf8'));}
  catch{return fallback;}
}
function validProjectId(value){
  if(typeof value!=='string'||!/^[a-z0-9][a-z0-9-]{1,100}$/.test(value))throw Error('Identifiant de projet incorrect');
  return value;
}
function relativeSafe(root,rel){
  if(typeof rel!=='string'||!rel||rel.length>260||rel.includes('\0')||rel.includes('\\'))throw Error('Chemin de fichier incorrect');
  const parts=rel.split('/');
  if(parts.some(p=>p==='..'||p==='.'||!p||p.startsWith('.')))throw Error('Chemin non autorisé');
  const full=path.resolve(root,...parts);
  if(!full.startsWith(path.resolve(root)+path.sep))throw Error('Accès extérieur au projet interdit');
  let check=path.resolve(root);
  for(const part of parts){
    check=path.join(check,part);
    if(fs.existsSync(check)&&fs.lstatSync(check).isSymbolicLink())throw Error('Liens symboliques non autorisés');
  }
  return full;
}
function terrainNoise(x,z,seed){
  let h=(Math.imul(x,374761393)+Math.imul(z,668265263)+Math.imul(seed,1442695041))|0;
  h=Math.imul(h^(h>>>13),1274126177);
  return ((h^(h>>>16))>>>0)/4294967295;
}
function smooth(t){return t*t*(3-2*t);}
function valueNoise(x,z,seed){
  const xx=Math.floor(x),zz=Math.floor(z),tx=smooth(x-xx),tz=smooth(z-zz);
  const a=terrainNoise(xx,zz,seed)*(1-tx)+terrainNoise(xx+1,zz,seed)*tx;
  const b=terrainNoise(xx,zz+1,seed)*(1-tx)+terrainNoise(xx+1,zz+1,seed)*tx;
  return a*(1-tz)+b*tz;
}
function heightAt(x,z,seed,octaves=5){
  let total=0,frequency=1,amp=1,totalAmp=0;
  for(let i=0;i<octaves;i++){total+=valueNoise(x*frequency,z*frequency,seed+i*239)*amp;totalAmp+=amp;frequency*=2;amp*=.5;}
  return Math.min(255,Math.max(0,Math.round(total/totalAmp*255)));
}
function validateEconomy(input){
  if(!input||typeof input!=='object'||!Array.isArray(input.items)||input.items.length>2000)throw Error('Catalogue de butin invalide');
  const ids=new Set();
  return {schema:'anomalia-economy',version:1,items:input.items.map(item=>{
    if(!item||typeof item.id!=='string'||!/^[a-z0-9_-]{1,64}$/i.test(item.id)||ids.has(item.id))throw Error('Identifiant de butin incorrect ou dupliqué');
    ids.add(item.id);
    const min=Number(item.min),max=Number(item.max),chance=Number(item.chance);
    if(!Number.isInteger(min)||!Number.isInteger(max)||min<0||max<min||max>100000||!Number.isFinite(chance)||chance<0||chance>100)
      throw Error('Quantités ou probabilités incorrectes');
    const category=String(item.category||'Divers').slice(0,45);
    return {id:item.id,category,min,max,chance};
  })};
}
class AnomaliaTools{
  constructor(dataDir){
    this.root=path.resolve(dataDir);
    fs.mkdirSync(this.root,{recursive:true});
  }
  overview(){
    const projects=this.listProjects();
    return {version:require('./package.json').version,privacy:'local-only',workspace:this.root,projects:projects.length,
      modules:['Workbench','Object Builder','Terrain Builder','Central Economy','Textures','Addon Builder','Publisher']};
  }
  getProjectPath(id){
    validProjectId(id);
    const root=path.join(this.root,id);
    if(!fs.existsSync(root)||!fs.statSync(root).isDirectory()||fs.lstatSync(root).isSymbolicLink()||
       !fs.existsSync(path.join(root,'anomalia.project.json')))throw Error('Projet introuvable');
    return root;
  }
  listProjects(){
    const projects=[];
    for(const dir of fs.readdirSync(this.root,{withFileTypes:true})){
      if(!dir.isDirectory()||!/^[a-z0-9][a-z0-9-]{1,100}$/.test(dir.name))continue;
      const f=path.join(this.root,dir.name,'anomalia.project.json');
      const p=readJSON(f,null);
      if(p&&p.schema==='anomalia-tools-project')projects.push({id:dir.name,name:p.name,createdAt:p.createdAt,description:p.description||''});
    }
    return projects.sort((a,b)=>b.createdAt.localeCompare(a.createdAt));
  }
  createProject({name='Nouveau mod',description=''}={}){
    name=safeName(name);description=String(description||'').slice(0,260);
    const id=name.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'').slice(0,35)+'-'+crypto.randomUUID().slice(0,8);
    const root=path.join(this.root,id);
    fs.mkdirSync(root,{recursive:true});
    for(const sub of ['Source','Content','Content/Models','Content/Textures','Content/Terrain','Config','Dist'])fs.mkdirSync(path.join(root,sub),{recursive:true});
    const meta={schema:'anomalia-tools-project',version:1,name,description,createdAt:new Date().toISOString(),engine:'Unreal Engine 5 - ANOMALIA'};
    atomicJSON(path.join(root,'anomalia.project.json'),meta);
    atomicJSON(path.join(root,'Config','economy.json'),validateEconomy({items:[
      {id:'water_bottle',category:'Nourriture',min:5,max:20,chance:30},
      {id:'bandage',category:'Médical',min:2,max:12,chance:17},
      {id:'wood_plank',category:'Construction',min:10,max:35,chance:55}
    ]}));
    fs.writeFileSync(path.join(root,'Source','README.md'),'# '+name+'\n\nCode, configurations et assets de ce mod ANOMALIA.\nFichiers conservés localement par utilisateur.\n');
    fs.writeFileSync(path.join(root,'Source','module.cpp'),'// '+name+'\n// Point de départ de module C++ pour ANOMALIA.\n// À intégrer dans un vrai module Unreal avec .Build.cs avant compilation.\n\nvoid InitAnomaliaMod() {\n    // Ajouter le code du mod ici.\n}\n');
    return {id,name,createdAt:meta.createdAt};
  }
  listFiles({projectId}={}){
    const root=this.getProjectPath(projectId),all=[];
    const walk=(folder,rel='',depth=0)=>{
      if(depth>8)return;
      for(const item of fs.readdirSync(folder,{withFileTypes:true})){
        if(item.name.startsWith('.')||item.isSymbolicLink())continue;
        const local=rel?rel+'/'+item.name:item.name;
        if(item.isDirectory()){all.push({path:local,type:'folder'});if(all.length>2000)return;walk(path.join(folder,item.name),local,depth+1);}
        else if(item.isFile())all.push({path:local,type:'file',size:fs.statSync(path.join(folder,item.name)).size});
        if(all.length>2000)return;
      }
    };walk(root);
    return all;
  }
  readText({projectId,file}={}){
    const root=this.getProjectPath(projectId),full=relativeSafe(root,file);
    if(!SOURCE_EXT.has(path.extname(full).toLowerCase()))throw Error('Extension non éditable');
    if(!fs.existsSync(full)||!fs.statSync(full).isFile()||fs.statSync(full).size>2*1024*1024)throw Error('Fichier absent ou trop volumineux');
    return {path:file,content:fs.readFileSync(full,'utf8')};
  }
  writeText({projectId,file,content}={}){
    const root=this.getProjectPath(projectId),full=relativeSafe(root,file);
    if(!SOURCE_EXT.has(path.extname(full).toLowerCase()))throw Error('Extension non éditable');
    if(typeof content!=='string'||Buffer.byteLength(content,'utf8')>2*1024*1024)throw Error('Document trop volumineux');
    fs.mkdirSync(path.dirname(full),{recursive:true});
    const temp=full+'.tmp-'+crypto.randomUUID();
    try{fs.writeFileSync(temp,content,'utf8');fs.renameSync(temp,full);}
    finally{if(fs.existsSync(temp))fs.rmSync(temp,{force:true});}
    return {saved:true,path:file,size:Buffer.byteLength(content)};
  }
  getEconomy({projectId}={}){
    const filename=path.join(this.getProjectPath(projectId),'Config','economy.json');
    return validateEconomy(readJSON(filename,{items:[]}));
  }
  saveEconomy({projectId,economy}={}){
    const clean=validateEconomy(economy);
    atomicJSON(path.join(this.getProjectPath(projectId),'Config','economy.json'),clean);
    return {saved:true,count:clean.items.length};
  }
  importAssets({projectId,paths}={}){
    const root=this.getProjectPath(projectId);
    if(!Array.isArray(paths)||paths.length>30)throw Error('Nombre de fichiers non valide');
    const imported=[];
    for(const source of paths){
      if(typeof source!=='string'||!fs.existsSync(source)||!fs.lstatSync(source).isFile()||fs.lstatSync(source).isSymbolicLink())
        throw Error('Fichier source manquant');
      const ext=path.extname(source).toLowerCase();
      if(!ASSET_EXT.has(ext))throw Error('Extension non autorisée : '+ext);
      const size=fs.statSync(source).size;
      if(size>150*1024*1024)throw Error('Fichier trop volumineux : 150 Mo maximum');
      const category=['.png','.jpg','.jpeg','.webp','.tga'].includes(ext)?'Textures':
        ['.wav','.ogg'].includes(ext)?'Audio':'Models';
      const dir=path.join(root,'Content',category);
      fs.mkdirSync(dir,{recursive:true});
      const base=safeName(path.basename(source,ext));
      const file=base+'-'+crypto.randomUUID().slice(0,6)+ext;
      fs.copyFileSync(source,path.join(dir,file),fs.constants.COPYFILE_EXCL);
      imported.push({path:'Content/'+category+'/'+file,size});
    }
    return imported;
  }
  previewAsset({projectId,file}={}){
    const root=this.getProjectPath(projectId);
    const full=relativeSafe(root,file),extension=path.extname(full).toLowerCase();
    if(!PREVIEW_EXT.has(extension))throw Error('Aperçu uniquement GLB, PNG, JPEG et WebP');
    if(!fs.existsSync(full)||fs.statSync(full).size>18*1024*1024||!fs.statSync(full).isFile())throw Error('Fichier trop volumineux pour aperçu (18 Mo)');
    const mime=extension==='.glb'?'model/gltf-binary':extension==='.webp'?'image/webp':extension==='.png'?'image/png':'image/jpeg';
    return {name:path.basename(full),mime,data:fs.readFileSync(full).toString('base64')};
  }
  generateTerrain({projectId,name='Terrain',seed=42,resolution=256,scaleMeters=2000,octaves=5}={}){
    const root=this.getProjectPath(projectId);
    resolution=Number(resolution);seed=Number(seed);scaleMeters=Number(scaleMeters);octaves=Number(octaves);
    if(![128,256,512,1024].includes(resolution)||!Number.isInteger(seed)||Math.abs(seed)>99999999||
       !Number.isFinite(scaleMeters)||scaleMeters<100||scaleMeters>64000||
       !Number.isInteger(octaves)||octaves<1||octaves>8)throw Error('Paramètres terrain invalides');
    name=safeName(name).replace(/ /g,'_');
    const png=new PNG({width:resolution,height:resolution});
    const freq=5/resolution;
    for(let z=0;z<resolution;z++)for(let x=0;x<resolution;x++){
      const v=heightAt(x*freq,z*freq,seed,octaves),idx=(z*resolution+x)*4;
      png.data[idx]=v;png.data[idx+1]=v;png.data[idx+2]=v;png.data[idx+3]=255;
    }
    const dest=path.join(root,'Content','Terrain');
    const filename=name+'-'+seed+'-'+resolution;
    const image=path.join(dest,filename+'.png'),json=path.join(dest,filename+'.json');
    fs.writeFileSync(image,PNG.sync.write(png));
    const meta={schema:'anomalia-terrain-heightmap',version:1,name,seed,resolution,
      scaleMeters,octaves,elevationRangeMeters:[0,500],format:'PNG grayscale 8-bit',
      note:'Heightmap de base. À rescaler/adapter aux paysages UE5 avant un import Landscape.'};
    atomicJSON(json,meta);
    return {image:'Content/Terrain/'+filename+'.png',metadata:'Content/Terrain/'+filename+'.json',resolution};
  }
  scaffoldNativeMod({projectId}={}){
    const root=this.getProjectPath(projectId);
    const project=readJSON(path.join(root,'anomalia.project.json'),{});
    return native.scaffoldNativeMod(root,projectId,project.name||'ANOMALIA Mod');
  }
  getNativeModStatus({projectId,engineRoot=''}={}){
    return native.buildStatus(this.getProjectPath(projectId),projectId,engineRoot);
  }
  validateNativeMod({projectId}={}){
    return native.validateNativeMod(this.getProjectPath(projectId),projectId);
  }
  async buildNativeMod({projectId,engineRoot=''}={}){
    return native.buildNativeMod(this.getProjectPath(projectId),projectId,engineRoot);
  }
  workshop(){return new Workshop(this);}
  listWorkshopMods(){return this.workshop().list();}
  publishWorkshopMod(payload={}){return this.workshop().publish(payload);}
  subscribeWorkshopMod(payload={}){return this.workshop().subscribe(payload);}
  prepareWorkshopMod(payload={}){return this.workshop().install(payload);}
  toggleWorkshopMod(payload={}){return this.workshop().toggle(payload);}
  exportWorkshopHostingManifest(payload={}){return this.workshop().exportHostingManifest(payload);}
  async packageMod({projectId}={}){
    const root=this.getProjectPath(projectId);
    const files=this.listFiles({projectId}).filter(x=>x.type==='file'&&!x.path.startsWith('Dist/')&&
      !x.path.split('/').some(p=>p.startsWith('.')||p==='.env'||p==='node_modules'));
    if(files.length>1500)throw Error('Projet trop volumineux (1500 fichiers maximum)');
    let total=0;
    for(const file of files){total+=file.size;if(total>250*1024*1024)throw Error('Taille totale maximum 250 Mo');}
    const manifest={
      schema:'anomalia-mod-package',version:1,projectId,
      project:readJSON(path.join(root,'anomalia.project.json'),{}).name,
      assets:files.map(x=>({path:x.path,size:x.size,sha256:crypto.createHash('sha256').update(fs.readFileSync(relativeSafe(root,x.path))).digest('hex')})),
      createdAt:new Date().toISOString(),
      note:'Archive de sources ANOMALIA, non compilée en .pak ni .pbo. Un SDK UE5 est requis pour un mod exécutable.'
    };
    const archivePath=path.join(root,'Dist',projectId+'-'+Date.now()+'.zip');
    const zip=new yazl.ZipFile();
    for(const file of files)zip.addFile(relativeSafe(root,file.path),file.path);
    zip.addBuffer(Buffer.from(JSON.stringify(manifest,null,2),'utf8'),'mod-manifest.json');
    zip.end();
    await pipeline(zip.outputStream,fs.createWriteStream(archivePath,{flags:'wx'}));
    return {path:archivePath,manifest,size:fs.statSync(archivePath).size};
  }
}
module.exports={AnomaliaTools,validateEconomy,relativeSafe,heightAt,safeName};
