/** The ANOMALIA Editor project/world catalogue, NOT a UE5 .umap loader.
 * Source of truth: the two approved WorldGen registries (20 + 3 entries).
 * Existing local Three.js editorObjects remain associated with the loaded demo
 * scene; selecting a catalogue world NEVER silently edits or switches it.
 */
import original from '../config/worldgen/worlds.json' with {type:'json'};
import additions from '../config/worldgen/expansion-worlds.json' with {type:'json'};

const rows=[...original.worlds,...additions.worlds];
export const EDITOR_WORLD_CATALOG=Object.freeze(rows.map(w=>Object.freeze({
  id:w.id, name:w.name, widthKm:w.widthKm??null, heightKm:w.heightKm??null,
  areaKm2:w.areaKm2, registryPhase:w.phase||w.status||'planned',
  sourceAvailable:w.id==='skjaeroyaas' ? 'RAW16 staging + UE5 script' :
    w.id==='racconia-varkovia'||w.id==='unknown-horror-x'?'Source kit' : null,
  playableLevelVerified:false
})));

export const editorCatalogSummary=(id)=>{
  const w=EDITOR_WORLD_CATALOG.find(x=>x.id===id);
  if(!w)return 'Les cartes de ce catalogue ne sont pas chargées dans la scène actuelle. Tu peux éditer uniquement la scène déjà ouverte.';
  const size=w.widthKm!=null&&w.heightKm!=null
    ?w.widthKm+' × '+w.heightKm+' km':w.areaKm2+' km² (dimensions à confirmer)';
  return w.name+' · '+size+' · '+w.areaKm2+' km². '
    +(w.sourceAvailable?'Source : '+w.sourceAvailable+'. ':'')
    +'Référencée dans le catalogue ; niveau UE5 jouable non vérifié. '
    +'Cette sélection ne change PAS la scène éditée ni les bâtiments enregistrés.';
};
export function mountEditorWorldCatalog(select,message,initialId='',onSelection=()=>{}){
  if(!select||!message)throw Error('Catalogue éditeur incomplet');
  select.replaceChildren(new Option('— Voir une carte du projet —',''));
  for(const world of EDITOR_WORLD_CATALOG)select.add(new Option(world.name,world.id));
  select.value=EDITOR_WORLD_CATALOG.some(w=>w.id===initialId)?initialId:'';
  message.textContent=editorCatalogSummary(select.value);
  select.onchange=()=>{
    onSelection(select.value);
    message.textContent=editorCatalogSummary(select.value);
  };
}
