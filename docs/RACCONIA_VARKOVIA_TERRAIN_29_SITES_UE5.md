# RACCONIA-VARKOVIA — terrain et routes UE5

NOUVELLE CARTE indépendante de **SKARVIK**. Taille **16 × 16 km = 256 km²**, **65,19 % terre**, 34,81 % mer dans le masque généré.

Un **vrai kit de données 3D généré hors Unreal** a été livré sous `RACCONIA_VARKOVIA_16x16_29_LIEUX_UE5_SOURCE.zip` dans le Google Drive ANOMALIAZ_PRIGIMALIA.

## Contenu contrôlé
- `Terrain/RACCONIA_VARKOVIA_1025_R16.png` est le PNG **source** 1025×1025, dont la première ligne est au sud. **Ne pas utiliser Z=100** : une vérification des 29 altitudes indique un décalage vertical d'un facteur 25. Pour préserver les altitudes originales, utiliser **Z=2500 cm**.
- Nouvelle conversion non destructive `scripts/ue5/worldgen/prepare_racconia_import_grade.py` → **1009×1009 RAW16 / PNG 16 bits nord en haut** ; Landscape UE5 (8×8 composants, 2×2 sections, 63 quads/section), **X=Y=1587,301587 cm et Z=2500 cm**, position recommandée (-800000,-800000,0) cm. Avant tout placement, vérifier le sens du nord et les collisions dans UE5.
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


## Avancement contrôlé le 10 novembre 2026 — raccordements des 29 sites

Le script `scripts/ue5/worldgen/audit_racconia_road_access.py` relit **directement le ZIP original** plutôt que de refaire RACCONIA-VARKOVIA. Une exécution sur le kit d'origine a confirmé : **29 sites**, **33 liaisons**, dont **28 terrestres** et **5 maritimes** ; **48,41 km de tracés terrestres** et **13,48 km de lignes maritimes**. Aucune pente segmentaire supérieure à 15 % n'a été signalée dans les points d'échantillonnage du kit, **ce qui ne prouve pas** que le relief entre ces points est carrossable.

État des accès calculés par proximité aux tracés **existants** :
- **24 sites** avec un accès candidat de moins de 200 m, en attente du contrôle terrain/collision, de vrais meshes/splines et d'un essai véhicule ;
- **2 sites** éloignés des voies terrestres existantes : **Pénitencier de Karsen** et **Tour Noctis** ; leurs accès nécessitent une conception routière nouvelle ;
- **3 sites** maritimes ou insulaires (**Paquebot Néréide**, **Épave du Léviathan**, **Île militaire de Krovak**) : **ne pas prolonger automatiquement de l'asphalte dans la mer**. Prévoir ferry, embarcadère ou accès bateau après étude.

### Reprendre depuis le vrai projet (sans doublons)

```powershell
python scripts/ue5/worldgen/audit_racconia_road_access.py --kit "C:\STAGING\RACCONIA_VARKOVIA_16x16_29_LIEUX_UE5_SOURCE.zip" --output "C:\STAGING\RACCONIA_CONTINUITE_NOUVELLE"
```

Le dossier destination doit être neuf et extérieur au projet source. Les fichiers de sortie `racconia-29-sites-ue5.csv`, `racconia-33-routes-ue5.csv`, `racconia-site-access-review.csv` et `racconia-continuation-report.json` fournissent les implantations existantes pour travailler dans **la même** map RACCONIA. L'axe Y suit la convention de ce kit RACCONIA (**Y nord positif**) ; **ne pas** appliquer la convention `-Y nord` de SKARVIK.

Ces fichiers ne créent pas automatiquement les routes Unreal, ni les bâtiments physiques, ni les collisions. Le ZIP d'origine, SKARVIK et les cartes jouables déjà installées restent inchangés.


## Correction essentielle — relief et 29 vrais modèles d'origine (2026-11-10)

**Le kit antérieur indique par erreur « Z Scale 100 cm » pour la heightmap originale. Ne pas utiliser cette valeur.** Le PNG 16 bits source code précisément **5,12 niveaux uint16/mètre**, vérifiés à partir des 29 altitudes de villages. Pour conserver la hauteur réelle : `Landscape Z Scale = 2500 cm` ; niveau marin `uint16 = 32768` à `Z = 0`. Avec Z 100 cm, les altitudes et montagnes seraient aplaties par un facteur 25.

Le nouveau générateur `scripts/ue5/worldgen/prepare_racconia_ue5_v2.py`, à exécuter sur le pack source original ZIP, produit :
- `Terrain/RACCONIA_VARKOVIA_1009x1009.r16` (8 × 8 composants, 63 quads par section, deux sections par composant ; X/Y = **1587,301587 cm**, soit exactement 16 km) ;
- les **29 blockouts d'origine** sous forme d'OBJ triangulés et transformés de mètres GLB vers centimètres Unreal, chacun associé à son ID `AZS_01`…`AZS_29` ;
- `Data/29_site_meshes.csv` avec coordonnées en cm et altitudes, `Data/33_road_waypoints.csv` avec les 28 traces terrestres et 5 itinéraires maritimes, et un manifeste JSON indiquant leurs limites.

**Commande reproductible :**
```powershell
python -m pip install numpy pillow trimesh
python scripts/ue5/worldgen/prepare_racconia_ue5_v2.py --kit "C:\Sources\RACCONIA_VARKOVIA_16x16_29_LIEUX_UE5_SOURCE.zip" --out "C:\RACCONIA_STAGE_V2_NEUF"
```

Un dossier de sortie neuf à l'extérieur de `D:\ANOMALIA` et des fichiers source est obligatoire. **Ne pas importer ces données dans SKARVIK** : coordonnées et niveaux indépendants. Dans UE5.8, créer une copie de staging du projet, un niveau World Partition séparé, importer RAW16 puis les 29 OBJ avec échelle import 1 (les sommets sont déjà en centimètres), placer les 29 acteurs aux coordonnées du CSV après validation de l'orientation de l'axe Y, des collisions, des niveaux de sous-sol et de l'eau. Les bandes routières du CSV sont des tracés de conception : il faut encore construire de vrais splines/meshes, intersections, ponts et tests véhicules.

**Statut réel :** ce pack a été généré hors Unreal à partir de l'archive originale ; les modèles restent des **blockouts**. Les niveaux natifs `.umap`, intérieurs finaux, animations, IA et routes carrossables ne sont **pas** attestés comme importés ou jouables. Ne jamais écraser les véritables cartes de `D:\ANOMALIA`.

## Correction critique des altitudes — 10 novembre 2026

Le ZIP historique conserve volontairement ses données d'origine (1025 px et ses modèles GLB). Ne pas réinjecter directement sa valeur `landscapeScaleCm[2]=100` dans le Landscape réel : le terrain serait 25 fois trop bas. La formule Unreal vérifiée contre les 29 emplacements est `h_m = (R16 - 32768) × ZScaleCm / 12800`, d'où **ZScaleCm = 2500** pour ce pack.

Créer le kit d'import séparé avec `python scripts/ue5/worldgen/prepare_racconia_import_grade.py --kit RACCONIA_VARKOVIA_16x16_29_LIEUX_UE5_SOURCE.zip --output C:/RACCONIA_IMPORT_NEW` (installer Pillow). **Le résultat reste une source**, non une carte `.umap` finie ; l'import Landscape via l'éditeur et le placement des vrais modèles sont obligatoires. Les 5 liaisons maritimes ne sont jamais transformées en routes carrossables. Toute route doit être vérifiée en collision/relief avant création de vrais splines, puis testée en véhicule dans une build UE5.
