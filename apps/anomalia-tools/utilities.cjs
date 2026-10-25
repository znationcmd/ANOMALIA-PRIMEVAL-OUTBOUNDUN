'use strict';
// ANOMALIA/UE5-friendly operations. DayZ-only PAA, PBO and signature tools
// are NOT emulated: never claim compatibility with proprietary formats.
const fs=require('node:fs');
const path=require('node:path');
const {PNG}=require('pngjs');
const crypto=require('node:crypto');
function sourcePath(root,relative,folder,extensions){
  if(typeof relative!=='string'||relative.length>250||!/^[A-Za-z0-9_ .\/-]+$/.test(relative)||relative.includes('\\'))throw Error('Chemin invalide');
  const parts=relative.split('/');
  if(parts.some(p=>!p||p==='.'||p==='..'||p.startsWith('.'))||parts[0]!==folder.split('/')[0]||
     !relative.startsWith(folder+'/'))throw Error('Fichier hors du dossier '+folder);
  const file=path.resolve(root,...parts);
  if(!file.startsWith(path.resolve(root)+path.sep)||!extensions.includes(path.extname(file).toLowerCase()))throw Error('Fichier non pris en charge');
  let base=root;
  for(const segment of parts){
    base=path.join(base,segment);
    if(fs.existsSync(base)&&fs.lstatSync(base).isSymbolicLink())throw Error('Liens symboliques interdits');
  }
  if(!fs.existsSync(file)||!fs.statSync(file).isFile()||fs.statSync(file).size>32*1024*1024)throw Error('Fichier introuvable ou trop volumineux');
  return file;
}
function writeUnique(dir,name,extension,data){
  fs.mkdirSync(dir,{recursive:true});
  const clean=String(name).replace(/[^a-z0-9_-]/gi,'_').slice(0,70);
  const file=clean+'-'+crypto.randomUUID().slice(0,8)+extension;
  fs.writeFileSync(path.join(dir,file),data,{flag:'wx'});
  return file;
}
function processTerrain(root,{source,mode='normalize'}={}){
  if(!['normalize','invert','smooth'].includes(mode))throw Error('Traitement inconnu');
  const file=sourcePath(root,source,'Content/Terrain',['.png']);
  const png=PNG.sync.read(fs.readFileSync(file));
  const {width,height,data}=png;
  if(width<16||height<16||width*height>4096*4096)throw Error('Heightmap invalide (16 à 4096 pixels)');
  let pixels=new Uint8Array(width*height);
  for(let i=0;i<pixels.length;i++)pixels[i]=Math.round(data[i*4]*.2126+data[i*4+1]*.7152+data[i*4+2]*.0722);
  if(mode==='normalize'){
    let min=255,max=0;for(const p of pixels){min=Math.min(min,p);max=Math.max(max,p);}
    if(min<max){for(let i=0;i<pixels.length;i++)pixels[i]=Math.round((pixels[i]-min)*255/(max-min));}
  }else if(mode==='invert'){for(let i=0;i<pixels.length;i++)pixels[i]=255-pixels[i];}
  else{
    const out=new Uint8Array(pixels.length);
    for(let y=0;y<height;y++)for(let x=0;x<width;x++){
      let sum=0,total=0;
      for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++){
        const xx=Math.min(width-1,Math.max(0,x+dx)),yy=Math.min(height-1,Math.max(0,y+dy));
        sum+=pixels[yy*width+xx];total++;
      }
      out[y*width+x]=Math.round(sum/total);
    }
    pixels=out;
  }
  const image=new PNG({width,height});
  for(let i=0;i<pixels.length;i++){
    const offset=i*4,value=pixels[i];image.data[offset]=image.data[offset+1]=image.data[offset+2]=value;image.data[offset+3]=255;
  }
  const saved=writeUnique(path.join(root,'Content','Terrain'),path.basename(file,'.png')+'-'+mode,'.png',PNG.sync.write(image));
  return {saved:true,path:'Content/Terrain/'+saved,width,height,mode,format:'heightmap-png'};
}
function convertTexture(root,{source}={}){
  const file=sourcePath(root,source,'Content/Textures',['.png']);
  const {width,height,data}=PNG.sync.read(fs.readFileSync(file));
  if(width<1||height<1||width*height>4096*4096)throw Error('Texture trop grande');
  const tga=Buffer.allocUnsafe(18+width*height*4);tga.fill(0,0,18);
  tga[2]=2; // uncompressed true-color
  tga.writeUInt16LE(width,12);tga.writeUInt16LE(height,14);tga[16]=32;tga[17]=0x28; // top-left RGBA
  for(let i=0;i<width*height;i++){
    const n=i*4,o=18+n;
    tga[o]=data[n+2];tga[o+1]=data[n+1];tga[o+2]=data[n];tga[o+3]=data[n+3];
  }
  const saved=writeUnique(path.join(root,'Content','Textures'),path.basename(file,'.png')+'-Unreal','.tga',tga);
  return {saved:true,path:'Content/Textures/'+saved,width,height,format:'tga-32bit',note:'Texture TGA pour import dans Unreal Engine. Ce fichier n’est pas un .paa DayZ.'};
}
function convertConfig(root,{source}={}){
  const file=sourcePath(root,source,'Config',['.ini','.json','.cfg']);
  const raw=fs.readFileSync(file,'utf8');
  if(Buffer.byteLength(raw)>1024*1024)throw Error('Configuration supérieure à 1 Mo');
  const ext=path.extname(file).toLowerCase();
  let values;
  if(ext==='.json'){
    values=JSON.parse(raw);
    if(!values||typeof values!=='object')throw Error('JSON doit contenir un objet ou un tableau');
  }else{
    values={global:{}};
    let section='global';
    for(const line of raw.split(/\r?\n/)){
      const trimmed=line.trim();
      if(!trimmed||trimmed.startsWith(';')||trimmed.startsWith('#'))continue;
      const m=/^\[([A-Za-z0-9_. -]{1,100})\]$/.exec(trimmed);
      if(m){section=m[1];if(!values[section])values[section]={};continue;}
      const pair=/^([A-Za-z0-9_.-]{1,100})\s*=\s*(.*)$/.exec(trimmed);
      if(!pair)throw Error('Syntaxe INI/CFG non reconnue: '+trimmed.slice(0,65));
      if(Object.prototype.hasOwnProperty.call(values[section],pair[1]))throw Error('Clé dupliquée: '+pair[1]);
      values[section][pair[1]]=pair[2];
    }
  }
  const result={schema:'anomalia-converted-config',version:1,sourceFormat:ext.slice(1),sourceFile:path.basename(file),data:values};
  const filename=writeUnique(path.join(root,'Config','Converted'),path.basename(file,ext)+'-ANOMALIA','.json',Buffer.from(JSON.stringify(result,null,2)+'\n'));
  return {saved:true,path:'Config/Converted/'+filename,format:'json',note:'Conversion syntaxique uniquement. Vérifie les clés avant utilisation dans Unreal Engine.'};
}
module.exports={processTerrain,convertTexture,convertConfig};
