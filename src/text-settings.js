import {XMLParser,XMLValidator} from 'fast-xml-parser';
import {WORLD_HALF} from "./mechanics.js";
export function parseIni(text=''){
 const sections=Object.create(null);let section='';sections[section]=Object.create(null);
 if(text.length>1e6)throw Error('INI trop grand.');
 for(const raw of text.split(/\r?\n/)){const line=raw.trim();if(!line||/^[;#]/.test(line))continue;const header=line.match(/^\[([^\]]+)\]$/);if(header){section=header[1];sections[section]??=Object.create(null);continue}const index=line.indexOf('=');if(index>0){const key=line.slice(0,index).trim();if(['__proto__','prototype','constructor'].includes(key))continue;sections[section][key]=line.slice(index+1).trim();}}
 return sections;
}
const value=(v,f,min,max)=>Number.isFinite(Number(v))?Math.max(min,Math.min(max,Number(v))):f;
export function parseTextSettings(docs){
 const game=parseIni(docs['Game.ini']),settings=parseIni(docs['GameUserSettings.ini']),advanced=game.ANOMALIA||{},server=settings.ServerSettings||{},graphics=settings.ScalabilityGroups||{};
 const cfg=docs['serverDZ.cfg']||'';
 const disableThird=!!Number(cfg.match(/^\s*disable3rdPerson\s*=\s*([01])\s*;/m)?.[1]||0);
 let world;try{world=JSON.parse(docs['world-settings.json']||'{}')}catch{throw Error('world-settings.json invalide.')}
 if(world.schemaVersion!==1||!Number.isFinite(world.playerSpawn?.x)||!Number.isFinite(world.playerSpawn?.z))throw Error('world-settings.json: schéma ou position invalide.');
 let gameplay={},canonicalServer={};
 try{gameplay=JSON.parse(docs['cfggameplay.json']||'{}');canonicalServer=JSON.parse(docs['config.json']||'{}')}catch{throw Error('config.json ou cfggameplay.json invalide.')}
 if((gameplay.schemaVersion!==undefined&&gameplay.schemaVersion!==1)||(canonicalServer.schemaVersion!==undefined&&canonicalServer.schemaVersion!==1))throw Error('Version de configuration non prise en charge.');
 let playerSpawn={x:world.playerSpawn.x,z:world.playerSpawn.z};
 const spawnXml=docs['cfgplayerspawnpoints.xml'];
 if(spawnXml){
  if(spawnXml.length>100000||/<!DOCTYPE|<!ENTITY/i.test(spawnXml)||XMLValidator.validate(spawnXml)!==true)throw Error('cfgplayerspawnpoints.xml invalide.');
  const spawn=new XMLParser({ignoreAttributes:false,attributeNamePrefix:'',parseAttributeValue:true}).parse(spawnXml)?.playerspawnpoints?.spawn;
  const first=Array.isArray(spawn)?spawn[0]:spawn;
  if(first&&Number.isFinite(Number(first.x))&&Number.isFinite(Number(first.z)))playerSpawn={x:Number(first.x),z:Number(first.z)};
 }
 return {serverName:String(canonicalServer.server?.name||'ANOMALIA').slice(0,96),serverMode:['rp','pvp','pve','mixed'].includes(canonicalServer.server?.mode)?canonicalServer.server.mode:'pve',timeMultiplier:value(canonicalServer.server?.timeMultiplier,1,.1,24),construction:gameplay.construction||{},staminaMultiplier:value(gameplay.player?.staminaMultiplier,1,.1,10),weatherEnabled:gameplay.weather?.enabled!==false,lootMultiplier:value(advanced.LootMultiplier,1,0,10),followDistance:value(advanced.CompanionFollowDistance,3,1,20),tamingSpeed:value(advanced.TamingSpeedMultiplier,1,.1,20),aiDamage:value(advanced.AiDamageMultiplier,1,0,10),foodDrain:value(server.PlayerCharacterFoodDrainMultiplier,1,0,10),waterDrain:value(server.PlayerCharacterWaterDrainMultiplier,1,0,10),resolution:value(graphics['sg.ResolutionQuality'],100,50,200),shadows:value(graphics['sg.ShadowQuality'],2,0,3)>0,thirdPersonAllowed:!disableThird&&server.ServerThirdPersonPlayer?.toLowerCase()!=='false',spawn:{x:value(playerSpawn.x,0,-WORLD_HALF,WORLD_HALF),z:value(playerSpawn.z,180,-WORLD_HALF,WORLD_HALF)},startingItems:world.startingItems&&typeof world.startingItems==='object'?world.startingItems:{}};
}
