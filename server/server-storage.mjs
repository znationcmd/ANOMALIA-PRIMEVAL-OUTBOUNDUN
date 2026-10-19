import {createHash} from 'node:crypto';
import {join,resolve,sep} from 'node:path';
import {mkdirSync,readFileSync,writeFileSync,existsSync,renameSync} from 'node:fs';
export function normalizeServerId(value){
 const id=String(value??'').trim().toLowerCase();
 if(!/^[a-z0-9][a-z0-9_-]{0,47}$/.test(id))throw Error('Invalid server ID');
 return id;
}
export function serverIdFromAddress(address){
 const url=new URL(address);
 if(!['ws:','wss:'].includes(url.protocol)||url.username||url.password)throw Error('Invalid server address');
 return createHash('sha256').update(url.host.toLowerCase()+url.pathname).digest('hex').slice(0,24);
}
export function serverDirectory(base,serverId){
 const root=resolve(base),id=normalizeServerId(serverId),directory=resolve(root,'servers',id);
 if(!directory.startsWith(root+sep))throw Error('Unsafe server directory');
 return directory;
}
export function readServerDocument(base,serverId,name,fallback){
 if(!/^[a-z0-9-]+\.json$/.test(name))throw Error('Invalid document');
 const path=join(serverDirectory(base,serverId),name);
 if(!existsSync(path))return fallback;
 try{return JSON.parse(readFileSync(path,'utf8'))}catch{return fallback}
}
export function writeServerDocument(base,serverId,name,value){
 if(!/^[a-z0-9-]+\.json$/.test(name))throw Error('Invalid document');
 const dir=serverDirectory(base,serverId);mkdirSync(dir,{recursive:true});
 const target=join(dir,name),temp=target+'.tmp';
 writeFileSync(temp,JSON.stringify(value),{encoding:'utf8',mode:0o600});
 renameSync(temp,target);return target;
}
