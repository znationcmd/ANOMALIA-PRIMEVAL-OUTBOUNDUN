import {appendFileSync,mkdirSync,statSync,renameSync,existsSync} from 'node:fs';
import {join} from 'node:path';
import {serverDirectory} from './server-storage.mjs';
const MAX_BYTES=2*1024*1024;
const FILES=new Set(['Server.log','console.log','Crash.log','Script.log']);
export function appendServerLog({dataRoot='server-data',serverId='main',file='Server.log',event,details={}}){
 if(!FILES.has(file))throw Error('Invalid log file');
 const dir=serverDirectory(dataRoot,serverId);mkdirSync(dir,{recursive:true});
 const path=join(dir,file);
 if(existsSync(path)&&statSync(path).size>MAX_BYTES)renameSync(path,path+'.previous');
 const clean=Object.fromEntries(Object.entries(details).filter(([key])=>!/pass|secret|token|adminKey|authorization/i.test(key)).map(([key,value])=>[key,typeof value==='string'?value.slice(0,120).replace(/[\r\n]/g,' '):typeof value==='number'||typeof value==='boolean'?value:null]));
 appendFileSync(path,JSON.stringify({time:new Date().toISOString(),event:String(event).slice(0,80),...clean})+'\n',{encoding:'utf8',mode:0o600});
}
