'use strict';
// Photos paysagères d'ambiance utilisées hors ligne après construction de l'installateur.
// Ces photos ne sont pas présentées comme des captures du jeu ANOMALIA.
// Licence : Unsplash License (voir https://unsplash.com/license).
const fs = require('node:fs');
const path = require('node:path');
const https = require('node:https');

const images = [
  ['hero.jpg','photo-1464822759023-fed622ff2c3b',1600],
  ['search.jpg','photo-1470770841072-f978cf4d019e',1200],
  ['projects.jpg','photo-1500534623283-312aade485b7',1200]
];
const dir = path.join(__dirname,'..','ui','generated');
fs.mkdirSync(dir,{recursive:true});
// Original ANOMALIA branding shipped with this repository, not a placeholder image.
// The app remains usable with its gradient fallback if the image is unavailable.
const anomaliaLogo=path.resolve(__dirname,'..','..','..','public','anomalia-logo.jpg');
if(fs.existsSync(anomaliaLogo)){
  fs.copyFileSync(anomaliaLogo,path.join(dir,'anomalia-logo.jpg'));
  console.log('Logo original ANOMALIA intégré à CMD Studio.');
}

function fetchPhoto(id,width,dest){
  return new Promise((resolve,reject)=>{
    const url='https://images.unsplash.com/'+id+'?w='+width+'&q=78&fit=crop&fm=jpg';
    const req=https.get(url,{timeout:20000,headers:{'User-Agent':'CMDStudioAssetBuild/0.2'}},res=>{
      if(res.statusCode!==200||!String(res.headers['content-type']||'').startsWith('image/')){
        res.resume();return reject(new Error('HTTP '+res.statusCode));
      }
      const parts=[];let size=0;
      res.on('data',chunk=>{
        size+=chunk.length;
        if(size>5*1024*1024){req.destroy(new Error('Image dépassant 5 Mo'));return;}
        parts.push(chunk);
      });
      res.on('error',reject);
      res.on('end',()=>{
        const data=Buffer.concat(parts);
        if(data.length<1000)return reject(new Error('Image vide'));
        fs.writeFileSync(dest,data);
        resolve(dest);
      });
    });
    req.on('timeout',()=>req.destroy(new Error('Téléchargement expiré')));
    req.on('error',reject);
  });
}
(async()=>{
  for(const [filename,id,w] of images){
    const dest=path.join(dir,filename);
    try{
      await fetchPhoto(id,w,dest);
      console.log('Image d’ambiance incluse localement : '+filename);
    }catch(e){
      console.warn('Photo indisponible ; dégradé CSS de secours : '+filename+' ('+e.message+')');
      // Évite de conserver un fichier partiellement téléchargé.
      if(fs.existsSync(dest)&&fs.statSync(dest).size<1000)fs.rmSync(dest,{force:true});
    }
  }
})();
