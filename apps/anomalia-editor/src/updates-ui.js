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
    const progress=['telechargement','prete','sauvegarde','installation'].includes(s.phase);
    $('#updateProgress').hidden=!progress;
    $('#updateProgressFill').style.width=Math.max(0,Math.min(100,Number(s.progress||0)))+'%';
    $('#installUpdate').hidden=s.phase!=='prete'||s.applyWhenSaved;
    $('#installUpdate').textContent=s.applyWhenSaved?'Application automatique':'Installer et redémarrer';
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

// Commande de mise à jour toujours accessible depuis la barre principale.
// L'ancien panneau de maintenance peut être replié, mais pas le contrôle.
const mainUpdateButton=document.getElementById('checkUpdatesMain');
if(mainUpdateButton){
  mainUpdateButton.hidden=!updater;
  if(updater){
    let info=null;
    updater.status().then(state=>{
      info=state;
      mainUpdateButton.title='ANOMALIA Editor v'+(state.currentVersion||'?')+' — '+(state.message||'mises à jour');
    }).catch(()=>{mainUpdateButton.title='Mise à jour Windows indisponible';});
    updater.subscribe(state=>{
      info=state;
      mainUpdateButton.title='ANOMALIA Editor v'+(state.currentVersion||'?')+' — '+(state.message||'');
      if(state.phase==='prete')mainUpdateButton.classList.add('updateReady');
      else mainUpdateButton.classList.remove('updateReady');
    });
    mainUpdateButton.addEventListener('click',async()=>{
      mainUpdateButton.disabled=true;
      try{
        if(info?.phase==='prete'){
          // Backup and installation are already handled in the main Electron process.
          if(!info.applyWhenSaved&&confirm('La version '+(info.nextVersion||'nouvelle')+' est prête. Installer et redémarrer ANOMALIA Editor ?'))await updater.install();
          return;
        }
        const status=await updater.check();
        info=status;
        const message=status.message||'Mise à jour vérifiée.';
        mainUpdateButton.title=message;
        const toast=document.getElementById('toast');
        if(toast){
          toast.textContent='ANOMALIA Editor v'+(status.currentVersion||'?')+' — '+message;
          toast.hidden=false;
          setTimeout(()=>{if(toast.textContent.includes(message))toast.hidden=true;},5000);
        }
      }catch(error){
        mainUpdateButton.title='Impossible de vérifier les mises à jour.';
      }finally{mainUpdateButton.disabled=false;}
    });
  }
}
