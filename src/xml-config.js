import {XMLParser,XMLValidator} from 'fast-xml-parser';
const array=v=>v==null?[]:Array.isArray(v)?v:[v];
const number=(v,f,min=0,max=1e6)=>Number.isFinite(Number(v))?Math.min(max,Math.max(min,Number(v))):f;
export const XML_FILES=['types.xml','events.xml','cfgeventspawns.xml','cfgspawnabletypes.xml','globals.xml','economy.xml','ai.xml','cfgeconomycore.xml'];
export function parseWorldConfig(docs){
 const parser=new XMLParser({ignoreAttributes:false,attributeNamePrefix:'',processEntities:false,parseAttributeValue:true});const roots={};
 const expected={'types.xml':'types','events.xml':'events','cfgeventspawns.xml':'eventposdef','cfgspawnabletypes.xml':'spawnabletypes','globals.xml':'variables','economy.xml':'economy','ai.xml':'ai','cfgeconomycore.xml':'economycore'};
 for(const name of XML_FILES){const xml=docs[name];if(typeof xml!=='string'||xml.length>1e6)throw Error(name+': document absent ou trop grand.');if(/<!DOCTYPE|<!ENTITY/i.test(xml))throw Error(name+': DTD et entités externes non prises en charge.');const valid=XMLValidator.validate(xml);if(valid!==true)throw Error(name+': XML invalide.');const parsed=parser.parse(xml);if(!parsed[expected[name]])throw Error(name+': racine attendue <'+expected[name]+'>.');roots[name]=parsed[expected[name]];}
 const types=array(roots['types.xml'].type).slice(0,300).map(t=>({id:String(t.name||''),nominal:Math.floor(number(t.nominal,0,0,80)),min:Math.floor(number(t.min,0,0,80)),lifetime:number(t.lifetime,3600,30,86400),restock:number(t.restock,120,10,86400),quantity:Math.floor(number(t.quantity,1,1,100)),category:String(t.category?.name||'other')})).filter(t=>t.id);
 const positions={};for(const e of array(roots['cfgeventspawns.xml'].event))positions[e.name]=array(e.pos).slice(0,100).map(p=>({x:number(p.x,0,-10240,10240),z:number(p.z,0,-10240,10240),yaw:number(p.a,0,-360,360)*Math.PI/180}));
 const cargo={};for(const t of array(roots['cfgspawnabletypes.xml'].type))cargo[t.name]=array(t.cargo?.item).slice(0,50).map(i=>({id:String(i.name),count:Math.floor(number(i.count,1,1,100))}));
 const events=array(roots['events.xml'].event).slice(0,30).map(e=>({name:String(e.name||''),nominal:Math.floor(number(e.nominal,1,0,15)),lifetime:number(e.lifetime,3600,30,86400),restock:number(e.restock,300,10,86400),active:number(e.active,1,0,1)===1,positions:positions[e.name]||[],cargo:cargo[e.name]||[]}));
 const globals={};for(const v of array(roots['globals.xml'].var))globals[v.name]=number(v.value,0,0,1000);
 const ai=array(roots['ai.xml'].npc).slice(0,60).map((n,i)=>({id:String(n.id||'npc-'+i),name:String(n.name||'Survivant'),faction:n.faction==='hostile'?'hostile':'friendly',x:number(n.x,0,-10240,10240),z:number(n.z,0,-10240,10240),recruitCost:number(n.recruitCost,100,0,100000)}));
 const defaults={};for(const v of array(roots['cfgeconomycore.xml'].defaults?.default))defaults[v.name]=number(v.value,1,0,1);
 const e=roots['economy.xml'];return {types,events,globals,ai,economy:{loot:e.dynamic?.init!==0&&defaults.LootEnabled!==0,events:e.events?.init!==0&&defaults.EventsEnabled!==0,lootRespawn:e.dynamic?.respawn!==0,eventRespawn:e.events?.respawn!==0}};
}
