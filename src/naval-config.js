import {XMLParser,XMLValidator} from 'fast-xml-parser';
import {WORLD_HALF} from './mechanics.js';
const TYPES=new Set(['carrier','warship','submarine']);
const num=(v,f,min,max)=>Number.isFinite(Number(v))?Math.max(min,Math.min(max,Number(v))):f;
export function parseNavalConfig(xml=''){
 if(typeof xml!=='string'||xml.length>200000||/<!DOCTYPE|<!ENTITY/i.test(xml))throw Error('vehicles.xml invalide.');
 const valid=XMLValidator.validate(xml);if(valid!==true)throw Error('vehicles.xml invalide.');
 const root=new XMLParser({ignoreAttributes:false,attributeNamePrefix:'',parseAttributeValue:true}).parse(xml)?.navalVehicles;
 if(!root)return [];
 const rows=Array.isArray(root.vehicle)?root.vehicle:root.vehicle?[root.vehicle]:[];
 return rows.filter(v=>TYPES.has(String(v.type))).map(v=>{
  const positions=(Array.isArray(v.pos)?v.pos:v.pos?[v.pos]:[]).map(p=>({x:num(p.x,0,-WORLD_HALF,WORLD_HALF),z:num(p.z,0,-WORLD_HALF,WORLD_HALF),yaw:num(p.yaw,0,-360,360)*Math.PI/180}));
  return {type:String(v.type),enabled:String(v.enabled)!=='0'&&v.enabled!==false,nominal:Math.floor(num(v.nominal,0,0,20)),respawn:Math.floor(num(v.respawn,3600,30,86400)),positions};
 });
}
