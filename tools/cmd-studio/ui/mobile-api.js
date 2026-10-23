'use strict';
// Mobile/local browser adapter for CMD Studio. Nothing is uploaded to a server.
// Native Blender/Unreal commands intentionally do not pretend to work on phones.
if(!window.cmdStudio){
  const DB='cmd-studio-mobile-v1';
  const picks=new Map();
  const LIMIT=24*1024*1024;
  const wait=new Promise((resolve,reject)=>{
    const req=indexedDB.open(DB,1);
    req.onupgradeneeded=()=>{const db=req.result;for(const name of ['assets','projects'])if(!db.objectStoreNames.contains(name))db.createObjectStore(name,{keyPath:'id'});};
    req.onsuccess=()=>resolve(req.result);
    req.onerror=()=>reject(req.error);
  });
  const txn=async(table,mode,cb)=>{
    const db=await wait;
    return new Promise((resolve,reject)=>{
      const tx=db.transaction(table,mode),req=cb(tx.objectStore(table));
      req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error);
    });
  };
  const all=table=>txn(table,'readonly',t=>t.getAll());
  const get=(table,id)=>txn(table,'readonly',t=>t.get(id));
  const put=(table,obj)=>txn(table,'readwrite',t=>t.put(obj));
  const supported=/\.(glb|gltf|fbx|obj|blend|usd|usdz|png|jpe?g)$/i;
  const openFile=(kind)=>new Promise(resolve=>{
    const input=document.createElement('input');input.type='file';input.style.display='none';
    input.accept=kind==='project'?'.uproject':kind==='asset'?'.glb,.gltf,.fbx,.obj,.blend,.usd,.usdz,.png,.jpg,.jpeg':'*/*';
    if(kind==='asset')input.multiple=true;
    document.body.append(input);
    let ended=false;
    const finish=files=>{
      if(ended)return;ended=true;input.remove();
      resolve(files.map(file=>{const key='browser:'+crypto.randomUUID();picks.set(key,file);return key;}));
    };
    input.addEventListener('change',()=>finish(Array.from(input.files||[])));
    // Some browsers do not dispatch cancel; user may reopen picker.
    input.addEventListener('cancel',()=>finish([]));
    input.click();
  });
  async function toBase64(blob){
    const buffer=new Uint8Array(await blob.arrayBuffer());
    let binary='';
    for(let i=0;i<buffer.length;i+=32768)binary+=String.fromCharCode(...buffer.subarray(i,i+32768));
    return btoa(binary);
  }
  async function importFiles(files){
    const saved=[];
    for(const id of files||[]){
      const file=picks.get(id);if(!file)throw Error('Fichier sélectionné introuvable.');
      if(!supported.test(file.name))throw Error('Format non reconnu : '+file.name);
      if(file.size>LIMIT)throw Error('La prévisualisation mobile accepte les fichiers jusqu’à 24 Mo. Utilise le PC pour les modèles plus lourds.');
      const asset={id:crypto.randomUUID(),name:file.name,format:file.name.split('.').at(-1).toLowerCase(),
        size:file.size,source:'mobile',license:'Fichier personnel',blob:file,createdAt:new Date().toISOString()};
      await put('assets',asset);saved.push({...asset,blob:undefined});
      picks.delete(id);
    }
    return saved;
  }
  async function search({provider='polyhaven',query=''}) {
    const term=String(query||'').trim().toLowerCase().slice(0,100);
    if(!navigator.onLine)throw Error('La recherche en ligne nécessite une connexion. Ta bibliothèque locale reste accessible hors ligne.');
    if(provider==='polyhaven'){
      const res=await fetch('https://api.polyhaven.com/assets?t=models');
      if(!res.ok)throw Error('Catalogue Poly Haven indisponible.');
      const data=await res.json();
      return Object.entries(data).filter(([id,a])=>!term||[id,a.name,...(a.categories||[])].join(' ').toLowerCase().includes(term))
      .slice(0,60).map(([id,a])=>({id,name:a.name||id,provider,license:'CC0',
        thumbnail:'https://cdn.polyhaven.com/asset_img/thumbs/'+encodeURIComponent(id)+'.png?height=180',
        url:'https://polyhaven.com/a/'+encodeURIComponent(id),downloadable:false}));
    }
    if(provider==='sketchfab'){
      const res=await fetch('https://api.sketchfab.com/v3/search?type=models&q='+encodeURIComponent(term)+'&count=24');
      if(!res.ok)throw Error('Sketchfab ne permet pas cette recherche depuis le navigateur mobile. Ouvre Sketchfab directement.');
      const data=await res.json();
      return (data.results||[]).map(a=>({id:a.uid,name:a.name||'Modèle',provider,license:a.license?.label||'Voir la fiche',
        thumbnail:a.thumbnails?.images?.[0]?.url||'',url:a.viewerUrl||'https://sketchfab.com/3d-models/'+encodeURIComponent(a.uid),downloadable:false}));
    }
    throw Error('Catalogue inconnu.');
  }
  const available=async()=>{
    const [assets,projects]=await Promise.all([all('assets'),all('projects')]);
    return {assets:assets.length,projects:projects.length,blender:false,unreal:false};
  };
  const commands={
    status:available,
    settings:async()=>({blenderPath:'',unrealPath:'',libraryPath:'Stockage privé de cet appareil (IndexedDB)'}),
    assets:async()=> (await all('assets')).map(({blob,...item})=>item),
    projects:async()=>{
      const items=await all('projects');
      return {items,active:localStorage.getItem('cmdStudio:activeProject')||''};
    },
    import:async payload=>importFiles(payload?.files),
    addProject:async({file}={})=>{
      const selected=picks.get(file);
      if(!selected||!selected.name.endsWith('.uproject'))throw Error('Choisis un fichier .uproject.');
      const item={id:crypto.randomUUID(),name:selected.name.replace(/\.uproject$/,''),path:'mobile:'+selected.name};
      await put('projects',item);
      localStorage.setItem('cmdStudio:activeProject',item.path);
      picks.delete(file);return item;
    },
    previewAsset:async({id}={})=>{
      const found=await get('assets',id);
      if(!found)throw Error('Modèle absent de la bibliothèque locale.');
      if(!['glb','png','jpg','jpeg'].includes(found.format))throw Error('Sur téléphone, convertis ce fichier en GLB sur ton PC pour le visualiser.');
      return {id:found.id,name:found.name,format:found.format,data:await toBase64(found.blob)};
    },
    openAsset:async({id}={})=>{
      const found=await get('assets',id);if(!found)throw Error('Modèle absent.');
      const a=document.createElement('a'),href=URL.createObjectURL(found.blob);
      a.href=href;a.download=found.name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(href),8000);
      return true;
    },
    search,
    downloadPolyHaven:async()=>{throw Error('Sur mobile, ouvre la fiche officielle puis télécharge le modèle via ton navigateur. Réimporte ensuite le fichier dans la bibliothèque.');},
    configure:async()=>{throw Error('Les chemins Windows ne sont pas accessibles depuis le navigateur mobile.');},
    convertBlender:async()=>{throw Error('Conversion Blender réservée au PC. Les fichiers locaux peuvent être conservés et consultés sur mobile.');},
    importUnreal:async()=>{throw Error('Importation Unreal Engine réservée au PC : aucun moteur UE5 installé sur cet appareil.');},
    openTool:async()=>{throw Error('Ce logiciel externe fonctionne sur PC uniquement.');}
  };
  window.cmdStudio=Object.freeze({
    call:async(name,payload)=>{
      if(!Object.prototype.hasOwnProperty.call(commands,name))throw Error('Action inconnue : '+name);
      return commands[name](payload);
    },
    pick:openFile,
    openExternal:async url=>{
      const parsed=new URL(url);
      if(parsed.protocol!=='https:'||!['polyhaven.com','www.polyhaven.com','sketchfab.com','www.sketchfab.com'].includes(parsed.hostname))throw Error('Lien externe non autorisé.');
      window.open(parsed.href,'_blank','noopener,noreferrer');
    },
    updates:Object.freeze({
      status:async()=>({phase:'a-jour',version:'Web mobile',message:'Version Web : les nouveaux fichiers du site sont récupérés automatiquement à la prochaine ouverture.',enabled:true,feedUrl:'',hasToken:false}),
      subscribe:()=>()=>{},configure:async()=>{throw Error('Les mises à jour sont gérées par la PWA.')},
      check:async()=>({phase:'a-jour',version:'Web mobile',message:'Recharge cette page pour obtenir la version Web publiée.'}),
      install:async()=>{throw Error('Aucun installateur Windows nécessaire sur téléphone.')}
    })
  });
}
