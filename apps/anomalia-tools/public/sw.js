const NAME='anomalia-tools-pwa-v1',CORE=['./','./index.html','./manifest.webmanifest','./icon.svg'];
self.addEventListener('install',e=>e.waitUntil(caches.open(NAME).then(c=>c.addAll(CORE)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(Promise.all([caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==NAME).map(k=>caches.delete(k)))),self.clients.claim()])));
self.addEventListener('fetch',e=>{const q=e.request,u=new URL(q.url);if(q.method!=='GET'||u.origin!==location.origin)return;
e.respondWith(fetch(q).then(r=>{if(r.ok&&r.type==='basic')e.waitUntil(caches.open(NAME).then(c=>c.put(q,r.clone())));return r;})
.catch(()=>caches.match(q).then(r=>r||caches.match('./index.html'))));});
