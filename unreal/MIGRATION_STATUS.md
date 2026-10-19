# ANOMALIA — état réel de la migration Unreal Engine 5

Branche de migration : `ue5/migration-native-20261019`. **Ne pas supprimer la version JavaScript/Three.js/Electron avant validation de la version UE5.**

## Disponible dans la branche
- Projet Unreal Engine 5 C++ (fichier `.uproject`, module, configuration de base).
- GameMode natif et sous-système de configuration de serveur avec chargement/sauvegarde JSON isolés sous `Saved/Servers/<id>/config.json`.
- Validation des identifiants de serveur et conservation des champs inconnus dans `config.json`.
- Sauvegarde de sécurité `config.json.bak` avant remplacement.
- Le mode PVE/PVP/RP/mixte, le nom, les places, le port et le multiplicateur de temps sont lisibles en C++ et exposés à Blueprints.
- Le projet d'origine et ses réglages ne sont pas effacés.

## Pas encore porté
- Terrain UE5 World Partition de 48 x 48 km et vérification physique de 300+ km² de terres.
- Gameplay jouable (déplacements, inventaire, survie, dinosaures, zombies, construction et IA).
- Physique et pilotage des véhicules (camions, avions, hélicoptères, navires et sous-marins).
- Menus UMG et ANOMALIA Editor avec permissions.
- Réplication multijoueur, serveur dédié, persistance des personnages, gestion des mods.
- Graphismes, assets 3D, animations, audio, interfaces, optimisation et intégration CMD Hosting.
- Compilations Unreal, tests de lancement et installateur Windows UE5.

## Procédure Windows
1. Installer Unreal Engine 5.x et Visual Studio 2022 avec le développement C++ pour jeux.
2. Ouvrir `unreal/AnomaliaPrimeval.uproject` et générer les fichiers du projet.
3. Compiler le module C++ et vérifier les éventuelles différences de version de l'API UE5.
4. Créer une carte UE5 et des Blueprints pour connecter les systèmes au monde.
5. Tester sur un serveur et un client distincts avant toute migration de données de joueurs.

**Les fichiers DayZ/ARK/Arma sont des formats de référence ; leurs moteurs et mods ne fonctionnent pas automatiquement sous UE5.** Aucun transfert de modèles 3D propriétaires depuis ces jeux n'est autorisé par ce dépôt. Utiliser des assets originaux ou sous licence compatible.
