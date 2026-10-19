# ANOMALIA PRIMEVAL OUTBOUNDUN — migration Unreal Engine 5

Ce dossier est un **socle de projet C++ UE5**, pas une version jouable du jeu.
La version JavaScript / Three.js / Electron à la racine reste inchangée et disponible.

## Démarrage
1. Installer Unreal Engine 5 et les composants C++ Visual Studio 2022 sur Windows.
2. Ouvrir `AnomaliaPrimeval.uproject` avec Unreal Engine 5 et générer les fichiers Visual Studio si demandé.
3. Compiler dans Unreal Editor. **Aucune compilation UE5 n'a encore été exécutée dans ce dépôt.**

## Migration progressive (ne pas perdre les données)
- **Étape 1** : importer les réglages JSON/XML existants par un adaptateur C++ validé ; chaque serveur garde son propre dossier, ses sauvegardes et ses permissions. Ne pas fusionner les données de joueurs ou de serveurs.
- **Étape 2** : reconstruire les cartes avec World Partition et des cellules streamées ; conserver la cible de 48 × 48 km et vérifier les 300+ km² émergés dans le terrain réel UE5. Les chiffres calculés par le prototype JS ne prouvent pas la carte UE5.
- **Étape 3** : créer les systèmes de survie, dinosaures, zombies, construction, véhicules (terre, mer, air) et les animations, collisions et physiques UE5.
- **Étape 4** : développer le multijoueur dédié, la réplication, les sauvegardes indépendantes, le contrôle d'accès d'ANOMALIA Editor et le panneau CMD Hosting.
- **Étape 5** : refaire le menu, ANOMALIA Editor et les interfaces, puis produire et tester un installateur Windows avec mises à jour versionnées.

## Attention
Les fichiers `serverDZ.cfg`, `Game.ini` et autres formats issus de DayZ/ARK ne deviennent pas automatiquement fonctionnels sous UE5. Le projet UE5 doit implémenter explicitement chaque réglage souhaité. Les plugins activés sont des dépendances de projet, **pas des véhicules ni des cartes déjà intégrés**.
