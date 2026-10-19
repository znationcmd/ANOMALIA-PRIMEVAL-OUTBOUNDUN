import {XMLParser,XMLValidator} from 'fast-xml-parser';
import {WORLD_HALF} from './mechanics.js';
import {VEHICLES} from './vehicles.js';
const TYPES=new Set(Object.keys(VEHICLES));
const num=(v,f,min,max)=>Number.isFinite(Number(v))?Math.max(min,Math.min(max,Number(v))):f;
export function parseNavalConfig(xml=''){
 if(typeof xml!=='string'||xml.length>200000||/<!DOCTYPE|<!ENTITY/i.test(xml))throw Error('vehicles.xml invalide.');
 const valid=XMLValidator.validate(xml);if(valid!==true)throw Error('vehicles.xml invalide.');
 const root=new XMLParser({ignoreAttributes:false,attributeNamePrefix:'',parseAttributeValue:true}).parse(xml)?.navalVehicles;
 if(!root)return [];
 const rows=Array.isArray(root.vehicle)?root.vehicle:root.vehicle?[root.vehicle]:[];
 const parsed=rows.filter(v=>TYPES.has(String(v.type))).map(v=>{
  const positions=(Array.isArray(v.pos)?v.pos:v.pos?[v.pos]:[]).map(p=>({x:num(p.x,0,-WORLD_HALF,WORLD_HALF),z:num(p.z,0,-WORLD_HALF,WORLD_HALF),yaw:num(p.yaw,0,-360,360)*Math.PI/180}));
  return {tuning:{speed:num(v.speed,VEHICLES[String(v.type)].speed,1,200),accel:num(v.accel,VEHICLES[String(v.type)].accel,.1,30),turn:num(v.turn,VEHICLES[String(v.type)].turn,.05,5),fuelRate:num(v.fuelRate,.03,0,5),fuelCapacity:num(v.fuelCapacity,100,1,10000),maxHealth:num(v.maxHealth,100,1,10000),cargoSlots:Math.floor(num(v.cargoSlots,0,0,1000))},type:String(v.type),enabled:!['0','false','no','off'].includes(String(v.enabled).toLowerCase()),nominal:Math.floor(num(v.nominal,0,0,20)),respawn:Math.floor(num(v.respawn,3600,30,86400)),positions};
 });
 const merged=new Map();
 for(const row of parsed){const old=merged.get(row.type);if(!old){merged.set(row.type,row);continue}old.nominal=Math.min(20,old.nominal+row.nominal);old.positions.push(...row.positions);old.enabled=old.enabled||row.enabled;old.respawn=Math.min(old.respawn,row.respawn);}
 return [...merged.values()];
}
