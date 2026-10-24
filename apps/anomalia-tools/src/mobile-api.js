import {zipSync} from 'fflate';
// Same actual editor pages and commands on Web/iOS/Android, persisted locally.
// Windows/Electron preload always wins; native-only tasks are not simulated.
if(!window.anomaliaTools){
  const DB='anomalia-tools-mobile-v1';
  const picked=new Map(),maxAsset=24*1024*1024;
  const dbReady=new Promise((resolve,reject)=>{
    const req=indexedDB.open(DB,1);
    req.onupgradeneeded=()=>{const d=req.result;for(const n of ['projects','files'])if(!d.objectStoreNames.contains(n))d.createObjectStore(n,{keyPath:'id'});};
    req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error);
  });
  async function query(store,mode,command){
    const db=await dbReady;
    return new Promise((resolve,reject)=>{
      const t=db.transaction(store,mode),r=command(t.objectStore(store));
      r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);
    });
  }
  const all=store=>query(store,'readonly',s=>s.getAll());
  const get=(store,id)=>query(store,'readonly',s=>s.get(id));
  const put=(store,val)=>query(store,'readwrite',s=>s.put(val));
  const name=p=>String(p||'').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9 _.-]/gi,'').trim().slice(0,55)||'Projet';
  function safeFile(file){
    if(typeof file!=='string'||file.length>260||!file||file.includes('\\')||file.startsWith('/')||
      file.split('/').some(x=>!x||x==='.'||x==='..'||x.startsWith('.')))throw Error('Chemin de fichier incorrect.');
    return file;
  }
  async function project(id){
    const value=await get('projects',id);
    if(!value)throw Error('Projet local absent de cet appareil.');
    return value;
  }
  const key=(id,file)=>id+'::'+safeFile(file);
  async function addFile(id,path,content,mime='text/plain'){
    await project(id);
    const saved={id:key(id,path),projectId:id,path,type:'file',data:content,mime,size:typeof content==='string'?new TextEncoder().encode(content).byteLength:content.size};
    await put('files',saved);
    return {path,saved:true,size:saved.size};
  }
  async function createProject({name:raw='Nouveau mod',description=''}={}){
    const title=name(raw),id=title.toLowerCase().replace(/[^a-z0-9]+/g,'-').slice(0,32)+'-'+crypto.randomUUID().slice(0,8);
    const item={id,name:title,description:String(description).slice(0,260),createdAt:new Date().toISOString()};
    await put('projects',item);
    await addFile(id,'Source/README.md','# '+title+'\n\nMod ANOMALIA local. À exporter pour utiliser sur un autre appareil.\n');
    await addFile(id,'Source/module.cpp','// '+title+'\nvoid InitAnomaliaMod() {\n    // Code de départ UE5\n}\n');
    await addFile(id,'Config/economy.json',JSON.stringify({schema:'anomalia-economy',version:1,items:[
      {id:'water_bottle',category:'Nourriture',min:5,max:20,chance:30},
      {id:'bandage',category:'Médical',min:2,max:12,chance:17}
    ]},null,2));
    return item;
  }
  async function listFiles({projectId}={}){
    await project(projectId);
    const files=(await all('files')).filter(x=>x.projectId===projectId);
    const paths=new Set();
    for(const file of files){
      const parts=file.path.split('/');
      for(let i=1;i<parts.length;i++)paths.add(parts.slice(0,i).join('/'));
    }
    return [...[...paths].map(path=>({path,type:'folder'})),...files.map(x=>({path:x.path,type:'file',size:x.size}))].sort((a,b)=>a.path.localeCompare(b.path));
  }
  async function readText({projectId,file}={}){
    await project(projectId);
    if(!/\.(js|ts|json|xml|ini|cfg|cpp|h|hpp|cs|txt|md|py|uproject|uplugin)$/i.test(file))throw Error('Format texte non éditable.');
    const x=await get('files',key(projectId,file));
    if(!x||typeof x.data!=='string')throw Error('Fichier texte introuvable.');
    return {path:file,content:x.data};
  }
  async function writeText({projectId,file,content}={}){
    if(!/\.(js|ts|json|xml|ini|cfg|cpp|h|hpp|cs|txt|md|py|uproject|uplugin)$/i.test(file))throw Error('Extension non prise en charge.');
    if(typeof content!=='string'||content.length>2000000)throw Error('Document trop volumineux.');
    return addFile(projectId,safeFile(file),content);
  }
  function verifyEconomy(input){
    if(!input||!Array.isArray(input.items)||input.items.length>2000)throw Error('Table de butin invalide.');
    const seen=new Set();
    const items=input.items.map(x=>{
      if(!/^[a-z0-9_-]{1,64}$/i.test(x.id)||seen.has(x.id))throw Error('Identifiant de butin incorrect ou dupliqué.');
      seen.add(x.id);
      const min=Number(x.min),max=Number(x.max),chance=Number(x.chance);
      if(!Number.isInteger(min)||!Number.isInteger(max)||min<0||max<min||max>100000||chance<0||chance>100)throw Error('Probabilités ou quantités incorrectes.');
      return {id:x.id,category:String(x.category||'Divers').slice(0,45),min,max,chance};
    });
    return {schema:'anomalia-economy',version:1,items};
  }
  async function getEconomy({projectId}={}){
    const value=await get('files',key(projectId,'Config/economy.json'));
    return verifyEconomy(value?JSON.parse(value.data):{items:[]});
  }
  async function saveEconomy({projectId,economy}={}){
    const parsed=verifyEconomy(economy);
    await addFile(projectId,'Config/economy.json',JSON.stringify(parsed,null,2));
    return {saved:true,count:parsed.items.length};
  }
  async function chooseAssets(){
    return new Promise(resolve=>{
      const input=document.createElement('input');input.type='file';input.multiple=true;
      input.accept='.glb,.gltf,.fbx,.obj,.usd,.png,.jpg,.jpeg,.webp,.tga,.wav,.ogg,.json,.xml,.ini';
      input.style.display='none';document.body.append(input);
      let finished=false;
      const end=files=>{
        if(finished)return;finished=true;input.remove();
        resolve(files.map(file=>{const id='picked:'+crypto.randomUUID();picked.set(id,file);return id;}));
      };
      input.onchange=()=>end([...input.files||[]]);input.addEventListener('cancel',()=>end([]));input.click();
    });
  }
  async function importAssets({projectId,paths}={}){
    if(!Array.isArray(paths)||paths.length>30)throw Error('30 fichiers maximum par import.');
    const out=[];
    for(const p of paths){
      const file=picked.get(p);
      if(!file||file.size>maxAsset)throw Error('Fichier absent ou trop volumineux pour la mémoire mobile (24 Mo maximum).');
      if(!/\.(glb|gltf|fbx|obj|usd|png|jpe?g|webp|tga|wav|ogg|json|xml|ini)$/i.test(file.name))throw Error('Format refusé : '+file.name);
      const ext='.'+file.name.split('.').at(-1).toLowerCase();
      const folder=['.png','.jpg','.jpeg','.webp','.tga'].includes(ext)?'Textures':['.wav','.ogg'].includes(ext)?'Audio':'Models';
      const filename=name(file.name.slice(0,-ext.length))+'-'+crypto.randomUUID().slice(0,6)+ext;
      const destination='Content/'+folder+'/'+filename;
      await addFile(projectId,destination,file,file.type||'application/octet-stream');
      picked.delete(p);out.push({path:destination,size:file.size});
    }
    return out;
  }
  async function previewAsset({projectId,file}={}){
    const x=await get('files',key(projectId,file));
    if(!x||!(x.data instanceof Blob)||x.size>18*1024*1024)throw Error('Aperçu limité à 18 Mo.');
    const bytes=new Uint8Array(await x.data.arrayBuffer());
    let raw='';
    for(let i=0;i<bytes.length;i+=32768)raw+=String.fromCharCode(...bytes.subarray(i,i+32768));
    return {name:x.path.split('/').at(-1),mime:x.mime,data:btoa(raw)};
  }
  function noise(x,z,seed){
    let h=(Math.imul(x,374761393)+Math.imul(z,668265263)+Math.imul(seed,1442695041))|0;
    h=Math.imul(h^(h>>>13),1274126177);
    return ((h^(h>>>16))>>>0)/4294967295;
  }
  function smooth(t){return t*t*(3-2*t);}
  function sample(x,z,seed){const xx=Math.floor(x),zz=Math.floor(z),tx=smooth(x-xx),tz=smooth(z-zz);
    return (noise(xx,zz,seed)*(1-tx)+noise(xx+1,zz,seed)*tx)*(1-tz)+
    (noise(xx,zz+1,seed)*(1-tx)+noise(xx+1,zz+1,seed)*tx)*tz;}
  function height(x,z,seed,octaves){let total=0,f=1,a=1,amp=0;for(let i=0;i<octaves;i++){total+=sample(x*f,z*f,seed+i*239)*a;amp+=a;f*=2;a*=.5;}return Math.round(total/amp*255);}
  async function generateTerrain({projectId,name:raw='Terrain',seed=42,resolution=256,scaleMeters=2000,octaves=5}={}){
    resolution=Number(resolution);seed=Number(seed);octaves=Number(octaves);scaleMeters=Number(scaleMeters);
    if(![128,256,512].includes(resolution)||!Number.isInteger(seed)||Math.abs(seed)>99999999||
      !Number.isInteger(octaves)||octaves<1||octaves>8||scaleMeters<100||scaleMeters>64000)
      throw Error('Terrain mobile : résolution 128, 256 ou 512. Utilise Windows pour 1024.');
    const canvas=document.createElement('canvas');canvas.width=canvas.height=resolution;
    const ctx=canvas.getContext('2d');if(!ctx)throw Error('Canvas 2D indisponible.');
    const img=ctx.createImageData(resolution,resolution),freq=5/resolution;
    for(let z=0;z<resolution;z++)for(let x=0;x<resolution;x++){
      const gray=height(x*freq,z*freq,seed,octaves),i=(z*resolution+x)*4;
      img.data[i]=img.data[i+1]=img.data[i+2]=gray;img.data[i+3]=255;
    }
    ctx.putImageData(img,0,0);
    const png=await new Promise((resolve,reject)=>canvas.toBlob(blob=>blob?resolve(blob):reject(Error('PNG non généré')),'image/png'));
    const root='Content/Terrain/'+name(raw).replace(/ /g,'_')+'-'+seed+'-'+resolution;
    await addFile(projectId,root+'.png',png,'image/png');
    await addFile(projectId,root+'.json',JSON.stringify({schema:'anomalia-terrain-heightmap',version:1,seed,resolution,scaleMeters,octaves,
      note:'Heightmap de base à adapter dans Unreal Engine.'},null,2));
    return {image:root+'.png',metadata:root+'.json',resolution};
  }
  async function packageMod({projectId}={}){
    const pr=await project(projectId),files=(await all('files')).filter(x=>x.projectId===projectId);
    if(files.length>800)throw Error('Archive mobile limitée à 800 fichiers.');
    const archive={},manifest={schema:'anomalia-mod-package',version:1,projectId,project:pr.name,assets:[],createdAt:new Date().toISOString()};
    let total=0;
    for(const x of files){
      const bytes=typeof x.data==='string'?new TextEncoder().encode(x.data):new Uint8Array(await x.data.arrayBuffer());
      total+=bytes.byteLength;
      if(total>90*1024*1024)throw Error('Archive mobile limitée à 90 Mo. Export sur Windows pour les gros fichiers.');
      archive[x.path]=bytes;
      const hash=await crypto.subtle.digest('SHA-256',bytes);
      manifest.assets.push({path:x.path,size:x.size,sha256:[...new Uint8Array(hash)].map(b=>b.toString(16).padStart(2,'0')).join('')});
    }
    archive['mod-manifest.json']=new TextEncoder().encode(JSON.stringify(manifest,null,2));
    const buffer=zipSync(archive,{level:1}),blob=new Blob([buffer],{type:'application/zip'});
    const filename=pr.id+'-'+Date.now()+'.zip';
    const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=filename;document.body.append(a);a.click();a.remove();
    setTimeout(()=>URL.revokeObjectURL(url),30000);
    return {path:'Téléchargements/'+filename,manifest,size:blob.size};
  }
  const operations={
    listProjects:()=>all('projects'),createProject,
    listFiles,readText,writeText,getEconomy,saveEconomy,importAssets,previewAsset,
    generateTerrain,packageMod,overview:async()=>({version:'Web mobile',privacy:'local-only',projects:(await all('projects')).length})
  };
  window.anomaliaTools=Object.freeze({
    call:async(method,payload)=>{
      if(!Object.hasOwn(operations,method))throw Error('Action mobile non disponible : '+method);
      return operations[method](payload);
    },
    chooseAssets,
    openFolder:async()=>{throw Error('Les dossiers de Windows ne sont pas accessibles depuis iOS/Android. Utilise les imports de fichiers.');},
    exportPackage:async id=>{
      const data=await packageMod({projectId:id});
      return {...data,cancelled:false};
    },
    updates:Object.freeze({
      status:async()=>({phase:'a-jour',currentVersion:'Web mobile',progress:0,message:'La version Web se met à jour automatiquement en ligne et conserve les données de cet appareil.'}),
      check:async()=>({phase:'a-jour',currentVersion:'Web mobile',message:'Recharge la PWA pour obtenir la version publiée.'}),
      install:async()=>{throw Error('Aucune installation EXE nécessaire sur téléphone.');},
      subscribe:()=>()=>{}
    })
  });
}
