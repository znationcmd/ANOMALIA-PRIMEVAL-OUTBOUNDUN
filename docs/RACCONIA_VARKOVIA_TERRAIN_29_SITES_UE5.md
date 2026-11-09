# RACCONIA-VARKOVIA — terrain et routes UE5

NOUVELLE CARTE indépendante de **SKARVIK**. Taille **16 × 16 km = 256 km²**, **65,19 % terre**, 34,81 % mer dans le masque généré.

Un **vrai kit de données 3D généré hors Unreal** a été livré sous `RACCONIA_VARKOVIA_16x16_29_LIEUX_UE5_SOURCE.zip` dans le Google Drive ANOMALIAZ_PRIGIMALIA.

## Contenu contrôlé
- `Terrain/RACCONIA_VARKOVIA_1025_R16.png` heightmap R16 1025×1025 ; Landscape Scale X=1562.5, Y=1562.5, Z=100 (centimètres).
- `Terrain/LandMask_1025.png` masque terre/eau.
- `Terrain/RacconiaVarkovia_Preview_Complet.glb` terrain 3D + routes + marqueurs de 29 sites.
- `Terrain/RacconiaVarkovia_Plan_29_Lieux.png` plan lisible avec les 29 emplacements.
- `Data/RacconiaVarkovia_Map.json` : noms, coordonnées XY, altitude, 29 lieux, **33 tracés** (dont traversées maritimes).
- `Data/RacconiaVarkovia_Roads.geojson` : trajets terrestres et maritimes (environ **48,4 km de voirie terrestre**).
- `Models/` : les **29 GLB de blockouts** déjà produits (non finalisés).
- `UE5/Place_Racconia_29_Sites_and_Routes.py` : script Unreal Editor pour poser marqueurs et bandes routières en **prévisualisation** sur une carte de test.
- `README_IMPORT_UE5_FR.md` : instructions d'importation dans le véritable projet et contraintes de sauvegarde.

## État et limite
Les modèles 3D préliminaires, terrain, tracés et données de placement ont été **générés, lus et vérifiés localement hors UE5**. L'accès à l'ordinateur Windows et au vrai `D:\ANOMALIA` n'est **pas disponible depuis cette conversation**. **Aucune importation, compilation, navigation, collision ou véritable version jouable UE5 n'a été testée.** Ce kit n'est pas une carte entièrement décorée ni un produit terminé.

### Intégration réelle à poursuivre
1. Ouvrir le vrai `.uproject`, créer une nouvelle map World Partition RACCONIA_VARKOVIA, importer le heightmap.
2. Vérifier l'échelle et le niveau 0 de la mer, générer eau, végétation, routes physiques et ponts.
3. Importer/remplacer les blockouts des 29 lieux, générer LOD/HLOD, collisions, navmesh, streaming.
4. Terminer les intérieurs, animer portes et puzzles, IA, inventaire, loot, réseau.
5. Tester chaque voie en véhicule, les 29 sites et faire un vrai build Unreal multijoueur.
