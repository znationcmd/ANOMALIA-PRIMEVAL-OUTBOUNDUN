/** Canonical ANOMALIA config catalog. Aliases are imported, never silently deleted.
 * Files of other engines are templates, not native DayZ/ARK/Reforger runtimes.
 */
export const CONFIG_GROUPS=Object.freeze({
 server:{primary:'config.json',files:['config.json','serverDZ.cfg'],scope:'server'},
 permissions:{primary:'admin_config.json',files:['admin_config.json','AllowedCheaterSteamIDs.txt'],scope:'server'},
 scenarios:{primary:'scenarios.json',files:['scenarios.json','world-settings.json','cfgplayerspawnpoints.xml'],scope:'server'},
 mods:{primary:'mods.json',files:['mods.json'],scope:'server'},
 gameplay:{primary:'cfggameplay.json',files:['cfggameplay.json','Game.ini','GameUserSettings.ini'],scope:'server'},
 loot:{primary:'types.xml',files:['types.xml','cfglootspawn.xml','cfgspawnabletypes.xml'],scope:'server'},
 events:{primary:'events.xml',files:['events.xml','cfgeventspawns.xml','messages.xml'],scope:'server'},
 economy:{primary:'globals.xml',files:['globals.xml','economy.xml','cfgeconomycore.xml'],scope:'server'},
 creatures:{primary:'creatures.json',files:['creatures.json','ai.xml'],scope:'server'},
 naval:{primary:'vehicles.xml',files:['vehicles.xml'],scope:'server'},
 persistence:{primary:'world.json',files:['world.json'],scope:'server'}
});
export const RUNTIME_LOGS=Object.freeze(['Server.log','console.log','Crash.log','Script.log']);
export const PERSISTENCE_DIRS=Object.freeze(['userProfile','dayz.db','SavedArks']);
export const ARK_ARTIFACTS=Object.freeze(['.ark','.arkprofile','.arktribe']);
export function validateConfigCatalog(groups=CONFIG_GROUPS){
 const seen=new Set();
 for(const [key,group] of Object.entries(groups)){
  if(!group.files.includes(group.primary))throw Error('Missing canonical config for '+key);
  for(const file of group.files){
   if(seen.has(file))throw Error('Duplicate config filename: '+file);
   seen.add(file);
  }
 }
 return true;
}
export const CONFIG_FILES=Object.freeze([...new Set(Object.values(CONFIG_GROUPS).flatMap(g=>g.files))]);
validateConfigCatalog();
