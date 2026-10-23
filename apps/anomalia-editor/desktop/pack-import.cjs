'use strict';
const path=require('node:path');
const fs=require('node:fs');
const crypto=require('node:crypto');
const {pipeline}=require('node:stream/promises');
const yauzl=require('yauzl');

const EXT=new Set(['.glb','.gltf','.fbx','.obj','.usd','.usdz','.blend','.uasset','.umap',
 '.png','.jpg','.jpeg','.webp','.tga','.bin','.json','.txt','.md','.mtl','.mhmat','.mhclo','.py','.wav','.ogg','.xml','.ini','.cfg']);
const MAX_FILES=7000;
const MAX_TOTAL=3*1024*1024*1024;
const MAX_SINGLE=320*1024*1024;
function safeEntry(name){
  if(typeof name!=='string'||name.length>350||name.includes('\\')||name.includes('\0')||
     name.startsWith('/')||/^[a-zA-Z]:/.test(name))throw Error('Archive : chemin non autorisé.');
  const parts=name.split('/');
  if(parts.some(x=>x==='..'||x==='.'||x===''))throw Error('Archive : chemin relatif dangereux.');
  if(parts.length>18)throw Error('Archive : profondeur non autorisée.');
  return parts;
}
async function digest(file){
  return new Promise((resolve,reject)=>{
    const hash=crypto.createHash('sha256');
    const stream=fs.createReadStream(file);
    stream.on('data',chunk=>hash.update(chunk));
    stream.on('error',reject);stream.on('end',()=>resolve(hash.digest('hex')));
  });
}
function openArchive(filename){
  return new Promise((resolve,reject)=>yauzl.open(filename,{lazyEntries:true,validateEntrySizes:true,decodeStrings:true},
     (err,zip)=>err?reject(err):resolve(zip)));
}
async function unzipSafe(filename,destination){
  const zip=await openArchive(filename);
  let files=0,total=0;
  return new Promise((resolve,reject)=>{
    let ended=false;
    const fail=e=>{
      if(ended)return;
      ended=true;zip.close();reject(e);
    };
    zip.on('error',fail);
    zip.on('end',()=>{if(!ended){ended=true;resolve({files,bytes:total});}});
    zip.on('entry',async entry=>{
      try{
        const directory=entry.fileName.endsWith('/');
        const entryName=directory?entry.fileName.slice(0,-1):entry.fileName;
        const parts=safeEntry(entryName);
        // Ignore Unix symlinks and special files, preventing escapes from root.
        const mode=(entry.externalFileAttributes>>>16)&0o170000;
        if(mode===0o120000|| (mode!==0&&mode!==0o100000&&mode!==0o040000))
          throw Error('Archive : liens et fichiers spéciaux refusés.');
        if(++files>MAX_FILES)throw Error('Archive contenant trop de fichiers.');
        const target=path.join(destination,...parts);
        const relative=path.relative(destination,target);
        if(relative.startsWith('..')||path.isAbsolute(relative))throw Error('Archive : chemin non autorisé.');
        if(directory){await fs.promises.mkdir(target,{recursive:true});zip.readEntry();return;}
        if(!EXT.has(path.extname(target).toLowerCase()))throw Error('Archive contenant des fichiers non autorisés : '+path.basename(target));
        if(entry.uncompressedSize>MAX_SINGLE||total+entry.uncompressedSize>MAX_TOTAL)
          throw Error('Archive trop volumineuse pour import sécurisé.');
        total+=entry.uncompressedSize;
        await fs.promises.mkdir(path.dirname(target),{recursive:true});
        const input=await new Promise((res,rej)=>zip.openReadStream(entry,(err,stream)=>err?rej(err):res(stream)));
        await pipeline(input,fs.createWriteStream(target,{flags:'wx',mode:0o600}));
        const stat=await fs.promises.stat(target);
        if(stat.size!==entry.uncompressedSize)throw Error('Extraction incomplète : '+entry.fileName);
        zip.readEntry();
      }catch(e){fail(e);}
    });
    zip.readEntry();
  });
}
async function verifyKnownManifests(directory){
  const candidates=[
    path.join(directory,'conversion-receipt.json'),
    path.join(directory,'manifest.json')
  ];
  for(const dir of await fs.promises.readdir(directory,{withFileTypes:true})){
    if(dir.isDirectory())candidates.push(path.join(directory,dir.name,'manifest.json'));
  }
  let verified=0;
  for(const file of candidates){
    let stat;
    try{stat=await fs.promises.stat(file);}catch{continue;}
    if(!stat.isFile()||stat.size>3*1024*1024)throw Error('Manifeste de ressources trop volumineux.');
    const manifest=JSON.parse(await fs.promises.readFile(file,'utf8'));
    if(!Array.isArray(manifest.models))continue;
    const parent=path.dirname(file);
    for(const model of manifest.models){
      if(!model||typeof model.file!=='string'||typeof model.sha256!=='string'||!(/^[a-f0-9]{64}$/.test(model.sha256)))
        throw Error('Manifeste de ressources invalide.');
      const target=path.resolve(parent,...safeEntry(model.file));
      const relative=path.relative(parent,target);
      if(!relative||relative.startsWith('..')||path.isAbsolute(relative))throw Error('Manifeste hors dossier autorisé.');
      // Staging est créé par l'importeur, les liens symboliques ZIP étant refusés :
      // ne pas résoudre le chemin natif Windows à travers les jonctions temporaires.
      const info=await fs.promises.lstat(target);
      if(!info.isFile()||info.isSymbolicLink())throw Error('Fichier de manifeste non autorisé.');
      if(model.bytes!==undefined&&info.size!==model.bytes)throw Error('Taille invalide : '+model.file);
      if(await digest(target)!==model.sha256)throw Error('Empreinte SHA-256 non conforme : '+model.file);
      verified++;
    }
  }
  return verified;
}
async function importArchive(filename,base){
  const resolved=path.resolve(filename);
  const stat=await fs.promises.lstat(resolved);
  if(!stat.isFile()||stat.isSymbolicLink()||!resolved.toLowerCase().endsWith('.zip')||
     stat.size>750*1024*1024)throw Error('Choisis une archive ZIP normale de 750 Mo maximum.');
  const hash=await digest(resolved);
  const packName=path.basename(resolved,'.zip').replace(/[^a-z0-9_-]/gi,'_').slice(0,65)||'pack';
  const packs=path.join(base,'imported-ANOMALIA-packs');
  const target=path.join(packs,packName+'-'+hash.slice(0,12));
  await fs.promises.mkdir(packs,{recursive:true});
  if(fs.existsSync(target))return {duplicate:true,folder:target,sha256:hash,files:0};
  const staging=path.join(packs,'.import-'+crypto.randomUUID());
  await fs.promises.mkdir(staging,{recursive:true});
  try{
    const result=await unzipSafe(resolved,staging);
    const verified=await verifyKnownManifests(staging);
    await fs.promises.rename(staging,target);
    return {duplicate:false,folder:target,sha256:hash,verified,...result};
  }catch(e){
    await fs.promises.rm(staging,{recursive:true,force:true});
    throw e;
  }
}
module.exports={importArchive,safeEntry,MAX_FILES,MAX_TOTAL};
