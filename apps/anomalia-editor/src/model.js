// ANOMALIA Editor — modèle indépendant, aucune connexion ni partage implicite.
export const SCHEMA = 'anomalia-editor';
export const VERSION = 1;
export const LIMIT = 4000;
export const AXES = ['x', 'y', 'z'];
export const PRESETS = Object.freeze([
  {id:'house',name:'Maison',category:'Bâtiments'},
  {id:'villa',name:'Villa',category:'Bâtiments'},
  {id:'apartment',name:'Immeuble',category:'Bâtiments'},
  {id:'warehouse',name:'Entrepôt',category:'Bâtiments'},
  {id:'wall',name:'Mur',category:'Construction'},
  {id:'road',name:'Route',category:'Construction'},
  {id:'fence',name:'Clôture',category:'Construction'},
  {id:'tower',name:'Tour',category:'Construction'},
  {id:'pine',name:'Sapin',category:'Nature'},
  {id:'tree',name:'Arbre',category:'Nature'},
  {id:'rock',name:'Rocher',category:'Nature'},
  {id:'bush',name:'Buisson',category:'Nature'},
  {id:'car',name:'Voiture',category:'Véhicules'},
  {id:'truck',name:'Camion',category:'Véhicules'},
  {id:'boat',name:'Bateau',category:'Véhicules'},
  {id:'helicopter',name:'Hélicoptère',category:'Véhicules'},
  {id:'table',name:'Table',category:'Mobilier'},
  {id:'crate',name:'Caisse',category:'Mobilier'},
  {id:'barrel',name:'Baril',category:'Mobilier'},
  {id:'streetlight',name:'Lampadaire',category:'Mobilier'}
]);
const PRESET_IDS = new Set(PRESETS.map(p => p.id));
const vector = (x=0,y=0,z=0) => ({x,y,z});
export function newProject(name='Nouvelle carte') {
  return {schema:SCHEMA,version:VERSION,name:String(name).slice(0,80),objects:[],createdAt:new Date().toISOString()};
}
export function makeObject(preset,position=vector(),asset=null) {
  if (!PRESET_IDS.has(preset) && preset !== 'custom-glb') throw new Error('Objet inconnu');
  const item=PRESETS.find(p=>p.id===preset);
  return {id:crypto.randomUUID(),preset,name:item?.name||asset?.filename||'Modèle 3D',
    position:{...vector(),...position},rotation:vector(),scale:vector(1,1,1),
    ...(asset?{asset}:{}),visible:true};
}
export function cloneProject(project) { return structuredClone(project); }
export class History {
  constructor(project=newProject(),limit=80) {this.limit=limit;this.past=[];this.future=[];this.project=cloneProject(project);}
  commit(project) {
    const candidate=validateProject(project);
    if(JSON.stringify(candidate)===JSON.stringify(this.project))return false;
    this.past.push(cloneProject(this.project));
    if(this.past.length>this.limit)this.past.shift();
    this.project=cloneProject(candidate);this.future=[];
    return true;
  }
  undo() {
    if(!this.past.length)return null;
    this.future.push(cloneProject(this.project));
    this.project=this.past.pop();
    return cloneProject(this.project);
  }
  redo() {
    if(!this.future.length)return null;
    this.past.push(cloneProject(this.project));
    this.project=this.future.pop();
    return cloneProject(this.project);
  }
  reset(project) {this.project=cloneProject(validateProject(project));this.past=[];this.future=[];return cloneProject(this.project);}
}
function validateAxis(data,defaults,mode) {
  if(!data||typeof data!=='object')throw new Error('Coordonnées absentes');
  const output={};
  for(const key of AXES){
    const n=data[key];
    if(typeof n!=='number'||!Number.isFinite(n))throw new Error('Coordonnées invalides');
    if(mode==='scale'?(n<.01||n>10000):(Math.abs(n)>1000000))
      throw new Error('Valeurs 3D hors limites');
    output[key]=n;
  }
  return output;
}
export function validateProject(input) {
  if(!input||input.schema!==SCHEMA||input.version!==VERSION||!Array.isArray(input.objects)||input.objects.length>LIMIT)
    throw new Error('Format de projet non pris en charge ou trop volumineux');
  if(typeof input.name!=='string'||input.name.length>80)throw new Error('Nom de projet invalide');
  const ids=new Set();
  const objects=input.objects.map(o=>{
    if(!o||typeof o.id!=='string'||o.id.length>120||ids.has(o.id))throw new Error('Identifiant d’objet invalide ou dupliqué');
    ids.add(o.id);
    if(!PRESET_IDS.has(o.preset)&&o.preset!=='custom-glb')throw new Error('Modèle inconnu');
    if(typeof o.name!=='string'||o.name.length>90)throw new Error('Nom d’objet invalide');
    const result={id:o.id,preset:o.preset,name:o.name,
      position:validateAxis(o.position,vector(),'position'),
      rotation:validateAxis(o.rotation,vector(),'rotation'),
      scale:validateAxis(o.scale,vector(1,1,1),'scale'),visible:o.visible!==false};
    if(o.preset==='custom-glb'){
      if(!o.asset||typeof o.asset.data!=='string'||o.asset.data.length>28000000||
        !/^[A-Za-z0-9+/]+={0,2}$/.test(o.asset.data)||typeof o.asset.filename!=='string'||o.asset.filename.length>140)
        throw new Error('Modèle GLB invalide ou trop lourd');
      result.asset={filename:o.asset.filename,data:o.asset.data};
    }
    return result;
  });
  return {schema:SCHEMA,version:VERSION,name:input.name,createdAt:input.createdAt||new Date().toISOString(),objects};
}
export function makeCSV(project) {
  const clean=validateProject(project);
  const fields=['id','name','preset','x_m','y_m','z_m','rot_x_deg','rot_y_deg','rot_z_deg','scale_x','scale_y','scale_z'];
  const escape=value=>'"'+String(value).replace(/"/g,'""')+'"';
  return [fields.join(','),...clean.objects.map(o=>[
    o.id,o.name,o.preset,o.position.x,o.position.y,o.position.z,
    o.rotation.x,o.rotation.y,o.rotation.z,o.scale.x,o.scale.y,o.scale.z
  ].map(escape).join(','))].join('\r\n')+'\r\n';
}
export function updateTransform(project,id,group,axis,value) {
  if(!['position','rotation','scale'].includes(group)||!AXES.includes(axis)||!Number.isFinite(value))
    throw new Error('Transformation invalide');
  const next=cloneProject(project);
  const o=next.objects.find(item=>item.id===id);
  if(!o)throw new Error('Objet non trouvé');
  o[group][axis]=value;
  return validateProject(next);
}
export function addToProject(project,item) {
  const next=cloneProject(project);
  if(next.objects.length>=LIMIT)throw new Error('Limite de 4 000 objets atteinte');
  next.objects.push(item);
  return validateProject(next);
}
export function removeFromProject(project,id) {
  const next=cloneProject(project);
  next.objects=next.objects.filter(o=>o.id!==id);
  return validateProject(next);
}
