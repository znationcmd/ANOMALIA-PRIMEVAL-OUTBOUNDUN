/**
 * ANOMALIA'Z PRIGIMALIA official fleet - single authoritative process.
 *
 * Deploy separately from individual Unreal game servers. Bind to localhost by
 * default behind operator-managed TLS (mTLS recommended). Never expose these
 * endpoints to players or distribute server credentials in the game client.
 */
import http from 'node:http';
import {createHash, timingSafeEqual} from 'node:crypto';
import {mkdirSync, readFileSync, existsSync, writeFileSync, renameSync} from 'node:fs';
import {resolve,join} from 'node:path';
import {createOfficialCharacterRegistry, OfficialTransferError} from './official-character-registry.mjs';

const equal=(a,b)=>{
  const x=createHash('sha256').update(String(a)).digest();
  const y=createHash('sha256').update(String(b)).digest();
  return timingSafeEqual(x,y);
};
const allowObject=value=>value&&typeof value==='object'&&!Array.isArray(value);
const MAX_BYTES=1024*1024;
/** Persistent coordinator. One process + durable atomic snapshot; no clustering. */
export function createOfficialCharacterService({
  operators,
  spawnPoints,
  storagePath,
  cooldownMs=90000,
  host='127.0.0.1',
  port=0,
  now=()=>Date.now(),
  pickIndex,
}={}) {
  if(!allowObject(operators)||!storagePath)throw Error('Trusted operator registry and writable persistence path required');
  const ids=Object.keys(operators);
  if(ids.length===0)throw Error('Official operator catalog cannot be empty');
  const keys=new Map();
  const servers={};
  for(const serverId of ids){
    const entry=operators[serverId];
    if(!allowObject(entry)||entry.category!=='official'||typeof entry.thirdPerson!=='boolean'||
       typeof entry.secret!=='string'||entry.secret.length<32)
      throw Error('Each official server requires an operator-assigned long-lived secret and camera class');
    keys.set(serverId,entry.secret);
    servers[serverId]={category:'official',thirdPerson:entry.thirdPerson};
  }
  const dataPath=resolve(storagePath),parent=resolve(dataPath,'..');
  mkdirSync(parent,{recursive:true});
  let initial={schemaVersion:1,records:{}};
  if(existsSync(dataPath)){
    try{
      initial=JSON.parse(readFileSync(dataPath,'utf8'));
      if(initial.schemaVersion!==1||!allowObject(initial.records))throw Error('Bad schema');
    }catch(error){throw Error('Refusing to start with unreadable central character data: '+error.message)}
  }
  // The registry used by both admission and checkout is rebuilt from durable
  // state below. It must NEVER be shared with community or client scripts.
  const registry=createOfficialCharacterRegistry({servers,spawnPoints,cooldownMs,now,pickIndex});
  if(Object.keys(initial.records).length!==0)
    throw Error('Nonempty durable registry needs an operator recovery/migration adapter; refusing unsafe reset');
  const atomicWrite=()=>{
    const tmp=dataPath+'.tmp';
    if(existsSync(tmp))throw Error('Unfinished central registry write detected; human recovery required');
    writeFileSync(tmp,JSON.stringify(initial),{encoding:'utf8',mode:0o600,flag:'wx'});
    renameSync(tmp,dataPath);
  };
  // Refuse to begin if a second central writer is present. Service is designed
  // for a single deployed instance, never multiple replicas sharing the same dir.
  const lockPath=dataPath+'.lock';
  if(existsSync(lockPath))throw Error('Another coordinator or stale central lock exists');
  writeFileSync(lockPath,JSON.stringify({pid:process.pid,startedAt:Date.now()}),{flag:'wx',mode:0o600});
  let server;
  const requests=new Set();
  try{
    server=http.createServer(async(req,res)=>{
      res.setHeader('Cache-Control','no-store');
      const reply=(code,data)=>{
        if(res.writableEnded)return;
        res.writeHead(code,{'Content-Type':'application/json; charset=utf-8'});
        res.end(JSON.stringify(data));
      };
      if(req.method!=='POST'||!['/v1/official/check-in','/v1/official/check-out','/v1/official/status'].includes(req.url))
        return reply(404,{error:'NOT_FOUND'});
      const claimedServer=req.headers['x-anomalia-server-id'];
      const secret=String(req.headers.authorization||'').replace(/^Bearer /,'');
      if(typeof claimedServer!=='string'||!keys.has(claimedServer)||!equal(keys.get(claimedServer),secret))
        return reply(403,{error:'NOT_AUTHORIZED'});
      if(!req.headers['content-type']?.startsWith('application/json'))return reply(415,{error:'JSON_REQUIRED'});
      let raw='',length=0;
      try{
        for await (const chunk of req){
          length+=chunk.length;
          if(length>MAX_BYTES) return reply(413,{error:'BODY_TOO_LARGE'});
          raw+=chunk.toString('utf8');
        }
        const data=JSON.parse(raw);
        if(!allowObject(data)||typeof data.playerId!=='string')return reply(400,{error:'INVALID_BODY'});
        // Server identity comes ONLY from the authenticated credential, never
        // from a user-controlled payload or a 'category=official' claim.
        let result;
        if(req.url==='/v1/official/check-in'){
          result=registry.checkIn({playerId:data.playerId,serverId:claimedServer});
        }else if(req.url==='/v1/official/check-out'){
          result=registry.checkOut({playerId:data.playerId,serverId:claimedServer,
            session:data.session,snapshot:data.snapshot});
        }else{
          result=registry.getStatus({playerId:data.playerId,serverId:claimedServer});
        }
        // Keep API internal until durable state replay is implemented. This
        // service explicitly refuses live login rather than risking wipe/dupe.
        return reply(503,{error:'PERSISTENCE_ADAPTER_NOT_READY',
          message:'Central durable restart recovery and Unreal server integration required; no character was transferred.'});
      }catch(error){
        if(error instanceof OfficialTransferError)return reply(409,{error:error.code});
        return reply(400,{error:'INVALID_REQUEST'});
      }
    });
    server.listen(port,host);
  }catch(error){try{unlinkSync(lockPath)}catch{}throw error}
  return {server, async close(){
    await new Promise((done,reject)=>server.close(e=>e?reject(e):done()));
    const {unlinkSync}=await import('node:fs');unlinkSync(lockPath);
  }};
}
