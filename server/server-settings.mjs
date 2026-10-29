/** Server-specific ANOMALIA settings, without sharing files between servers.
 * Server config precedence: explicit options > environment > server config.json > defaults.
 * Never write secrets to the shipped public templates.
 */
import {readFileSync,existsSync} from 'node:fs';
import {join} from 'node:path';
import {serverDirectory} from './server-storage.mjs';
const integer=(v,f,min,max)=>Number.isInteger(Number(v))?Math.min(max,Math.max(min,Number(v))):f;
const safeString=(v,f,max=100)=>typeof v==='string'?v.slice(0,max):f;
export function loadServerSettings({dataRoot='server-data',serverId='main',env=process.env}={}){
 const dir=serverDirectory(dataRoot,serverId);
 const file=join(dir,'config.json');
 let document={};
 if(existsSync(file)){
  const raw=readFileSync(file,'utf8');
  if(raw.length>65536)throw Error('config.json exceeds 64KB');
  document=JSON.parse(raw);
  if(!document||document.schemaVersion!==1||typeof document.server!=='object')throw Error('config.json invalid');
 }
 const s=document.server||{};
 const mode=['rp','pvp','pve','mixed'].includes(s.mode)?s.mode:'pve';
 return {
  name:safeString(env.SERVER_NAME??s.name,'ANOMALIA’Z PRIGIMALIA',96),
  port:integer(env.PORT??s.port,2303,1024,65535),
  maxPlayers:integer(env.MAX_PLAYERS??s.maxPlayers,16,1,64),
  password:safeString(env.SERVER_PASSWORD??s.password,'',128),
  mode:['rp','pvp','pve','mixed'].includes(env.GAME_MODE)?env.GAME_MODE:mode,
  timeMultiplier:Number.isFinite(Number(s.timeMultiplier))?Math.max(.1,Math.min(24,Number(s.timeMultiplier))):1,
  thirdPerson:s.thirdPerson!==false,
  serverId
 };
}
