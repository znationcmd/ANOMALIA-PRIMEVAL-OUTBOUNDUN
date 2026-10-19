# ANOMALIA PRIMEVAL OUTBOUNDUN — migration Unreal Engine 5

## Lot UE5 — réglages de carburant et vitesse par véhicule (19 octobre 2026)

Chaque entrée de `Saved/Servers/<id>/vehicles.json` peut maintenant préciser `fuelPercent` (0 à 100), `fuelConsumptionPerSecond` (0 à 10) et `speedMultiplier` (0,1 à 3). Ces paramètres sont **validés côté serveur**, appliqués à l'apparition et propres au dossier du serveur. Les entrées invalides sont ignorées sans écraser le fichier. La jauge de carburant et le multiplicateur de vitesse sont répliqués ; aucun RPC client ne permet de modifier ces valeurs. Le modèle de configuration est `Config/Anomalia/vehicles.example.json`.

Ce lot reste un **prototype de conduite générique** : il n'ajoute pas la physique Chaos, les modèles 3D finaux, la plongée, le vol ni un installateur UE5. Les tests automatiques sont des contrôles statiques, pas une compilation Unreal Engine.


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

### Catalogue des réglages

`Config/Anomalia/settings-catalog.json` recense les réglages UE5 avec type,
plage, valeur par défaut, portée, mécanisme de code et état vérifié. `functional`
signale un raccordement source explicite au runtime, `partial` un raccordement
incomplet, `not_implemented` un réglage sans mécanisme actif et `migration_only`
un ancien fichier conservé sans adaptateur UE5. Les lignes `server.port`,
`server.maxPlayers`, `server.mode`, `server.thirdPerson` et `server.timeMultiplier`
ne prouvent pas l'ouverture réseau, la capacité, les règles de mode, une caméra
à la première personne ou une horloge de jeu : leur statut reste partiel. Les
fichiers DayZ/ARK et formats `.pbo`, `.paa`, `.edds`, `.ark`, `.c`, `.uasset` et
`.umap` sont explicitement conservés comme sources de migration, jamais déclarés
exécutables par UE5. Les contrôles `tests/test_ue5_config_catalog.py` vérifient
les valeurs de configuration contre les modèles et chemins de code présents.

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

## Lot supplémentaire — apparition des véhicules par serveur (19 octobre 2026)

Le GameMode UE5 lit désormais **uniquement** `Saved/Servers/<identifiant>/vehicles.json` au démarrage de la partie sur le **serveur**. Un modèle non destructif est disponible dans `Config/Anomalia/vehicles.example.json`. Copier ce modèle vers le dossier du serveur voulu puis adapter les identifiants et positions `x,y,z,yaw` en **centimètres UE5**. Le fichier n'est jamais créé ni écrasé automatiquement.

- 27 types autorisés, contrôlés par le catalogue C++ ; maximum **64 véhicules** chargés, taille maximale **256 Kio**, coordonnées finies dans les limites de 48 km.
- Aucun RPC de spawn libre côté client. Les fichiers et les véhicules d'un serveur ne sont pas chargés depuis un autre serveur.
- Les véhicules restent des **prototypes sans modèles 3D finalisés**. Les collisions du niveau, la flottabilité, le vol et les points de spawn sûrs doivent être mis au point dans Unreal Editor.
- `vehicles.xml` appartient encore au prototype JavaScript ; l'importation automatique de ce format dans le GameMode UE5 n'est **pas** implémentée. Ne pas considérer les deux fichiers comme interchangeables.
- Les contrôles automatisés GitHub inspectent le code source ; ils ne remplacent pas la compilation et les tests Unreal Engine sur Windows.

## Lot supplémentaire — survie paramétrable par serveur (19 octobre 2026)

