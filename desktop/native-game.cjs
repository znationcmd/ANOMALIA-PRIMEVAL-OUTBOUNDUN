'use strict';
const fs=require('node:fs');
const path=require('node:path');
const {createHash}=require('node:crypto');
const {spawn}=require('node:child_process');
const MANIFEST=String.raw`D:\ANOMALIAZ\Jeu\installation.json`;
const WORLD='/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1';

function createNativeGameLauncher(io={readFileSync:fs.readFileSync,existsSync:fs.existsSync,spawn}){
 let active=null;
 return async function launchNativeGame(){
  if(active&&active.exitCode===null)return {launched:true,alreadyRunning:true,map:WORLD};
  let record;
  try{record=JSON.parse(io.readFileSync(MANIFEST,'utf8').replace(/^\uFEFF/,''));}
  catch{throw Error('Le vrai jeu SKARVIK n’est pas encore installé.');}
  if(record.state!=='AUTHENTIC_GAMEPLAY_VERIFIED'||record.standalonePackagedExe!==true||record.map!==WORLD)
   throw Error('L’installation du vrai jeu SKARVIK n’est pas validée.');
  if(typeof record.exe!=='string'||typeof record.packageRoot!=='string'||typeof record.sha256!=='string')
   throw Error('Installation du jeu incomplète.');
  const exe=path.win32.resolve(record.exe),root=path.win32.resolve(record.packageRoot);
  if(!/^(AnomaliaPrimeval|AnomaliaZPrigimalia)(-Win64-(Development|Shipping))?\.exe$/i.test(path.win32.basename(exe))||
     !exe.toLowerCase().startsWith(root.toLowerCase()+'\\')||
     !root.toLowerCase().startsWith('d:\\anomaliaz\\jeu\\versions\\'))
   throw Error('Le lanceur doit ouvrir le jeu autonome, jamais Unreal Editor.');
  const paks=['AnomaliaPrimeval','AnomaliaZPrigimalia'].some(name=>io.existsSync(path.win32.join(root,name,'Content','Paks')));
  if(!io.existsSync(exe)||!paks)throw Error('Les fichiers du vrai jeu SKARVIK sont absents.');
  const hash=createHash('sha256').update(io.readFileSync(exe)).digest('hex');
  if(hash!==record.sha256.toLowerCase())throw Error('Le jeu installé ne correspond pas à la version vérifiée.');
  return await new Promise((resolve,reject)=>{
   let child;
   try{child=io.spawn(exe,[WORLD,'-d3d11','-sm5'],{cwd:root,detached:true,stdio:'ignore',windowsHide:false,shell:false});}
   catch{return reject(Error('Le vrai jeu SKARVIK n’a pas pu démarrer.'));}
   active=child;
   child.once('error',()=>{active=null;reject(Error('Le vrai jeu SKARVIK n’a pas pu démarrer.'));});
   child.once('exit',()=>{if(active===child)active=null;});
   child.once('spawn',()=>{child.unref();resolve({launched:true,map:WORLD,pid:child.pid});});
  });
 };
}
module.exports={createNativeGameLauncher,launchNativeGame:createNativeGameLauncher()};
