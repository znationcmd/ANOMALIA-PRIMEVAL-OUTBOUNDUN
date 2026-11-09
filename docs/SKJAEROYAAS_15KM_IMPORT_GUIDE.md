# SKJÆRØYÅS — carte de survie nordique (source Unreal 5.8)

**Nom : SKJÆRØYÅS** (fiction, avec les lettres norvégiennes Æ Ø Å).
**Dimensions : 15 × 15 km = 225 km².** Carte indépendante.
**Statut : terrain source RAW16, pas une carte .umap jouable.**

## Relief et ambiances
Fjords profonds, criques navigables, îlots, grandes montagnes enneigées, landes, forêts de pins et de bouleaux, petits ports et villages de pêcheurs. Survie nordique réaliste : vent froid, pluie, neige, hypothermie, animaux sauvages, refuges et bateaux (gameplay non encore créé).

Zones de villages d'inspiration norvégienne réservées à la conception : Skjærnes, Bjørnevik, Åshamn, Fjellgård, Nordvik, Frostmyra. Ces noms sont des propositions fictionnelles ; aucun bâtiment 3D n'est déjà placé.

## Fichiers et génération
Le script scripts/ue5/worldgen/generate_skjaeroyaas.py génère **neuf tuiles RAW16 505 × 505**, chacune représentant 5 × 5 km, un aperçu topographique PNG et un manifeste avec empreintes SHA256.
Commande : python scripts/ue5/worldgen/generate_skjaeroyaas.py --output /tmp/SKJAEROYAAS_R16_SOURCE
Le dossier doit être nouveau et extérieur aux sources du jeu. Le script refuse tout écrasement.
Le moteur commun scripts/ue5/worldgen/preview_world.py peut créer des propositions de villes, routes et masques PCG pour --world skjaeroyaas, **sans les importer dans Unreal**.

## Import Unreal Engine 5.8 — à effectuer sur Windows
1. Sauvegarder le projet d'origine ; travailler sur une copie de staging, jamais dans D:\ANOMALIA directement.
2. Créer un niveau neuf indépendant, par exemple /Game/Maps/SKJAEROYAAS_15KM_STAGE, avec World Partition.
3. Importer les neuf tuiles RAW16 ou, si l'outil d'import d'Unreal l'exige, convertir la grille en une heightmap 1513 × 1513 contenant les frontières communes une seule fois. Vérifier le format accepté par Landscape et l'orientation Nord/Sud.
4. Chaque tuile a 504 quads : définir X/Y Scale = 500000 / 504 = 992,063492 cm, et Z Scale = 800 cm ; code R16 32768 = altitude zéro (niveau de la mer). Vérifier ces réglages dans UE5.
5. Contrôler les coutures, les collisions, les masses d'eau, l'échelle des montagnes et le streaming World Partition.
6. Ajouter les couches et les graphes PCG de forêts, plages, neige, routes et villages ; vérifier que les constructions existantes des autres mondes sont préservées.
7. Tester en PIE et dans une version empaquetée Windows avant de déclarer la carte jouable.

## Suivi et périmètre
Les 20 cartes d'origine restent inchangées dans config/worldgen/worlds.json. Le registre config/worldgen/expansion-worlds.json ajoute UNKNOWN HORROR X (400 km²), KÖNIGSBRÜCK (900 km²) et SKJÆRØYÅS (225 km²), soit 23 cartes et 25 865,18 km² en conception.
Le générateur crée de **véritables données de relief** prêtes à vérifier/importer mais il ne crée ni .umap, ni routes et bâtiments physiques, ni IA, ni gameplay, ni fichier de sauvegarde UE5.
