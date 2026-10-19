# ANOMALIA PRIMEVAL OUTBOUNDUN — migration Unreal Engine 5

Ce dossier est un **socle de projet C++ UE5**, pas une version jouable du jeu.
La version JavaScript / Three.js / Electron à la racine reste inchangée et disponible.

## État du portage C++ (19 octobre 2026)

**Implémenté dans le dépôt UE5 (code source, non compilé dans Unreal Editor) :**
- `AAnomaliaGameMode` sélectionné dans `Config/DefaultEngine.ini`.
- `AAnomaliaSurvivor` : personnage 3D de base, caméra à la troisième personne, clavier ZQSD/WASD à configurer selon le clavier, déplacement/saut, faim/soif/santé répliqués et calculés côté serveur.
- `UAnomaliaConfigLibrary` : API accessible aux Blueprints pour charger/sauvegarder `config.json` par serveur et les profils joueurs sous `Saved/Servers/<id>/userProfile/<id>.json`. Les identifiants sont validés, les JSON contrôlés et les écritures passent par un fichier temporaire. Les champs inconnus de `config.json` sont conservés.
- `Config/Anomalia/config.json` : modèle UE5 du fichier principal, avec port, nom, places, mode RP/PVP/PVE/mixte et multiplicateur de temps.
- `scripts/migrate-to-ue5.py` : copie non destructive de **tous** les fichiers `public/config` dans `unreal/Config/Anomalia/Legacy`. Les doublons identiques sont ignorés, les conflits sont signalés sans écraser les données. Commande à la racine : `python scripts/migrate-to-ue5.py`.

**Non terminé :** aucune carte `.umap` n'a été construite ; il reste à porter les 48 × 48 km en World Partition, la géométrie des routes, les zombies, dinosaures, véhicules terrestres/navals/aériens, ANOMALIA Editor, les constructions, l'inventaire, le combat, l'authentification des administrateurs, le réseau dédié complet, CMD Hosting et le système de mises à jour du futur exécutable UE5. Les modèles 3D procéduraux Three.js ne se convertissent pas automatiquement en assets Nanite/Chaos UE5.

**Sécurité :** la bibliothèque de profils doit être appelée par du code serveur autorisé ; les fonctions Blueprint ne constituent pas un système d'authentification. Ne jamais exposer des écritures de profils à des clients non vérifiés.

**Vérification :** compiler dans Unreal Engine 5 sur Windows avec Visual Studio et exécuter les tests multijoueurs. Les tests GitHub de la version JS ne prouvent pas la compilation du projet UE5.

## Nouveau lot — catalogue et conduite UE5 (19 octobre 2026)

- `UAnomaliaVehicleCatalog` : **27 définitions uniques** accessibles dans les Blueprints, couvrant camions/remorques, quads, buggys, motoneiges, motos, karting, F1, SUV, fourgons, police/gendarmerie, pompiers, ambulance, blindés, monster trucks, jet-skis, zodiaques, porte-avions, navires de guerre, sous-marins, avions de chasse et hélicoptères. Les valeurs de vitesse, places et stockage sont des valeurs initiales **ajustables**, pas des performances simulées.
- `AAnomaliaVehiclePawn` : prototype C++ **possédable et répliqué**, caméra troisième personne, commandes avant/arrière/direction, validation de l'identifiant de véhicule par le serveur, déplacements calculés côté serveur. Il faut créer des Blueprints enfants, attribuer les vrais modèles 3D, collisions et animations, et programmer la montée/descente.
- `AAnomaliaGameMode::SpawnServerVehicle` : création d'un véhicule par **logique serveur de confiance** ; pas de RPC public autorisant n'importe quel joueur à créer un véhicule.
- `tests/test_unreal_port.py` et workflow `ue5-source-checks.yml` : contrôles statiques de la liste des véhicules et de l'importation non destructive. **Ce ne sont pas des tests de compilation UE5.**

**Limites actuelles :** la conduite est une première base `UFloatingPawnMovement` générique. La physique des roues Chaos, les remorques articulées, la flottabilité des navires, la plongée des sous-marins, les vols, le carburant, les armes, les passagers et la persistance des véhicules **ne sont pas encore implémentés**. Les 27 définitions ne sont pas 27 véhicules finis ou photoréalistes. La compilation Unreal Engine 5 sur Windows reste indispensable.

## Nouveau lot — interaction véhicule (19 octobre 2026)

- **E** à pied : demande d'entrée dans le véhicule libre le plus proche, à **4,5 mètres maximum**. Le serveur vérifie la distance, l'état du personnage et la disponibilité de la place conducteur.
- **E** au volant : sortie du véhicule et reprise du **même personnage**, sans réinitialiser sa santé ni ses références de progression.
- Les demandes utilisent des RPC serveur fiables ; un client ne peut pas prendre le volant d'un véhicule déjà occupé. Les mouvements restent calculés côté serveur.
- Ce système est une **implémentation C++ à compiler et tester sous UE5**, pas une fonctionnalité vérifiée dans un exécutable. Il reste à créer des Blueprints de véhicules avec collisions adaptées, animations d'entrée/sortie, passagers et placement sûr du personnage à la sortie.

## Lot suivant — carburant et paramètres isolés (19 octobre 2026)

- `AAnomaliaVehiclePawn` : jauge `FuelPercent` répliquée, consommation uniquement sur le serveur quand le conducteur accélère, arrêt de la propulsion et de la direction lorsque le carburant est épuisé. Le taux `FuelConsumptionPerSecond` est personnalisable dans les Blueprints enfants.
- `RefuelOnServer` : API de ravitaillement réservée à une logique serveur de confiance ; aucun RPC client public permettant de s'attribuer du carburant. Il reste à développer les stations-service, réservoirs, consommation propre à chaque véhicule et sauvegarde du carburant.
- `AAnomaliaGameMode::InitGame` : lit les paramètres propres au serveur via l'option de lancement `?AnomaliaServerId=rp-corse` et `Saved/Servers/rp-corse/config.json`. Les identifiants sont validés ; aucune modification automatique d'un fichier malformé.
- Les tests `tests/test_unreal_port.py` contrôlent ces garanties **statiquement**. La compilation, la physique, le multijoueur et l'exécution sous UE5 restent à vérifier dans Unreal Editor sur Windows.

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
