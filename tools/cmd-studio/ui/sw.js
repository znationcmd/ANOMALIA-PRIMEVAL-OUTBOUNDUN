const CACHE='cmd-studio-mobile-pwa-v1';
const CORE=['./','./index.html','./style.css','./ui.js','./mobile-api.js','./generated/viewer.bundle.js','./manifest.webmanifest','./icon.svg'];
self.addEventListener('install',event=>event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(CORE)).then(()=>self.skipWaiting())));
self.addEventListener('activate',event=>event.waitUntil(Promise.all([caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))),self.clients.claim()])));
self.addEventListener('fetch',event=>{
 const req=event.request,u=new URL(req.url);
 if(req.method!=='GET'||u.origin!==self.location.origin)return;
 event.respondWith(fetch(req).then(res=>{
  if(res.ok&&res.type==='basic')event.waitUntil(caches.open(CACHE).then(cache=>cache.put(req,res.clone())));
  return res;
 }).catch(()=>caches.match(req).then(found=>found||caches.match('./index.html'))));
});
