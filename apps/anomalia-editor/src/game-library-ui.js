// Catalogue local ANOMALIA : ajout automatique des nouvelles ressources disponibles,
// placement sur action explicite. Les fichiers Unreal .umap/.uasset ne sont pas
// des GLB et ne sont jamais présentés comme des scènes Three.js importées.
export function bindGameLibrary({placeGLB,openMap,notify}){
  const library=window.anomaliaDesktop?.gameLibrary;
  const $=s=>document.querySelector(s);
  const items=$('#gameLibraryItems'),count=$('#gameLibraryCount');
  const category=$('#gameAssetCategory'),search=$('#gameAssetSearch');
  const updateMessage=text=>{$('#gameLibraryStatus').textContent=text;};
  if(!library){
    $('#linkGameFolder').disabled=true;
    $('#refreshGameFolder').disabled=true;
    updateMessage('Synchronisation automatique disponible uniquement dans ANOMALIA Editor pour Windows.');
    return;
  }
  let all=[], busy=false;
  const categories=[
    'Cartes et secteurs','Véhicules','Bâtiments',
    'Routes et infrastructures','Nature','Objets et équipements',
    'Matériaux et textures','Autres ressources'
  ];
  function shortBytes(bytes){
    return bytes>=1048576?(bytes/1048576).toFixed(1)+' Mo':Math.max(1,Math.ceil(bytes/1024))+' Ko';
  }
  function render(){
    const q=search.value.trim().toLocaleLowerCase('fr');
    const cat=category.value;
    const matches=all.filter(x=>(!cat||x.category===cat)&&
      (!q||[x.name,x.relative,x.category,x.kind].some(t=>String(t).toLocaleLowerCase('fr').includes(q))));
    items.replaceChildren();
    if(!matches.length){
      const empty=document.createElement('p');empty.className='libraryNotice';
      empty.textContent=all.length?'Aucun fichier ne correspond à ta recherche.':'Aucun asset trouvé dans ce dossier. Les téléchargements futurs seront détectés.';
      items.append(empty);return;
    }
    const limit=150;
    for(const item of matches.slice(0,limit)){
      const row=document.createElement('div');
      row.className='gameLibraryItem';
      const meta=document.createElement('div');
      meta.className='gameItemMeta';
      const title=document.createElement('strong');title.textContent=item.name;title.title=item.relative;
      const desc=document.createElement('small');
      desc.textContent=item.category+' · '+shortBytes(item.bytes);
      meta.append(title,desc);
      const act=document.createElement('button');
      act.type='button';
      if(item.canPlace){
        act.textContent='Placer';act.title='Ajouter ce vrai modèle GLB à la scène';
        act.addEventListener('click',async()=>{
          act.disabled=true;
          try{
            await placeGLB(item);
            updateMessage('Modèle réellement placé : '+item.name);
          }catch(e){notify('Import 3D impossible : '+e.message,true);}
          finally{act.disabled=false;}
        });
      }else if(item.canOpen){
        act.textContent='Ouvrir';act.title='Ouvrir le secteur ANOMALIA JSON (remplace la scène active)';
        act.addEventListener('click',async()=>{
          if(!window.confirm('Ouvrir cette carte ANOMALIA ? Sauvegarde ou exporte la scène actuelle avant de la remplacer.'))return;
          act.disabled=true;
          try{
            const payload=await library.read(item.id);
            if(payload.kind!=='map')throw Error('Format de carte non pris en charge');
            await openMap(payload.data);
            updateMessage('Secteur chargé : '+item.name);
          }catch(e){notify('Ouverture de carte impossible : '+e.message,true);}
          finally{act.disabled=false;}
        });
      }else{
        act.textContent=item.kind==='unreal-map'?'UE5':item.kind==='unreal-asset'?'UE5':'Source';
        act.disabled=true;
        act.title='Fichier repéré mais conversion ou chargement dans Unreal Engine nécessaire';
      }
      row.append(meta,act);
      items.append(row);
    }
    if(matches.length>limit){
      const more=document.createElement('p');more.className='libraryNotice';
      more.textContent=matches.length+' résultats. Affichage des '+limit+' premiers : précise ta recherche pour trouver les autres.';
      items.append(more);
    }
  }
  function apply(status){
    if(!status)return;
    all=Array.isArray(status.items)?status.items:[];
    count.textContent=String(status.total??all.length);
    $('#gameLibraryFolder').textContent=status.folder||
      (status.packCount?'Packs importés dans la bibliothèque privée. Tu peux aussi lier le dossier Unreal.':
       'Aucun dossier lié — sélectionne celui du jeu ou importe un pack ZIP.');
    $('#gameLibraryFolder').title=status.folder||'';
    $('#gameModelsCount').textContent=all.filter(x=>x.kind==='glb').length+' modèles GLB';
    $('#gameMapsCount').textContent=all.filter(x=>['map','unreal-map'].includes(x.kind)).length+' cartes/secteurs';
    $('#gameUnreadableCount').textContent=all.filter(x=>x.kind==='unreal-asset'||x.kind==='unreal-map').length+' fichiers Unreal';
    const selected=category.value;
    category.replaceChildren(new Option('Toutes les catégories',''));
    for(const key of categories)if(all.some(x=>x.category===key))category.add(new Option(key,key));
    if([...category.options].some(x=>x.value===selected))category.value=selected;
    render();
    if(status.syncedAt)updateMessage('Bibliothèque actualisée : '+all.length+' ressources. Prochaine vérification automatique sous 45 s.');
    else updateMessage('Choisis un dossier du jeu pour activer la synchronisation.');
  }
  library.status().then(apply).catch(e=>updateMessage('Bibliothèque inaccessible : '+e.message));
  library.subscribe(event=>{
    if(event.type==='changed')apply(event);
    else if(event.type==='error')updateMessage(event.message);
  });
  $('#linkGameFolder').addEventListener('click',async()=>{
    if(busy)return;busy=true;
    try{const result=await library.choose();if(!result.cancelled)apply(result);}
    catch(e){notify('Dossier ANOMALIA impossible à ouvrir : '+e.message,true);}
    finally{busy=false;}
  });
  $('#importGamePack').addEventListener('click',async()=>{
    if(busy)return;busy=true;
    updateMessage('Importation sécurisée des modèles et licences du pack ANOMALIA…');
    try{
      const result=await library.importPack();
      if(!result.cancelled){
        apply(result.library);
        updateMessage(result.duplicate?'Ce pack était déjà importé.':'Pack ajouté : '+result.files+' fichiers réels dans la bibliothèque privée.');
      }
    }catch(e){notify('Import ZIP impossible : '+e.message,true);}
    finally{busy=false;}
  });
  $('#refreshGameFolder').addEventListener('click',async()=>{
    if(busy)return;busy=true;
    updateMessage('Analyse des ressources locales…');
    try{apply(await library.scan());}
    catch(e){notify('Actualisation échouée : '+e.message,true);}
    finally{busy=false;}
  });
  search.addEventListener('input',render);
  category.addEventListener('change',render);
}
