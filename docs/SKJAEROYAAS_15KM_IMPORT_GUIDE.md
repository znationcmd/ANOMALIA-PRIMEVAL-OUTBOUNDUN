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


## Kit d'intégration UE5 — deuxième phase (World Partition et marqueurs)

Après génération des tuiles :
```bash
python scripts/ue5/worldgen/prepare_skjaeroyaas_import.py --tiles C:/SKJAEROYAAS_R16_SOURCE --output C:/SKJAEROYAAS_UE5_IMPORT_NEW
```

Le dossier de sortie doit être **inexistant** et externe au projet source. Le préprocesseur valide les empreintes SHA256 et les coutures des neuf tuiles, puis assemble une heightmap indépendante **SKJAEROYAAS_1513x1513.r16**, compatible avec le système Landscape (24 sections de 63 quads par côté, 12 × 12 composants de 126 quads). La densité de points reste modeste : l'espacement de 9,9206 m par vertex correspond à une première itération du relief, non à une topographie finale haute résolution.

Le fichier `ue5-import-manifest.json` contient les paramètres d'import : **1513 × 1513 ; 63 quads/section ; 2 × 2 sections/composant ; 12 × 12 composants ; X/Y = 992,063492 cm ; Z = 800 cm ; position d'angle proposée = (-750000,-750000,0) cm**. Vérifier orientation Y (option Flip Y) et coordonnées avant de bâtir des bâtiments, car les RAW16 sont stockées du nord vers le sud. Ne pas ajuster l'échelle par simple estimation.

Le fichier `skjaeroyaas-layout.json` est généré depuis **la même équation de relief** que le RAW16 et recense :
- six **points de villages** norvégiens fictionnels (Skjærnes, Bjørnevik, Åshamn, Fjellgård, Nordvik, Frostmyra) ;
- cinq **tracés candidats** de routes (toutes les liaisons non trouvées restent signalées, sans invention de ponts) ;
- des points d'ancrage de pins/bouleaux filtrés par altitude, pente, villages et routes.
Les CSV correspondants utilisent les **centimètres d'Unreal Engine**. Ce sont des candidats, pas des objets 3D déjà placés.

### Création native d'un niveau de staging
Sur une **COPIE** du projet Windows Unreal Engine 5.8, activer le plugin **Python Editor Script Plugin** (et redémarrer l'éditeur), puis ouvrir la console Python UE5 :
```python
import sys
sys.path.insert(0, r"C:\SOURCE_ANOMALIA\unreal\EditorPython")
import stage_skjaeroyaas_world
layout = r"C:\SKJAEROYAAS_UE5_IMPORT_NEW\skjaeroyaas-layout.json"
print(stage_skjaeroyaas_world.create_new_partitioned_staging_level(layout))
# Uniquement dans une copie sauvegardée :
print(stage_skjaeroyaas_world.create_new_partitioned_staging_level(layout, confirm_create=True))
```
Cette commande crée **uniquement un nouveau niveau World Partition** nommé `/Game/Maps/SKJAEROYAAS_15KM_STAGE` et y place **six TargetPoints** pour les centres de villages. Elle ne touche pas aux autres cartes et refuse d'écraser une carte existante. **Elle n'importe pas elle-même le Landscape**.

Dans le niveau neuf : mode **Landscape → Import from File**, sélectionner `SKJAEROYAAS_1513x1513.r16`, vérifier la résolution 1513, les 12 × 12 composants et les échelles indiquées. Contrôler que les marqueurs de villages se trouvent sur le terrain (l'orientation des lignes du RAW peut imposer Flip Y). Adapter l'import si le format R16 requiert un panneau de configuration spécifique. Après contrôle, créer les zones d'eau avec Water Plugin, la vraie couche de végétation via PCG et les routes via Landscape Splines ou acteurs Spline. Ce travail **reste manuel dans l'éditeur** et nécessite les vrais meshes d'arbres/maisons/routes.

Les tests CI GitHub prouvent uniquement la validité des données R16, du tracé logique et du code Python standard. **Aucune compilation Unreal native ni scène Windows jouable n'est attestée.**

Sources Epic : https://dev.epicgames.com/documentation/unreal-engine/landscape-technical-guide-in-unreal-engine et https://dev.epicgames.com/documentation/en-us/unreal-engine/importing-and-exporting-landscape-heightmaps-in-unreal-engine .
