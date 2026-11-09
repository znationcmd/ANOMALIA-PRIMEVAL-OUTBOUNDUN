# ANOMALIA’Z PRIGIMALIA — 29 lieux horror : implémentation du gameplay (kit V0.1)

## Fichiers disponibles
Pack cloud : `Google Drive / ANOMALIAZ_PRIGIMALIA / ANOMALIAZ_29_LIEUX_GAMEPLAY_CODE_UE5.zip`.

**29 GLB**, **491 zones**, **754 points d'interaction**, **187 énigmes à produire**, catalogue unifié, moteur Python de simulation testé, plugin Unreal Engine C++ expérimental.

### Code livré (dans ZIP)
- `Horror_Catalog_29.json` : identifiants, salles, coordonnées relatives et liens d'actions.
- `runtime/horror_server.py` : règles serveur de clés, portes, secrets, loot, progression, sauvegarde et resets.
- `tests/test_horror_server.py` : 7 tests exécutés avec succès.
- `UE5/Plugins/AZHorrorRuntime` : sources du plugin C++ **non compilées** : acteurs répliqués, RPC serveur, vérification de distance, clés, persistance prototype.
- `UE5/README_PLUGIN_FR.md` : limites, câblage Blueprint et instructions.

## État précis
Le jeu local UE5 `D:\ANOMALIA` n'est pas dans ce dépôt : le repository GitHub actuel est un prototype Web/Three.js. **Aucun import UE5, aucun placement sur SKARVIK et aucune compilation du plugin ne sont vérifiés.**

Les 29 modèles sont des *blockouts* et non des bâtiments entièrement décorés. Les 187 énigmes sont identifiées, mais leurs solutions, indices et séquences animées restent à créer. Le plugin refuse volontairement les puzzles, codes Morse et coffres dont la validation sécurisée manque encore.

## Phase suivante sur le PC UE5
1. Importer le pack dans un clone de test du véritable `.uproject`, compilations C++ comprises.
2. Réaliser toutes les façades, salles, escaliers, collisions, navmesh, props et matériaux PBR.
3. Relier les 754 points aux Blueprints, avec les objets de l'inventaire réel et sauvegardes serveur.
4. Créer les solutions et indices de chaque énigme, avec validation côté serveur.
5. Établir des positions validées dans SKARVIK/World Partition puis tests multi-clients + sauvegarde.
6. Soumettre des captures et des logs de build avant toute déclaration de finalisation.
