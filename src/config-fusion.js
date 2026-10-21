/** Non-destructive ANOMALIA DayZ/ARK-inspired config merger. No runtime side effects. */
export const FUSION_DOMAINS=Object.freeze({
 server:{primary:'config.json',legacy:['serverDZ.cfg']},
 permissions:{primary:'admin_config.json',legacy:['AllowedCheaterSteamIDs.txt']},
 gameplay:{primary:'GameUserSettings.ini',legacy:['cfggameplay.json']},
 advanced:{primary:'Game.ini',legacy:[]},
 loot:{primary:'types.xml',legacy:['cfglootspawn.xml','cfgspawnabletypes.xml','loot_tiers.json','loot_items_catalog.json']},
 events:{primary:'events.xml',legacy:['cfgeventspawns.xml','radiation_zones.json']},
 vehicles:{primary:'vehicles.xml',legacy:[]},
 maps:{primary:'scenarios.json',legacy:['world-settings.json','cfgplayerspawnpoints.xml','mapping/manifest.json']},
 creatures:{primary:'dinosaurs/catalog.json',legacy:['creatures.json','ai.xml','dino_species_catalog.json','dino_variants_catalog.json','dino_moro_creatures_catalog.json','dino_kibbles_catalog.json']},
 economy:{primary:'globals.xml',legacy:['economy.xml','cfgeconomycore.xml']},
 mods:{primary:'mods.json',legacy:[]},
 persistence:{primary:'world.json',legacy:[]}
});
const dangerous=new Set(['__proto__','constructor','prototype']);
export function parseIni(input){
 const sections=Object.create(null);let section='';
 for(const raw of String(input).split(/\r?\n/)){
  const line=raw.trim();if(!line||line.startsWith(';')||line.startsWith('#'))continue;
  const match=line.match(/^\[([^\]]+)\]$/);
  if(match){section=match[1];if(dangerous.has(section))throw Error('Unsafe INI section');sections[section]??=Object.create(null);continue;}
  const index=line.indexOf('=');if(index<1)continue;
  const key=line.slice(0,index).trim();if(dangerous.has(key))throw Error('Unsafe INI key');
  sections[section]??=Object.create(null);sections[section][key]=line.slice(index+1).trim();
 }
 return sections;
}
export function mergeConfig({defaults={},legacy={},canonical={},server={}}={}){
 const conflicts=[];const output=Object.create(null);
 for(const [source,layer] of [['defaults',defaults],['legacy',legacy],['canonical',canonical],['server',server]]){
  for(const [key,value] of Object.entries(layer)){
   if(dangerous.has(key))throw Error('Unsafe config key');
   if(Object.hasOwn(output,key)&&output[key]!==value)conflicts.push({key,from:output[key],to:value,source});
   output[key]=value;
  }
 }
 return {values:output,conflicts,precedence:['defaults','legacy','canonical','server']};
}
export function flattenIniSections(parsed){
 const result=Object.create(null);
 for(const [section,values] of Object.entries(parsed)){
  for(const [key,value] of Object.entries(values)){
   const name=section?section+'.'+key:key;
   if(dangerous.has(name))throw Error('Unsafe flattened key');
   result[name]=value;
  }
 }
 return result;
}
export function buildFusionReport(files={}){
 const report=[];
 for(const [domain,group] of Object.entries(FUSION_DOMAINS)){
  report.push({domain,primary:group.primary,primaryPresent:Object.hasOwn(files,group.primary),legacy:group.legacy.map(path=>({path,present:Object.hasOwn(files,path)}))});
 }
 return report;
}
