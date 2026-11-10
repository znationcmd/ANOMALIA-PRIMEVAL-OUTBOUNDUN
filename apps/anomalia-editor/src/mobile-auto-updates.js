// Mobile PWA update channel. The build revision is injected by Vite and the
// release.json is generated from the exact Git commit packaged in this build.
// Always save the local scene before reloading; never clear IndexedDB or caches
// containing application project data. Updates require a reachable HTTPS host.
const CURRENT_REVISION=__ANOMALIA_WEB_BUILD__;
const POLL_MS=4*60*1000;

export function startMobileAutoUpdates({saveBeforeReload,notify=()=>{}}={}){
  if(typeof window==='undefined'||typeof navigator==='undefined')return {active:false};
  if(window.anomaliaDesktop||!('serviceWorker' in navigator)||
      !(location.protocol==='https:'||location.hostname==='localhost'))return {active:false};
  if(typeof saveBeforeReload!=='function')throw Error('Local save callback required');

  let busy=false;
  let lastSuccess=0;
  const check=async(force=false)=>{
    if(busy||document.visibilityState==='hidden'||!navigator.onLine)return false;
    // Avoid double reload loops when browser focus and visibility events coincide.
    if(!force&&Date.now()-lastSuccess<12000)return false;
    try{
      const url=new URL('./release.json',window.location.href);
      url.searchParams.set('check',String(Date.now()));
      const response=await fetch(url.href,{cache:'no-store',credentials:'same-origin'});
      if(!response.ok)return false;
      const type=response.headers.get('content-type')||'';
      if(!type.includes('json'))return false;
      const release=await response.json();
      if(!release||typeof release.revision!=='string'||
         !/^[0-9a-zA-Z._-]{6,100}$/.test(release.revision))return false;
      lastSuccess=Date.now();
      if(release.revision===CURRENT_REVISION)return false;
      busy=true;
      notify('Mise à jour détectée : sauvegarde locale de la scène avant actualisation…');
      try{
        await saveBeforeReload();
      }catch(error){
        busy=false;
        notify('Sauvegarde impossible : mise à jour reportée pour protéger la scène.');
        return false;
      }
      // Web / standalone iOS PWA reload: it fetches the newest Vite hashed bundle.
      // No reinstall and no deletion of locally stored projects is necessary.
      window.location.reload();
      return true;
    }catch{
      // Offline mode and captive portals must not interrupt editing.
      return false;
    }
  };

  const install=async()=>{
    try{
      const registration=await navigator.serviceWorker.register('./sw.js',{updateViaCache:'none'});
      await registration.update().catch(()=>{});
    }catch{
      // The website still works even if service-worker registration is blocked.
    }
    await check(true);
  };
  window.addEventListener('load',install,{once:true});
  window.addEventListener('online',()=>check(true));
  window.addEventListener('focus',()=>check(true));
  document.addEventListener('visibilitychange',()=>{
    if(document.visibilityState==='visible')check(true);
  });
  window.setInterval(()=>check(false),POLL_MS);
  return {active:true,revision:CURRENT_REVISION,check};
}
