'use strict';
const fs=require('node:fs');
const path=require('node:path');
const {spawn}=require('node:child_process');
const PROJECT_ROOT='D:\\ANOMALIA\\unreal';
const MAP_ROOT=path.join(PROJECT_ROOT,'Content');
function findProject(){
 if(!fs.existsSync(PROJECT_ROOT))return null;
 const candidates=fs.readdirSync(PROJECT_ROOT).filter(n=>n.toLowerCase().endsWith('.uproject'));
 const preferred=candidates.find(n=>n.toLowerCase()==='anomaliaprimeval.uproject');
 return candidates.length?path.join(PROJECT_ROOT,preferred||candidates[0]):null;
}
function listMaps(){
 const project=findProject();
 if(!project)return {connected:false,project:null,maps:[],error:'Projet Unreal introuvable sur D:'};
 const maps=[],stack=[MAP_ROOT];
 while(stack.length){
  const folder=stack.pop();if(!fs.existsSync(folder))continue;
  for(const entry of fs.readdirSync(folder,{withFileTypes:true})){
   if(entry.isSymbolicLink())continue;
   const full=path.join(folder,entry.name);
   if(entry.isDirectory())stack.push(full);
   else if(entry.isFile()&&entry.name.toLowerCase().endsWith('.umap')){
    const relative=path.relative(MAP_ROOT,full).replace(/\\/g,'/');
    const stats=fs.statSync(full);
    maps.push({name:path.basename(entry.name,'.umap'),package:'/Game/'+relative.replace(/\.umap$/i,''),relative,size:stats.size,modified:stats.mtime.toISOString()});
   }
  }
 }
 maps.sort((a,b)=>a.package.localeCompare(b.package));
 return {connected:true,project,maps,count:maps.length};
}
function openInUnreal(packageName){
 const inventory=listMaps();
 if(!inventory.connected)throw Error(inventory.error);
 if(typeof packageName!=='string'||!inventory.maps.some(m=>m.package===packageName))throw Error('Carte inconnue ou non installée');
 // The project file opens the actual UE editor. A map can be selected by a validated local package path.
 const map=inventory.maps.find(m=>m.package===packageName);
 const candidates=[
  process.env.ANOMALIA_UNREAL_EDITOR_EXE,
  process.env.UE_EDITOR_EXE,
  'C:\\Program Files\\Epic Games\\UE_5.8\\Engine\\Binaries\\Win64\\UnrealEditor.exe',
  'D:\\Epic Games\\UE_5.8\\Engine\\Binaries\\Win64\\UnrealEditor.exe',
  'D:\\UE_5.8\\Engine\\Binaries\\Win64\\UnrealEditor.exe'
 ];
 const exe=candidates.find(candidate=>candidate&&fs.existsSync(candidate));
 if(!exe)throw Error('UnrealEditor.exe introuvable. Définir ANOMALIA_UNREAL_EDITOR_EXE avec le chemin exact de Unreal Engine 5.8.');
 const child=spawn(exe,[inventory.project,map.package],{detached:true,stdio:'ignore',windowsHide:false});
 child.on('error',()=>{});
 child.unref();
 return {launched:true,project:inventory.project,map:map.package};
}
module.exports={listMaps,openInUnreal};
