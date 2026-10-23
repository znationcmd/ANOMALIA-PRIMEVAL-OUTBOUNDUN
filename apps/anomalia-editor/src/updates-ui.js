// Le système de mise à jour concerne uniquement l’application Windows installée.
// La version web conserve exactement les mêmes fonctions de création sans accès au PC.
const updater=window.anomaliaDesktop?.updates;
const panel=document.getElementById('updaterPanel');
if(updater&&panel){
  panel.hidden=false;
  const $=s=>document.querySelector(s);
  let lastState=null;
  const render=s=>{
    lastState=s;
    $('#editorVersion').textContent='v'+(s.currentVersion||'—');
    $('#updateState').textContent=s.message||'Statut des mises à jour inconnu.';
    const progress=s.phase==='telechargement'||s.phase==='prete';
    $('#updateProgress').hidden=!progress;
    $('#updateProgressFill').style.width=Math.max(0,Math.min(100,Number(s.progress||0)))+'%';
    $('#installUpdate').hidden=s.phase!=='prete';
  };
  updater.status().then(render).catch(()=>{$('#updateState').textContent='Mises à jour indisponibles sur cet appareil.';});
  updater.subscribe(render);
  $('#checkForUpdates').onclick=async()=>{
    const b=$('#checkForUpdates');b.disabled=true;
    try{render(await updater.check());}
    catch(e){$('#updateState').textContent='Vérification impossible. La version actuelle reste installée.';}
    finally{b.disabled=false;}
  };
  $('#installUpdate').onclick=async()=>{
    if(lastState?.phase!=='prete')return;
    if(!confirm('Installer la nouvelle version d’ANOMALIA Editor et redémarrer ? Sauvegarde ta scène avant de continuer.'))return;
    try{await updater.install();}
    catch{$('#updateState').textContent='Installation impossible pour le moment.';}
  };
}
