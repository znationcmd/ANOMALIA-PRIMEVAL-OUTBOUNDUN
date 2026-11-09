// Official standalone horror world specification for ANOMALIA’Z PRIGIMALIA.
// DESIGN/REGISTRY ONLY: not generated terrain or an accessible UE5 map.
export const RACCONIA_VARKOVIA=Object.freeze({
 id:'racconia-varkovia',name:'RACCONIA-VARKOVIA',subtitle:'ZONE ZÉRO',
 independent:true,replaces:null,widthKm:16,heightKm:16,areaKm2:256,landFraction:.65,seaFraction:.35,
 targetLandKm2:166.4,targetSeaKm2:89.6,genre:'survival-horror',
 environment:['zombies','brouillard','pluie','nuits inquiétantes'],
 regions:Object.freeze({
  centre:['Quartier contaminé de Big City','Skarvik Police Department (S.P.D.)','Hôtel Ravenfall','Orphelinat Saint-Veyr','Secteur zéro de SKARVIK','Institut médical Veyrholm','Cathédrale Saint-Morvan'],
  nord:['Manoir Varkov','Forteresse de Valdris','Château de Drakov','Laboratoire souterrain NEXUS','Complexe scientifique HELIX','Académie de Varkov','Sanctuaire de Valdris'],
  sud:['Domaine Blackwood','Marais de Zarnov','Village de Ravenska','Station d\'épuration Morozov','District de Karzhan'],
  est:['Cité maritime de Valtéria','Paquebot Néréide','Épave du Léviathan','Centre biologique OMEGA','Métropole de Lianskar'],
  ouest:['Pénitencier de Karsen','Tour Noctis','Île militaire de Krovak','District de Volskaya','Express Nocturne']
 }),
 gameplay:['énigmes','loot','clés','bunkers','radio Morse 107 MHz'],
 plannedSites:29,implementedInUE5:false,terrainGenerated:false,playable:false
});
export default RACCONIA_VARKOVIA;
