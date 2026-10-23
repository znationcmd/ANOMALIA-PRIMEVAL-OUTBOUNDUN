/** Per-world settings UI model, separate from dedicated CMD Hosting config. */
export const WORLD_OPTIONS=Object.freeze([
 {key:'mode',label:'Mode de jeu',type:'select',options:['pve','pvp','rp','mixed'],default:'pve',group:'Général'},
 {key:'difficulty',label:'Difficulté',min:0.2,max:5,step:0.1,default:1,group:'Général'},
 {key:'xp',label:'Expérience ×',min:0.1,max:20,step:0.1,default:1,group:'Progression'},
 {key:'harvest',label:'Récolte ×',min:0.1,max:20,step:0.1,default:1,group:'Progression'},
 {key:'loot',label:'Butin ×',min:0.1,max:20,step:0.1,default:1,group:'Progression'},
 {key:'foodDrain',label:'Consommation de nourriture ×',min:0,max:5,step:0.1,default:1,group:'Survie'},
 {key:'waterDrain',label:'Consommation d’eau ×',min:0,max:5,step:0.1,default:1,group:'Survie'},
 {key:'staminaDrain',label:'Consommation d’endurance ×',min:0,max:5,step:0.1,default:1,group:'Survie'},
 {key:'taming',label:'Apprivoisement ×',min:0.1,max:50,step:0.1,default:1,group:'Dinosaures'},
 {key:'breeding',label:'Reproduction ×',min:0.1,max:50,step:0.1,default:1,group:'Dinosaures'},
 {key:'hatching',label:'Éclosion ×',min:0.1,max:50,step:0.1,default:1,group:'Dinosaures'},
 {key:'maturation',label:'Croissance des bébés ×',min:0.1,max:50,step:0.1,default:1,group:'Dinosaures'},
 {key:'dayLength',label:'Durée du jour ×',min:0.1,max:10,step:0.1,default:1,group:'Monde'},
 {key:'nightLength',label:'Durée de la nuit ×',min:0.1,max:10,step:0.1,default:1,group:'Monde'},
 {key:'maxPlayers',label:'Joueurs (non dédié)',min:2,max:64,step:1,default:8,group:'Multijoueur'}
]);
const storageKey='anomalia-world-settings-v1';
export function normalizeWorldSettings(input={}){
 const result={};for(const spec of WORLD_OPTIONS){
  const raw=input[spec.key];
  if(spec.type==='select'){result[spec.key]=spec.options.includes(raw)?raw:spec.default;continue;}
  const n=Number(raw);result[spec.key]=raw!==undefined&&raw!==null&&raw!==''&&Number.isFinite(n)?Math.min(spec.max,Math.max(spec.min,n)):spec.default;
 }return result;
}
export function loadWorldSettings(){try{return normalizeWorldSettings(JSON.parse(localStorage.getItem(storageKey)||'{}'))}catch{return normalizeWorldSettings()}}
export function saveWorldSettings(input){const normalized=normalizeWorldSettings(input);localStorage.setItem(storageKey,JSON.stringify(normalized));return normalized;}
export function renderWorldSettings(panel){
 const form=panel.querySelector('[data-world-form]');let values=loadWorldSettings();form.replaceChildren();let group='';
 for(const spec of WORLD_OPTIONS){
  if(spec.group!==group){group=spec.group;const heading=document.createElement('h3');heading.textContent=group;form.append(heading);}
  const label=document.createElement('label');label.textContent=spec.label;
  let control;
  if(spec.type==='select'){control=document.createElement('select');for(const option of spec.options){const item=document.createElement('option');item.value=option;item.textContent=option.toUpperCase();control.append(item);}control.value=values[spec.key];}
  else{control=document.createElement('input');control.type='number';control.min=String(spec.min);control.max=String(spec.max);control.step=String(spec.step);control.value=String(values[spec.key]);}
  control.dataset.setting=spec.key;label.append(control);form.append(label);
 }
 const status=panel.querySelector('[data-world-status]');
 panel.querySelector('[data-world-save]').onclick=()=>{const next={};for(const input of form.querySelectorAll('[data-setting]'))next[input.dataset.setting]=input.value;values=saveWorldSettings(next);window.dispatchEvent(new CustomEvent('anomalia-world-settings-changed',{detail:values}));status.textContent='Réglages enregistrés pour les parties locales. Les systèmes non raccordés dans le moteur ne changent pas encore.';};
 panel.querySelector('[data-world-reset]').onclick=()=>{values=saveWorldSettings({});renderWorldSettings(panel);status.textContent='Valeurs par défaut restaurées.';};
 return ()=>values;
}
