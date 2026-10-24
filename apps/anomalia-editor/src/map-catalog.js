// Carte du lanceur : seules les scènes locales enregistrées et les cartes Unreal
// découvertes sur le poste sont proposées. Aucun monde fictif ou capture DayZ.
export function buildMapCatalog(localScenes=[],unrealStatus=null){
  const scenes=Array.isArray(localScenes)?localScenes:[];
  const maps=unrealStatus?.linked&&Array.isArray(unrealStatus.maps)?unrealStatus.maps:[];
  const safeScenes=scenes.filter(x=>x&&typeof x.id==='string'&&typeof x.name==='string')
    .map(x=>({id:'local:'+x.id,key:x.id,title:x.name||'Carte sans nom',
      type:'local',subtitle:x.objects===1?'1 objet':(x.objects||0)+' objets',
      edited:x.edited||'',description:'Scène ANOMALIA locale · chargement intégré'}));
  const safeMaps=maps.filter(x=>typeof x==='string'&&/^[A-Za-z0-9_/-]+\.umap$/.test(x))
    .map(x=>({id:'ue5:'+x,key:x,title:x.split('/').pop().replace(/\.umap$/i,'').replace(/[_-]+/g,' '),
      type:'ue5',subtitle:x,edited:'',description:'Carte Unreal native · ouverture dans UE5'}));
  return [...safeScenes,...safeMaps];
}
export function filterMapCatalog(catalog,kind='all',term=''){
  const q=String(term).toLocaleLowerCase('fr').trim();
  return catalog.filter(x=>(kind==='all'||x.type===kind)&&
    (!q||(x.title+' '+x.subtitle).toLocaleLowerCase('fr').includes(q)));
}
