// Per-scene IndexedDB terrain cache. Local to the same Windows or mobile user;
// no sync, no project deletion, no change to the existing scenes DB.
const DB='anomalia-editor-terrain-local-v1';
function db(){
  return new Promise((resolve,reject)=>{
    const req=indexedDB.open(DB,1);
    req.onupgradeneeded=()=>{
      if(!req.result.objectStoreNames.contains('terrain'))
        req.result.createObjectStore('terrain',{keyPath:'sceneId'});
    };
    req.onsuccess=()=>resolve(req.result);
    req.onerror=()=>reject(req.error);
  });
}
async function command(mode,callback){
  const database=await db();
  return new Promise((resolve,reject)=>{
    const tx=database.transaction('terrain',mode),store=tx.objectStore('terrain'),result=callback(store);
    result.onsuccess=()=>resolve(result.result);
    result.onerror=()=>reject(result.error);
    tx.onabort=()=>reject(tx.error||Error('Enregistrement local du terrain interrompu.'));
    tx.oncomplete=()=>database.close();
  });
}
function validateKey(key){
  if(typeof key!=='string'||key.length>120||!key)throw Error('Identifiant de scène manquant.');
  return key;
}
export async function saveTerrain(sceneId,blob,settings){
  validateKey(sceneId);
  if(!(blob instanceof Blob)||blob.size>32*1024*1024)throw Error('Image de terrain trop volumineuse.');
  return command('readwrite',store=>store.put({sceneId,blob,settings,savedAt:Date.now()}));
}
export async function loadTerrain(sceneId){
  return command('readonly',store=>store.get(validateKey(sceneId)));
}
export async function clearTerrain(sceneId){
  return command('readwrite',store=>store.delete(validateKey(sceneId)));
}
