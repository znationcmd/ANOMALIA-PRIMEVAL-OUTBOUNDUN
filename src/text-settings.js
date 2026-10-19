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
 return {lootMultiplier:value(advanced.LootMultiplier,1,0,10),followDistance:value(advanced.CompanionFollowDistance,3,1,20),tamingSpeed:value(advanced.TamingSpeedMultiplier,1,.1,20),aiDamage:value(advanced.AiDamageMultiplier,1,0,10),foodDrain:value(server.PlayerCharacterFoodDrainMultiplier,1,0,10),waterDrain:value(server.PlayerCharacterWaterDrainMultiplier,1,0,10),resolution:value(graphics['sg.ResolutionQuality'],100,50,200),shadows:value(graphics['sg.ShadowQuality'],2,0,3)>0,thirdPersonAllowed:!disableThird&&server.ServerThirdPersonPlayer?.toLowerCase()!=='false',spawn:{x:value(world.playerSpawn.x,0,-10240,10240),z:value(world.playerSpawn.z,180,-10240,10240)},startingItems:world.startingItems&&typeof world.startingItems==='object'?world.startingItems:{}};
}
