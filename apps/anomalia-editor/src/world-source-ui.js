// The game world cannot be decoded from .umap by Three.js.
// This panel opens the actual UE5 Editor for those native files, and supports
// honest, local preview of user-supplied PNG heightmaps in ANOMALIA Editor.
export function bindWorldSources({terrain,notify,onHeightmap,onClearTerrain}){
  const find=id=>document.getElementById(id);
  const api=window.anomaliaDesktop?.unreal;
  const announce=text=>{find('realWorldInfo').textContent=text;};
  function updateWorld(status){
    const maps=find('realWorldMaps');
    maps.replaceChildren();
    find('launchRealWorld').disabled=!status?.linked;
    find('openWorldNow').disabled=!status?.linked&&!api;
    if(!status?.linked){
      announce(status?.warning||'Projet Unreal non lié. Associe AnomaliaPrimeval.uproject une seule fois.');
      return;
    }
    announce('Projet : '+status.projectName+' · Unreal '+status.engine+
      ' · '+status.mapCount+' fichiers de carte .umap détectés.');
    const preview=status.maps.slice(0,12);
    for(const file of preview){
      const row=document.createElement('div');
      row.className='worldMapEntry';row.textContent='◇ '+file;
      row.title='Carte Unreal native : cliquer sur « Ouvrir la vraie carte » pour ouvrir UE5.';
      maps.append(row);
    }
    if(status.mapCount>12){
      const label=document.createElement('small');label.textContent='+'+(status.mapCount-12)+' secteurs supplémentaires';
      maps.append(label);
    }
  }
  const desktopRequired=()=>notify('Pour ouvrir une carte .umap, utilise ANOMALIA Editor sur le PC Windows où Unreal Engine 5 est installé.',true);
  const showError=(err)=>notify('Carte UE5 : '+err.message,true);
  async function link(){
    if(!api)return desktopRequired();
    try{const r=await api.link();if(!r.cancelled)updateWorld(r);}catch(err){showError(err);}
  }
  async function open(){
    if(!api)return desktopRequired();
    try{
      const status=await api.status();
      if(!status.linked)return link();
      const result=await api.open();
      notify('Ouverture du véritable projet '+result.projectName+' dans Unreal Engine. Ce logiciel reste disponible pour les secteurs JSON/GLB.');
    }catch(err){showError(err);}
  }
  find('linkRealWorld')?.addEventListener('click',link);
  find('launchRealWorld')?.addEventListener('click',open);
  find('openWorldNow')?.addEventListener('click',open);
  if(api){
    api.status().then(updateWorld).catch(showError);
    // Newly compiled UE5 maps are detected during the current editing session.
    setInterval(()=>api.status().then(updateWorld).catch(()=>{}),60000);
  }
  else updateWorld({linked:false,warning:'Les fichiers .umap ne peuvent être ouverts que depuis l’application Windows avec Unreal Engine installé.'});

  let loaded=false;
  function labelTerrain(info){
    loaded=Boolean(info);
    find('resetTerrain').disabled=!loaded;
    const label=find('worldSourceLabel');
    const mode=find('viewportWorldMode');
    if(info){
      label.textContent=info.name+' · RELIEF 3D '+(info.width/1000).toFixed(2)+' KM';
      mode.textContent='APERÇU HEIGHTMAP · NON CONVERTI EN .UMAP';
      notify('Relief affiché en 3D : '+info.name+'. Le monde Unreal complet reste à ouvrir dans UE5.');
    }else{
      label.textContent='MONDE 3D · AUCUNE CARTE RÉELLE CHARGÉE';
      mode.textContent='APERÇU LOCAL, PAS UNE CARTE UE5';
    }
  }
  async function loadTerrain(blob,name){
    if(!blob)return;
    const width=Number(find('heightmapWidth').value);
    const info=await terrain.load(blob,{width,relief:180,name});
    labelTerrain(info);
    await onHeightmap?.(blob,info);
    return info;
  }
  find('chooseHeightmap')?.addEventListener('click',()=>find('fileTerrain').click());
  find('fileTerrain')?.addEventListener('change',async e=>{
    const file=e.target.files?.[0];if(!file)return;
    try{await loadTerrain(file,file.name);}
    catch(err){notify('Relief : '+err.message,true);}
    finally{e.target.value='';}
  });
  find('resetTerrain')?.addEventListener('click',async()=>{
    terrain.clear();labelTerrain(null);
    try{await onClearTerrain?.();}catch(err){notify('Nettoyage du relief local : '+err.message,true);}
  });
  return {loadTerrain,labelTerrain};
}
