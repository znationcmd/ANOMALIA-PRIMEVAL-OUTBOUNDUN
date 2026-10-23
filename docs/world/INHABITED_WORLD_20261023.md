# Archipel habité ANOMALIA — état réel au 23 octobre 2026

La nouvelle cible est `/Game/Maps/ANOMALIA_Inhabited_v1`, un monde distinct de 48 × 48 km. Le code crée un paysage World Partition original avec 27 emplacements aménagés. Le sol sous les quartiers est aplani avec une transition de 200 m ; le littoral et les fonds marins restent ceux de la géographie ANOMALIA. L'archipel v2 existant n'est jamais remplacé.

## Ce qui a réellement été reçu et préparé

Le téléchargement direct a réussi pour les huit sources déjà épinglées dans `docs/art/realism-validation-sources.json`. Chaque fichier reçu correspond à sa taille et à son SHA-256 attendus. Les modèles préparés ont été produits par `scripts/vehicle-assets/prepare-realism.mjs`, avec leurs crédits, leurs textures et un manifeste. Cela ne constitue pas une importation Unreal.

| Asset | Source/licence | Préparation |
| --- | --- | --- |
| Maison à deux étages | Innerscene, CC0 | 12 238 triangles ; portes d'entrée retirées dans cette variante ; 11,056 × 14,67 m au sol |
| Arbre | Poly Haven, CC0 | scan détaillé ; 1 072 213 triangles avant LOD ; variante d'environ 3,4 m de haut, insuffisante seule pour toutes les grandes forêts |
| Herbe | Poly Haven, CC0 | géométrie et textures conservées |
| Rochers moussus | Poly Haven, CC0 | géométrie et textures conservées |
| Sol forestier | Poly Haven, CC0 | textures PBR 2K, surface de validation préparée |
| Asphalte | Poly Haven, CC0 | textures PBR 2K, bande de route de validation préparée |
| Voiture Concept | Khronos glTF Sample Assets, CC BY 4.0 | logos exclus retirés ; modèle statique préparé |
| Camion | Innerscene, CC0 | modèle statique préparé, orientation corrigée |

**Ces assets ne sont pas tous photoréalistes validés.** La maison nécessite notamment une inspection visuelle de ses matériaux. Les sources PBR reçues sont en 2K ; aucune livraison de textures 16K n'est déclarée.

## Assemblage ajouté au projet

`create_inhabited_archipelago.py` exige des meshes réellement importés et identifiés par leur empreinte, puis crée un nouveau monde. Il refuse de remplacer un monde existant. Il pose les maisons avec collision, regroupe la végétation par type et par kilomètre dans des composants HISM, ajoute un départ joueur, l'éclairage et une région marine native. Le matériau de paysage utilise les textures de sol vérifiées avec des UV en espace monde. Aucune sphère de végétation ni maison en cube n'est utilisée par cet assembleur.

Le calcul local, relié directement au code C++ du nouveau relief, donne :

- 27 secteurs habités et 4 760 placements de maisons ;
- 15 447 placements de végétation et de rochers ;
- 344 lots trop bas/hauts et 188 lots trop pentus rejetés ;
- au maximum 12 cm de variation de sol sous les maisons, avec au plus 2 cm au-dessus du sol au point bas ;
- côtes et fonds marins inchangés dans les contrôles numériques.

Les couloirs réservés entre parcelles restent libres. Ce ne sont pas encore des routes construites. Le terrain a une maille d'environ 15,87 m ; cette maille et les textures reçues ne prouvent pas un rendu « ultra HD » du monde entier.

**La carte `.umap` n'a pas été créée dans cette session : aucun Unreal Editor n'est installé dans l'environnement de travail actuel.** Le plan JSON et les tests ne remplacent ni une exécution du script dans UE5.8 ni un essai en jeu.

## Références de composition demandées

Les éléments ci-dessous guident la composition originale ; aucun terrain, maillage, texture, plan de ville ou bâtiment extrait de ces jeux n'est inclus.

| Référence | Principe à retenir | Source |
| --- | --- | --- |
| Chernarus | Hiérarchie entre villes côtières, bourgs intérieurs, villages et repères | https://dayz.wiki.gg/wiki/Chernarus_%28Map%29 |
| Livonia | Paysage rural, refuges, météo et trajets entre zones habitées | https://dayz.com/article/general/on-the-road-to-livonia |
| Sakhal | Archipel, secteurs enneigés, relief exposé et grandes installations navales | https://dayz.com/article/game-update/DayZ-Frostline-Release |
| Nasdara | Région aride, villes abandonnées, infrastructures industrielles ; couverture et chemins protégés | https://dayz.com/article/general/DayZ-Badlands-coming-2026 ; https://dayz.com/article/Dev-blogs/DayZ-Badlands-Dev-Blog-Week-73 |
| Deer Isle | Terrain insulaire, exploration et transformation d'une référence réelle selon le gameplay | https://www.patreon.com/deerisle/about?l=en-GB |
| Namalsk | Atmosphère, objectifs et zones souterraines conçues avec le terrain | https://www.nightstalkers.cz/author/ ; https://www.nightstalkers.cz/2026/10/15/out-with-the-workarounds/ |

Le terme « lux » dans la demande n'a pas permis d'identifier une carte avec certitude ; aucune référence n'est inventée pour ce nom.

## Ce qui reste pour une carte complète

L'assemblage actuel répète une seule maison détaillée. Il faut encore diversifier l'architecture, construire les services et intérieurs, les routes et réseaux de transport, ports, aéroports, ponts, stations, circuits, équipements, bases et lieux d'exploration. La végétation actuelle est une base clairsemée ; elle ne constitue pas des forêts denses finies. La mer possède des bornes de navigation, sans rendu d'océan réaliste livré dans ce lot. Les matériaux de chaque biome, le relief de proximité, le streaming, les collisions en jeu et les performances doivent être contrôlés dans Unreal. Les cartes de référence ne sont pas reproduites à l'identique.

Tests locaux : cinq tests de population reliés au noyau C++ réel, deux contrôles d'includes natifs et compilation syntaxique des scripts Python réussis. Compilation du module Unreal et validation GPU non exécutées.
