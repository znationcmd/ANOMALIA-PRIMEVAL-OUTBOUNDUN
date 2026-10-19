import {WORLD_HALF} from "./mechanics.js";
import creatures from '../public/config/creatures.json?raw';
import types from '../public/config/types.xml?raw';
import events from '../public/config/events.xml?raw';
import positions from '../public/config/cfgeventspawns.xml?raw';
import cargo from '../public/config/cfgspawnabletypes.xml?raw';
import globals from '../public/config/globals.xml?raw';
import economy from '../public/config/economy.xml?raw';
import ai from '../public/config/ai.xml?raw';
import core from '../public/config/cfgeconomycore.xml?raw';
import cfg from '../public/config/serverDZ.cfg?raw';
import game from '../public/config/Game.ini?raw';
import settings from '../public/config/GameUserSettings.ini?raw';
import world from '../public/config/world-settings.json?raw';
import serverJson from '../public/config/config.json?raw';
import adminJson from '../public/config/admin_config.json?raw';
import scenariosJson from '../public/config/scenarios.json?raw';
import modsJson from '../public/config/mods.json?raw';
import gameplayJson from '../public/config/cfggameplay.json?raw';
import lootspawnXml from '../public/config/cfglootspawn.xml?raw';
import playerSpawnXml from '../public/config/cfgplayerspawnpoints.xml?raw';
import messagesXml from '../public/config/messages.xml?raw';
import vehiclesXml from '../public/config/vehicles.xml?raw';
import legacyArkAdmins from '../public/config/AllowedCheaterSteamIDs.txt?raw';
import {parseWorldConfig as parseXmlConfig} from './xml-config.js';
import {parseTextSettings} from './text-settings.js';
import {parseNavalConfig} from './naval-config.js';
export const DEFAULT_XML={'types.xml':types,'events.xml':events,'cfgeventspawns.xml':positions,'cfgspawnabletypes.xml':cargo,'globals.xml':globals,'economy.xml':economy,'ai.xml':ai,'cfgeconomycore.xml':core,'serverDZ.cfg':cfg,'Game.ini':game,'GameUserSettings.ini':settings,'world-settings.json':world,'creatures.json':creatures,'config.json':serverJson,'admin_config.json':adminJson,'scenarios.json':scenariosJson,'mods.json':modsJson,'cfggameplay.json':gameplayJson,'cfglootspawn.xml':lootspawnXml,'cfgplayerspawnpoints.xml':playerSpawnXml,'messages.xml':messagesXml,'vehicles.xml':vehiclesXml,'AllowedCheaterSteamIDs.txt':legacyArkAdmins};
export function parseWorldConfig(docs){const config=parseXmlConfig(docs);config.settings=parseTextSettings(docs);config.naval=parseNavalConfig(docs['vehicles.xml']||'<navalVehicles/>');let creatures;try{creatures=JSON.parse(docs['creatures.json'])}catch{throw Error('creatures.json invalide.')}
 if(creatures.schemaVersion!==1||!Array.isArray(creatures.spawns))throw Error('creatures.json: schéma invalide.');
 config.creatures={preferredKibble:creatures.preferredKibble||{},spawns:creatures.spawns.filter(d=>['raptor','stegosaur','triceratops','bront'].includes(d.type)&&Number.isFinite(d.x)&&Number.isFinite(d.z)&&Math.abs(d.x)<=WORLD_HALF&&Math.abs(d.z)<=WORLD_HALF).slice(0,100)};config.globals.LootMultiplier=(config.globals.LootMultiplier??1)*config.settings.lootMultiplier;config.globals.CompanionFollowDistance=config.settings.followDistance;return config}
export async function readWorldConfig(overrides={}){
 const docs={...DEFAULT_XML};
 if(location.protocol!=='file:')await Promise.all(Object.keys(docs).map(async name=>{try{const response=await fetch('./config/'+name,{cache:'no-store'});if(response.ok)docs[name]=await response.text()}catch{}}));
 Object.assign(docs,overrides);return {docs,config:parseWorldConfig(docs)};
}