- Le fichier `Saved/Servers/<id>/config.json` accepte maintenant une section `survival` : `hungerDrainPerSecond`, `thirstDrainPerSecond`, `starvationDamagePerSecond`.
- Les valeurs sont bornées entre 0 et 10, avec conservation des valeurs historiques si la section est absente. Les propriétés inconnues sont conservées lors d'un enregistrement : pas de fusion destructrice.
- `AAnomaliaSurvivor::Tick` lit les règles du `AAnomaliaGameMode` **côté serveur uniquement** et réplique la faim, la soif et la santé aux joueurs. Deux serveurs avec des identifiants différents peuvent donc appliquer des règles de survie distinctes.
- Le modèle est dans `Config/Anomalia/config.json`. Ne pas modifier les fichiers d'un autre serveur ni effacer les sauvegardes existantes.
- Les tests GitHub vérifient statiquement ce raccordement ; **aucune compilation UE5 native ni test de partie multijoueur n'a été exécuté ici**.

### Exemple de réglage par serveur

```json
{
  "survival": {
    "hungerDrainPerSecond": 0.015,
    "thirstDrainPerSecond": 0.025,
    "starvationDamagePerSecond": 0.25
  }
}
```

Ajouter cette section au `config.json` du serveur concerné, sans supprimer les autres clés.

## Cibles graphiques et consoles — PS5 / Xbox Series X (19 octobre 2026)

**Objectif de production, pas certification :** image de sortie 3840 × 2160 à 60 FPS, avec rendu interne dynamique, reconstruction TSR et géométrie Nanite. La sortie 4K n'implique **pas** 4K natif à chaque image. Les scènes complexes (villes, végétation dense, hordes, dinosaures, véhicules, constructions et multijoueur) nécessitent du profilage pour tenir le budget de **16,67 ms/image**.

- `Config/DefaultEngine.ini` active Nanite, Lumen, Virtual Shadow Maps, TSR et configure un budget de résolution dynamique de 16,67 ms avec bornes de 50 à 100 %.
- `Config/DefaultGameUserSettings.ini` définit des réglages initiaux évolutifs, une limite de 60 FPS et la résolution dynamique ; les joueurs PC pourront personnaliser leurs réglages sans modifier ceux des serveurs.
- `Config/Anomalia/PerformanceTargets.ini` conserve des **objectifs** distincts PC, PS5, Xbox Series X et un profil de repli. Ce fichier est une **spécification de réglages** : il n'est pas encore chargé automatiquement par le runtime, ni certifié sur console. Les valeurs seront affinées sur matériel réel.

**Ce qu'il reste à faire pour publier sur console :** obtenir les accès développeur officiels PlayStation et Xbox, les SDK/versions UE5 compatibles et les kits de développement ; adapter contrôles manette, comptes, invitations, réseau, sauvegardes, restrictions de mémoire et stockage, performances et certification des plateformes. Le code C++ actuel ne constitue pas un build PS5/Xbox. Les SDK propriétaires ne sont ni inclus ni redistribués dans ce dépôt public.

**Mesure obligatoire avant d'annoncer 4K/60 :** compiler dans Unreal Engine 5, charger la carte World Partition finale et tester sur kits PS5 et Series X avec `stat unit`, `stat gpu`, Unreal Insights, profilage mémoire et tests multijoueurs chargés. Ajuster Nanite/Lumen/TSR, densité de végétation, IA et distance d'affichage jusqu'à atteindre 60 FPS de façon stable, ou réduire les objectifs si nécessaire.

### Sélection des réglages depuis l'interface du jeu

Le nouveau `UAnomaliaPerformanceLibrary` expose `GetGraphicsPresets` et `ApplyGraphicsPreset` aux Blueprints. Il lit les sections `[Anomalia.*]` de `Config/DefaultGame.ini` (config standard embarquée dans les builds), puis applique localement les niveaux de qualité, l'échelle de rendu, la résolution dynamique et la limite de 60 FPS. Les préférences sont enregistrées dans `GameUserSettings.ini` **du joueur uniquement**, sans écrire dans `Saved/Servers/<id>`. La fenêtre de paramètres UMG et les contrôles manette restent à réaliser. Les profils PS5/Series X sont des points de départ, non des optimisations validées.

## Lot 1 — compilation native reproductible (19 octobre 2026)

Le pilote `scripts/ue5/validate-build.py` appelle le vrai script UnrealBuildTool
fourni par l'installation UE5 pour les cibles **Editor puis Game**, en Development.
Il s'arrête au premier échec et conserve les sorties du compilateur ainsi qu'un
rapport JSON dans `unreal/Saved/BuildValidation`. Il n'efface ni configurations,
ni sauvegardes. Une compilation réussie ne valide pas le lancement du jeu :
`execution` reste `not_run` et `worldPlayable` reste `not_verified`.

