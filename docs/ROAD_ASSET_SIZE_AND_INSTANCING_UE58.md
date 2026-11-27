# ANOMALIA’Z PRIGIMALIA — routes économiques sur toutes les cartes (UE5.8)

## Problème constaté dans les vrais scripts SKARVIK

Les scripts historiques (par ex.
\`unreal/Scripts/author_skarvik_final_safe_town_access_b3.py\` et
\`author_skarvik_final_safe_regional_road_fragments_v1.py\`)
font **un appel à \`spawn_actor_from_class(unreal.StaticMeshActor)\` par
petit segment d'asphalte**. World Partition sauvegarde un fichier
\`__ExternalActors__\` pour chaque acteur.

**Cela ne duplique pas nécessairement le maillage** :
\`/Game/Road/Kit_City_Road/SM_ROAD_19_10_0_0_road\` est le même asset réutilisé,
mais son acteur, sa transformation et ses métadonnées sont dupliqués.
L'augmentation de l'espace éditeur n'est PAS automatiquement la taille
du jeu téléchargé (cook/packaging compressé, assets inutilisés exclus).
Ne pas faire de prédiction de « 1000 Go » à partir des fichiers sources.

## Architecture adoptée pour les nouvelles routes

- Une ressource \`UStaticMesh\` City Sample partagée entre les instances.
- Acteur natif \`AAnomaliaZPrigimaliaRoadCluster\` contenant un
  \`UHierarchicalInstancedStaticMeshComponent\` dont la collision est \`BlockAll\`.
- Un groupe par **cellule de 128 × 128 mètres**, mesh identique,
  signature de matériaux identique, profil de collision identique,
  Data Layer et Runtime Grid identiques, **256 instances maximum**.
- Chacune conserve sa transformation monde précise (position, pente, direction, échelle).
- Il ne faut PAS fusionner les routes et les ponts, les matériaux différents,
  les routes possédant une logique gameplay unique, ni les assets mobiles.
- Le groupe doit rester **spatially loaded** pour éviter le chargement global
  des milliers de kilomètres de voies.

Les grandes cartes ne contiennent pas toutes un seul acteur de route ! Cette
solution garde les cellules proches du joueur, avec LOD/HLOD et streaming adapté.

## Fichiers fournis

- \`unreal/Source/AnomaliaZPrigimalia/World/AnomaliaZPrigimaliaRoadCluster.h/.cpp\` :
  classe UE5 source, à **compiler et tester** sous UE5.8.
- \`scripts/ue5/worldgen/plan_road_instancing.py\` : planificateur **non destructif**.
- \`tests/test_road_instancing.py\` : tests de stabilité, limites, compatibilité.
- \`unreal/Scripts/audit_skarvik_instanced_road_candidates_20261111.py\` :
  audit natif en lecture seule des vrais acteurs de SKARVIK ;
  la simple présence d'un label ne confirme PAS l'égalité des matériaux.

**Aucune conversion native 9765 → X acteurs n'est encore exécutée**.
La réduction exacte des fichiers et la taille finale du jeu ne peuvent être
connues qu'après migration sur une **copie de test**, recompilation et cook.

## Ordre d'intégration non destructif

1. Vérifier que le ZIP cloud inclut le vrai \`.umap\` et ses 12 780
   \`ExternalActors\`; préserver les originaux \`D:\ANOMALIA\`.
2. Compiler la nouvelle classe C++ dans un stage séparé ; vérifier
   \`ConfigureRoadMesh\` et \`AddRoadPieceWorld\`.
3. Auditer mesh, override de matériaux, collisions, mobilité et Data Layers
   de chaque acteur déjà sauvegardé. Ne pas inférer ces informations
   à partir de son nom.
4. Dupliquer la map complète (y compris \`__ExternalActors__\`), puis
   remplacer **un secteur test** par des instances dans le seul stage.
5. Comparer géométrie, jointures, collision voiture/joueur,
   changement de cellule, trous d'asphalte et performances PIE/SM5.
6. Comparer sur le stage : fichiers \`ExternalActors\` et leur poids
   avant/après ; ensuite produire un **cook Windows** et mesurer la taille
   exacte \`.pak\`/\`.ucas\`/\`.utoc\` compressée.
7. Si tests réussis, migrer progressivement le reste, une cellule à la fois.
   Ne pas supprimer les originaux sans test ni sauvegarde vérifiée.

## Budget distribution

À mesurer, plutôt qu'inventer :

- **Poids source** : UE5 + assets importés + DerivedDataCache + Saved + Intermediate.
- **Poids des cartes réellement préparées** : uniquement assets référencés ;
  éviter \`Cook everything\` si ce n'est pas nécessaire.
- **Poids du téléchargement** : fichiers packagés (compressés suivant réglages).
- **DLC / chunks** : les nombreuses cartes peuvent être proposées séparément
  afin que le joueur n'installe pas d'emblée tous les mondes.

L'instancing réduit surtout les acteurs, la surcharge mémoire/draw calls et
les \`ExternalActors\`. La majeure partie des 100 Go de City Sample peut être
liée aux textures et géométries : il faudra aussi gérer LOD/Nanite, références,
qualité des textures et cook sélectif. Aucun chiffre de réduction en gigaoctets
n'est promis avant mesure d'une build.
