# VALHALLA EXTINCTION — ANOMALIA’Z PRIGIMALIA, source UE5.8 haute résolution

Carte utilisateur **24 × 24 km = 576 km²**, thème **100 % viking** avec **zombies Draugr vêtus de tenues vikings** (pas de bâtiments, véhicules, armes ni vêtements modernes).

## Source principale dans Google Drive

Dossier : `ANOMALIAZ_PRIGIMALIA/VALHALLA_EXTINCTION`.
Archive **`ANOMALIAZ_VALHALLA_EXTINCTION_24x24_UE58_SOURCE.zip`** (source existante du projet, vérifiée sans modification) :
- Relief RAW16 et PNG 16 bits **4033 × 4033** exactement, fichiers terrain bit-à-bit identiques.
- Masques PNG de six biomes, 36 maillages GLB de terrain proxy ; **ces tuiles proxy ne sont pas le terrain Landscape final**.
- 28 lieux vikings, 555 placements prévus d'architecture viking, 374 ancres Draugr, 67 routes candidates.
- Catalogues tenues en laine et fourrure, cottes de mailles, casques sans cornes, haches, épées, boucliers, lances ; zombies en tenue viking uniquement.
- SHA256 de l'archive : `5525a74c6b1174f47db9e205bea25dd2666604a04d7430e616f0cce57a09acea`.

**Aucun vrai bâtiment ou personnage zombie 3D sous licence n'est livré dans l'archive**. Les références `/Game/ValhallaExtinction/...` sont des références attendues, non des fichiers `.uasset` réellement présents.

## Vrai niveau Unreal — étapes

1. Sauvegarder le projet local **D:\\ANOMALIA** et préparer une copie de travail. Les autres cartes doivent rester intactes.
2. Télécharger et extraire l'archive sur le PC. Activer le plugin **Python Editor Script Plugin** d'Unreal Engine 5.8.
3. Copier `unreal/EditorPython/stage_valhalla_extinction_4033.py` dans un endroit accessible à la console Python UE. Exécuter `create_level(zip)` d'abord en mode diagnostic ; puis `create_level(zip, confirm_create=True)` **sur la copie du vrai projet**, pour créer `/Game/Maps/VALHALLA_EXTINCTION` avec 28 marqueurs de villages et 374 marqueurs Draugr. **Cela ne crée pas encore le terrain**.
4. Dans ce nouveau niveau uniquement, **Landscape > Import from File**, choisir `Terrain/VALHALLA_EXTINCTION_4033x4033_R16.png` (ou `.r16`). Résolution : **4033 × 4033**, 32 × 32 composants, 63 quads/section, 2 × 2 sections/composant, X et Y **595,238095 cm**, Z **500 cm**. Centrer le relief sur (0,0). Vérifier **Flip Y** : le raster source a sa première ligne au sud et les coordonnées des lieux ont Y positif vers le nord.
5. Construire le matériau Landscape avec les masques PNG `BiomeLayers/` ; définir la mer à Z = 0, plages, neige, taïga, routes et collisions. Avant de placer les bâtiments, vérifier l'alignement 3D entre coordonnées et véritable terrain.
6. Dans le fichier `config/worldgen/valhalla-4033-assets.template.json`, renseigner avec de **vrais** chemins `/Game/...` déjà importés pour les **16 types de bâtiment** et **8 Blueprints de Draugr**. Les Draugr doivent avoir leur SkeletalMesh animé, tenues vikings, IA, comportement, navigation et loot.
7. `place_licensed_content(zip, bindings, confirm_place=True)` peut alors placer les meshes et classes **si et seulement si** le vrai Landscape existe et tous les assets sont trouvés. Contrôler les échelles, pentes, collisions, positions d'eau, navigation et HLOD.
8. Enfin, tester la carte dans **Play In Editor**, lancer une partie Windows compilée et valider le système de sélection de carte du vrai jeu. **Aucun de ces tests n'a pu être exécuté depuis les outils cloud.**

## État exact

- **Vérifié** : intégrité ZIP, résolution RAW16 et PNG16, 28 villes, 555 emplacements, 374 Draugr, 36 proxies, 6 masques, taille 24 × 24 km d'après les paramètres d'import.
- **Pas fait** : `.umap` créé sur le PC, Landscape importé dans le projet, `.uasset` des vrais bâtiments et personnages, IA/vêtements réels, routes splines, gameplay, build jouable. Ne pas déclarer la carte terminée.
- Le prototype de génération **2017 × 2017** issu d'une autre approche ne doit **pas** être mélangé avec cette source 4033 : les hauteurs, côtes et coordonnées sont différentes.

Docs Epic : https://dev.epicgames.com/documentation/unreal-engine/landscape-technical-guide-in-unreal-engine et https://dev.epicgames.com/documentation/unreal-engine/importing-and-exporting-landscape-heightmaps-in-unreal-engine .