Depuis la racine du dépôt sur Windows :

```powershell
python scripts/ue5/validate-build.py --engine-root "C:\Program Files\Epic Games\UE_5.6"
```

Le chemin est un exemple : utiliser la véritable installation UE5 et ses outils
C++ compatibles. Le workflow manuel **UE5 native build (engine host required)**
utilise un runner Windows portant le label `anomalia-ue5`, avec `UE_ROOT` défini
sur cette machine et Python disponible. Ce workflow ne provisionne pas Unreal
Engine et n'a pas encore été exécuté sur un tel hôte. Il n'est pas déclenché par
les contributions publiques.

**Constat de cette session :** aucun exécutable Unreal Editor ni installation
UE5 détecté dans l'environnement de travail. Le précontrôle a échoué avec le
code 2 ; aucune compilation native ni exécution réelle n'a donc eu lieu.
Les contrôles Python sont distincts de cette preuve manquante. Le projet utilise
encore `/Engine/Maps/Entry` et ne contient pas de carte de jeu `.umap`.
Le lot 1 reste **bloqué**, les lots suivants ne sont pas déclarés terminés.

### Tests natifs après compilation

`--run-tests` lance Unreal Editor en mode automatisé sans rendu (`NullRHI`),
puis exige un rapport neuf avec les deux tests `Anomalia.Native.VehicleCatalog`
et `Anomalia.Native.ProfileIsolation` réussis. Un simple code de sortie zéro,
un rapport absent ou des tests manquants entraînent un échec. Le processus est
limité à quinze minutes. Le workflow natif utilise désormais cette option.

Ces tests exécutent le catalogue C++ et les API réelles de sauvegarde : aller-retour
d'un profil avec champs inconnus, refus d'accès depuis un autre serveur, refus
 de traversée de répertoires et conservation de l'original après écriture invalide.
Les données de test utilisent des identifiants GUID distincts, conservés sous
`Saved/Servers/automation-*` ; aucun profil existant n'est effacé.

**État :** tests natifs ajoutés, pas encore compilés ni exécutés sous Unreal.
Les cinq tests Python du pilote vérifient son comportement par simulation et ne
constituent pas une preuve de compilation. Le lancement d'Editor sans rendu
ne valide ni la carte, ni les graphismes, ni une partie jouable.

Référence Epic : https://dev.epicgames.com/documentation/unreal-engine/run-automation-tests-in-unreal-engine


## Lot 2 — source topographique vérifié, import UE encore requis

`scripts/ue5/generate-terrain.py` génère 144 heightmaps RAW 16 bits, tuiles
contiguës 4 × 4 km avec bord partagé, échantillonnées à environ 3,97 m. Le calcul
à 25 m de résolution estime **354,687 km² au-dessus du niveau de la mer** sur une emprise
de 48 × 48 km (2 304 km² mer comprise). Trois tests vérifient la superficie,
l’encodage et la continuité exacte des bords. Commande :

```sh
python scripts/ue5/generate-terrain.py unreal/TerrainSource
```

Les fichiers sont une **source de heightmaps**, pas des niveaux `.umap`. Leur
import, la création des paysages World Partition, des matériaux, des collisions,
des routes, du point d’apparition et le parcours dans Unreal Editor restent à
effectuer et tester sur une installation UE5. La superficie est estimée par
échantillonnage du champ de hauteur avec le niveau marin fixé à 0 m, pas mesurée
sur un paysage Unreal final.

Pour l’import manuel dans UE5 : générer le dossier, créer un nouveau niveau vide
avec World Partition, passer en mode Landscape > Import from File et sélectionner
`height_x0_y0.r16`. Régler l’échelle de paysage à environ X/Y `396.8254` et Z
`200`, vérifier l’assemblage des 144 tuiles, l’orientation nord/sud et le niveau
de la mer, puis enregistrer sous `/Game/Maps/AnomaliaWorld`. Cette opération
reste à effectuer dans l’éditeur ; elle n’est pas exécutée par le générateur.
