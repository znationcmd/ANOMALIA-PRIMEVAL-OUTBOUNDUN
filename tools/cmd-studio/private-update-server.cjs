'use strict';
// Serveur privé optionnel : déployer derrière HTTPS avec volume persistant.
const http=require('node:http'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const ROOT=path.resolve(process.env.CMD_STUDIO_UPDATE_STORAGE||'/data/cmd-studio');
const READ=process.env.CMD_STUDIO_UPDATE_READ_TOKEN||'';
const WRITE=process.env.CMD_STUDIO_UPDATE_WRITE_TOKEN||'';
function auth(h,secret) {
 if(!h?.startsWith('Bearer ')||!secret)return false;
 const a=Buffer.from(h.slice(7)),b=Buffer.from(secret);
 return a.length===b.length&&crypto.timingSafeEqual(a,b);
}
function clean(s){
 const decoded=decodeURIComponent(s);
 if(!/^[a-z0-9 _().+-]{1,160}\.(?:exe|yml|blockmap)$/i.test(decoded)||decoded.includes('..')||decoded!==path.basename(decoded))throw Error('Nom de fichier interdit');
 return decoded;
}
function createServer(){
 if(READ.length<20||WRITE.length<20||READ===WRITE)throw Error('Configure deux jetons privés distincts de 20 caractères minimum.');
 return http.createServer(async(req,res)=>{
   try{
     if(req.url==='/health'){res.writeHead(200);res.end('OK');return;}
     const url=new URL(req.url,'http://127.0.0.1');
     if(url.search||!url.pathname.startsWith('/updates/cmd-studio/')){res.writeHead(404);res.end();return;}
     const file=path.join(ROOT,clean(url.pathname.slice('/updates/cmd-studio/'.length)));
     const write=req.method==='PUT';
     if(!['GET','HEAD','PUT'].includes(req.method)){res.writeHead(405);res.end();return;}
     if(!auth(req.headers.authorization,write?WRITE:READ)){res.writeHead(401,{'WWW-Authenticate':'Bearer'});res.end();return;}
     if(write){
       fs.mkdirSync(ROOT,{recursive:true});
       const tmp=path.join(ROOT,'.incoming-'+crypto.randomUUID());
       const output=fs.createWriteStream(tmp,{flags:'wx'});
       let total=0;
       try{
         for await(const chunk of req){
           total+=chunk.length;if(total>275e6)throw Error('Payload too large');
           if(!output.write(chunk))await new Promise(resolve=>output.once('drain',resolve));
         }
         await new Promise((resolve,reject)=>{output.end(resolve);output.on('error',reject)});
         if(path.basename(file)==='latest.yml'){
           const contents=fs.readFileSync(tmp,'utf8');
           if(contents.length>50000||!contents.includes('signature:')||!contents.includes('sha512:')||!contents.includes('version:'))throw Error('Manifeste signé obligatoire');
         }
         fs.renameSync(tmp,file);
         res.writeHead(201);res.end('OK');
       }catch(e){output.destroy();try{fs.rmSync(tmp,{force:true})}catch{}res.writeHead(400);res.end('Upload refusé');}
       return;
     }
     if(!fs.existsSync(file)||!fs.statSync(file).isFile()||fs.lstatSync(file).isSymbolicLink()){res.writeHead(404);res.end();return;}
     const stat=fs.statSync(file),headers={'Content-Type':file.endsWith('.yml')?'text/yaml':'application/octet-stream','Cache-Control':'private, no-store','Accept-Ranges':'bytes'};
     let start=0,end=stat.size-1,code=200;
     if(req.headers.range){
       const m=/^bytes=(\d+)-(\d*)$/.exec(req.headers.range);
       if(!m){res.writeHead(416);res.end();return;}
       start=Number(m[1]);end=m[2]?Math.min(Number(m[2]),end):end;
       if(!Number.isSafeInteger(start)||!Number.isSafeInteger(end)||start>end||end>=stat.size){res.writeHead(416);res.end();return;}
       headers['Content-Range']='bytes '+start+'-'+end+'/'+stat.size;code=206;
     }
     headers['Content-Length']=end-start+1;res.writeHead(code,headers);
     if(req.method==='HEAD'){res.end();return;}
     fs.createReadStream(file,{start,end}).pipe(res);
   }catch{if(!res.headersSent)res.writeHead(500);res.end();}
 });
}
if(require.main===module)createServer().listen(Number(process.env.PORT||8080),'0.0.0.0');
module.exports={createServer,auth,clean};
