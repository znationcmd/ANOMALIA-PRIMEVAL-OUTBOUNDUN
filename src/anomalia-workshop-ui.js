import {validatePlacements} from './building-rules.js';
const KEY='anomalia-workshop-map-mods-v1';
const ID=/^[a-z0-9][a-z0-9._-]{1,79}$/;
function read(){try{const data=JSON.parse(localStorage.getItem(KEY)||'[]');return Array.isArray(data)?data:[]}catch{return []}}
function save(mods){localStorage.setItem(KEY,JSON.stringify(mods));}
export function validateMapMod(raw){
 if(!raw||!ID.test(raw.id)||typeof raw.name!=='string'||raw.name.length>90||!/^\d+\.\d+\.\d+$/.test(raw.version))throw Error('Identifiant, nom ou version invalide');
 if(raw.type!=='mapping')throw Error('Ce prototype prend en charge uniquement les mods de mapping JSON');
 const objects=validatePlacements({schemaVersion:1,objects:raw.objects});
 return {id:raw.id,name:raw.name,version:raw.version,type:'mapping',objects};
}
function download(name,data){
 const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));
 const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
export function createWorkshopPanels({modsPanel,toolsPanel}){
 const render=()=>{
  const list=modsPanel.querySelector('[data-mod-list]');list.replaceChildren();
  const mods=read();
  if(!mods.length){const p=document.createElement('p');p.textContent='Aucun mod de mapping installé localement.';list.append(p);}
  for(const mod of mods){
   const row=document.createElement('div');row.className='workshop-mod-row';
   const label=document.createElement('span');label.textContent=mod.name+' · '+mod.version+' · '+(mod.enabled?'Activé':'Désactivé');
   const toggle=document.createElement('button');toggle.textContent=mod.enabled?'Désactiver':'Activer';
   toggle.onclick=()=>{save(read().map(m=>m.id===mod.id?{...m,enabled:!m.enabled}:m));render();};
   const exportBtn=document.createElement('button');exportBtn.textContent='Exporter';exportBtn.onclick=()=>download(mod.id+'.json',mod);
   const remove=document.createElement('button');remove.textContent='Désinstaller';remove.onclick=()=>{if(!confirm('Désinstaller '+mod.name+' ?'))return;save(read().filter(m=>m.id!==mod.id));render();};
   row.append(label,toggle,exportBtn,remove);list.append(row);
  }
 };
 const install=async(file)=>{
  if(!file)return;if(file.size>500000)throw Error('Fichier trop volumineux (max 500 Ko)');
  const mod=validateMapMod(JSON.parse(await file.text()));
  const mods=read();const index=mods.findIndex(m=>m.id===mod.id);
  if(index>=0)mods[index]={...mod,enabled:mods[index].enabled};else mods.push({...mod,enabled:true});
  save(mods);render();return mod;
 };
 const importInput=modsPanel.querySelector('[data-mod-import]');
 importInput.onchange=async()=>{const status=modsPanel.querySelector('[data-mod-status]');try{const mod=await install(importInput.files?.[0]);status.textContent=mod?'Mod de mapping installé : '+mod.name:'';}catch(e){status.textContent='Échec : '+e.message;}finally{importInput.value='';}};
 const buildBtn=toolsPanel.querySelector('[data-mod-build]');
 buildBtn.onclick=async()=>{
  const status=toolsPanel.querySelector('[data-mod-status]');
  try{
   const file=toolsPanel.querySelector('[data-mod-source]').files?.[0];
   if(!file||file.size>500000)throw Error('Choisis un export JSON ANOMALIA Editor (max 500 Ko)');
   const source=JSON.parse(await file.text());const objects=validatePlacements(source);
   const id=toolsPanel.querySelector('[data-mod-id]').value.trim().toLowerCase();
   const name=toolsPanel.querySelector('[data-mod-name]').value.trim();
   const version=toolsPanel.querySelector('[data-mod-version]').value.trim();
   const mod=validateMapMod({id,name,version,type:'mapping',objects});
   download(id+'-'+version+'.json',mod);
   status.textContent='Mod de mapping exporté. Installe-le ensuite dans Mods.';
  }catch(e){status.textContent='Échec : '+e.message;}
 };
 render();
 return {render,getEnabledMapMods:()=>read().filter(m=>m.enabled)};
}
