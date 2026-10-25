// Les mises à jour sont gérées dans le processus Electron principal.
// Ce module n'expose aucun accès système au navigateur et ne télécharge rien.
const updates=window.anomaliaTools?.updates;
const toolbar=document.querySelector('.topbar');
const updateButton=document.createElement('button');
updateButton.type='button';
updateButton.id='quickUpdateCheck';
updateButton.className='update-quick-control';
updateButton.textContent='⟳ Vérifier les mises à jour';
updateButton.title='Vérifier, télécharger et appliquer la mise à jour Windows sans nouvel installateur';
updateButton.setAttribute('aria-label','Mise à jour automatique ANOMALIA Tools');
if(toolbar)toolbar.append(updateButton);
const $=selector=>document.querySelector(selector);
function paint(state){
  if(!state)return;
  const installedVersion=state.currentVersion||'—';
  const phases={initialisation:'Initialisation',veille:'Vérification automatique',verification:'Recherche',
    disponible:'Téléchargement en préparation',telechargement:'Téléchargement',prete:'À installer',
    'a-jour':'À jour',erreur:'Échec réseau'};
  updateButton.textContent='⟳ v'+installedVersion+' · '+(phases[state.phase]||'Mises à jour')+
    (state.phase==='telechargement'?' '+Math.round(state.progress||0)+' %':'');
  updateButton.title=(state.message||'')+
    (state.phase==='prete'?' — cliquer pour installer et redémarrer':' — cliquer pour vérifier');
  updateButton.classList.toggle('updateReady',state.phase==='prete');
  updateButton.classList.toggle('updateError',state.phase==='erreur');
  $('#updateVersion').textContent='v'+installedVersion;
  document.getElementById('appSidebarVersion').textContent=installedVersion;
  document.getElementById('appFooterVersion').textContent=installedVersion;
  $('#updateStatusTitle').textContent={
    initialisation:'Initialisation',developpement:'Application en développement',veille:'Surveillance activée',
    verification:'Recherche en cours',disponible:'Mise à jour disponible',
    telechargement:'Téléchargement en cours',prete:'Mise à jour prête',
    'a-jour':'Dernière version installée',erreur:'Vérification indisponible'
  }[state.phase]||'Mises à jour';
  $('#updateMessage').textContent=state.message||'Aucune information disponible.';
  const downloading=['telechargement','prete'].includes(state.phase);
  $('#updateProgress').hidden=!downloading;
  const percent=Math.max(0,Math.min(100,Math.round(Number(state.progress||0))));
  $('#updateProgressFill').style.width=percent+'%';
  $('#updatePercentage').textContent=percent+' %';
  $('#installUpdates').hidden=state.phase!=='prete';
  $('#sidebarUpdateBadge').textContent=state.phase==='prete'?'PRÊT':state.phase==='telechargement'?'↓':'AUTO';
}
if(updates){
  updateButton.onclick=async()=>{
    if(updateButton.disabled)return;
    if(updateButton.classList.contains('updateReady')){
      if(window.confirm('Installer automatiquement la version téléchargée et redémarrer ANOMALIA Tools ?'))await updates.install();
      return;
    }
    updateButton.disabled=true;
    try{paint(await updates.check());}
    catch{updateButton.title='Impossible de vérifier la mise à jour. Ouvre Mises à jour pour le détail.';}
    finally{updateButton.disabled=false;}
  };
  updates.status().then(paint).catch(()=>{
    $('#updateMessage').textContent='Statut des mises à jour indisponible.';
  });
  updates.subscribe(paint);
  $('#checkUpdates').onclick=async()=>{
    const button=$('#checkUpdates');button.disabled=true;
    try{paint(await updates.check());}
    catch{$('#updateMessage').textContent='La vérification a échoué. La version installée reste inchangée.';}
    finally{button.disabled=false;}
  };
  $('#installUpdates').onclick=async()=>{
    const confirmed=window.confirm('La nouvelle version va installer ANOMALIA Tools. Vérifie que tes fichiers ouverts sont enregistrés avant de continuer.');
    if(!confirmed)return;
    try{await updates.install();}
    catch{$('#updateMessage').textContent='Impossible d’installer maintenant. Réessaie après avoir enregistré ton travail.';}
  };
}else{
  $('#updateMessage').textContent='La mise à jour automatique fonctionne dans la version Windows installée.';
  $('#checkUpdates').disabled=true;
}
