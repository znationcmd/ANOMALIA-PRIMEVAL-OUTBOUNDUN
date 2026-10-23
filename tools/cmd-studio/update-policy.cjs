'use strict';
const path=require('node:path');
const fs=require('node:fs');
const crypto=require('node:crypto');
const PUBLIC_KEY=`-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEA/MAUxeQ03KyL9gC3EfC+7g7Nbt9eE/Gt4qtojF0NF2c=
-----END PUBLIC KEY-----`;
const INTERVAL_MS=6*60*60*1000;
function validateFeedUrl(value){
  if(typeof value!=='string'||value.length>1024)throw Error('Adresse de mises à jour invalide');
  let url;try{url=new URL(value);}catch{throw Error('URL de mises à jour invalide');}
  if(url.protocol!=='https:'||!url.hostname||url.username||url.password||url.search||url.hash)
    throw Error('Utilise une adresse HTTPS privée, sans identifiants dans l’URL.');
  if(['github.com','api.github.com','raw.githubusercontent.com','objects.githubusercontent.com'].includes(url.hostname))
    throw Error('Utilise un serveur de mises à jour privé, pas des artefacts GitHub publics.');
  if(url.hostname==='localhost'||url.hostname==='127.0.0.1'||url.hostname==='::1')
    throw Error('Le serveur de mises à jour doit être accessible en HTTPS.');
  if(!url.pathname.endsWith('/'))url.pathname+='/';
  return url.href;
}
function redactError(error) {
  const msg=String(error?.message||error||'Erreur de mises à jour');
  return msg.replace(/Bearer\s+[^\s]+/ig,'Bearer [masqué]')
    .replace(/(token|authorization|password|secret)=([^\s&#]+)/ig,'$1=[masqué]')
    .slice(0,300);
}
function writeJsonAtomic(file,data){
  const temp=file+'.'+crypto.randomUUID()+'.tmp';
  fs.mkdirSync(path.dirname(file),{recursive:true});
  try{fs.writeFileSync(temp,JSON.stringify(data,null,2),{encoding:'utf8',mode:0o600});fs.renameSync(temp,file);}
  finally{if(fs.existsSync(temp))fs.rmSync(temp,{force:true});}
}
function readPrivateSettings(file){
  try{
    const s=JSON.parse(fs.readFileSync(file,'utf8'));
    return {enabled:s.enabled===true,url:s.url?validateFeedUrl(s.url):'',tokenEncrypted:typeof s.tokenEncrypted==='string'?s.tokenEncrypted:''};
  }catch{return {enabled:false,url:'',tokenEncrypted:''};}
}
module.exports={PUBLIC_KEY,INTERVAL_MS,validateFeedUrl,redactError,writeJsonAtomic,readPrivateSettings};
