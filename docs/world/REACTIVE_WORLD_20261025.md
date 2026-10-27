# ANOMALIA — monde réactif, état du chantier au 25 octobre 2026

Branche : `ue5/reactive-world-expeditions-20261025`.
Base conservée : `ue5/driveable-roster-city-20261023`.
PR : https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/pull/38

## Ce qui est écrit dans le runtime C++

| Système | Réalisation | Limite de validation |
| --- | --- | --- |
| Monde persistant | `UAnomaliaWorldStateSubsystem`, état versionné par serveur **et carte**, identifiants stables, refus des versions futures/corrompues | Reprise du processus vérifiée par test natif ; aucune garantie matérielle de coupure disque |
| Réparation | Dépôts partiels plafonnés au coût restant ; recette par défaut **100 `metal_sheet` + 50 `plank`**, délai et étapes de mesh configurables ; Destroyed/Repairing/Repaired/Disabled | Pas encore de pont de production placé avec ses modèles endommagé/réparé et ses animations |
| Inventaire/monde | Un journal contient le résultat du monde et le profil après consommation ; l'inventaire reste verrouillé jusqu'à publication durable du profil ; reprise idempotente au démarrage | Tests de dépôts simultanés entre clients réels encore requis |
| Électricité | Graphe de câbles explicites, portée par défaut 3 000 cm, génération à carburant, consommation, coupure de surcharge ; lampe native et porte existante raccordables | Solaire, éolien, batteries, fusibles, disjoncteurs et appareils industriels spécialisés non réalisés |
| Carte d'accès | Vérification dans l'inventaire, consommation optionnelle, état déverrouillé persistant, porte verrouillée en absence d'alimentation requise | Parcours réel avec cartes valides/invalides et déconnexion à tester |
| Portail | Activation consomme les composants définis, événement actif obligatoire, fenêtre UTC, destination choisie par l'auteur, téléportation Unreal avec contrôle d'encombrement | Pas de destination dimensionnelle de production, de VFX ni de tenue de protection ORACLE |
| Événement | Événement serveur temporisé sauvegardé, projection répliquée sur les acteurs | Pas encore d'effets météo ni d'intégration au climat visuel |
| Loot par POI | `allowedPOIs` sur les objets et `poiId` sur les points, filtrage dans le vrai générateur et à la collecte, retrait des anciens pickups devenus interdits | Les POI de production et les crafts avancés restent à éditer et placer |
| Noms et panneaux | 36 noms originaux stables pour les emplacements `settlement_r_c` ; noms de bases/ports par ID ; acteur natif recto/verso et modèle 3D original détaillé générable | Placement mondial, orientation lisible et toutes les bases/ports réels à valider |

Les positions, IDs et géométries existants ne sont pas remplacés par cette branche.
Aucun modèle Bohemia, carte DayZ ou asset sans licence n'est copié.

## Édition Unreal

Créer des `UAnomaliaWorldDefinition` dans le navigateur de contenu, puis placer des
`AAnomaliaWorldMechanism` avec un `StableId` unique. Choisir `Kind`, coûts, meshes
licenciés des étapes et mesh final. Les collisions proviennent réellement des
meshes. La navigation dynamique doit être configurée dans la carte et vérifiée
avec une IA et un véhicule : elle n'est pas revendiquée comme validée.

Renseigner `ConnectedNodeIds` pour les câbles. Deux objets proches mais sans lien
n'ont aucune connexion électrique. Un nœud déchargé par World Partition interrompt
les connexions qui le traversent ; son état n'est pas effacé. La consommation des
générateurs déchargés est suspendue. Il reste à mettre en place la simulation
électrique hors cellule pour les grands réseaux mondiaux.

Le serveur choisit la cible avec le rayon d'interaction existant du survivant ;
il contrôle ensuite propriétaire du personnage, état vivant/éveillé, portée,
visibilité, coût d'inventaire et disponibilité du journal. Les clients ne peuvent
pas envoyer un compte de matériaux ou une identité de joueur arbitraires.

Les champs sont exposés à Unreal/Blueprints. Le panneau spécialisé d'ANOMALIA
Editor Electron/PWA n'est **pas** implémenté dans cette tranche.

### Règle de ressource par POI

Dans un catalogue de loot côté serveur, ajouter par exemple à une définition :

```json
"allowedPOIs": ["quarry-east", "quarry-west"]
```

Sur chacun des points autorisés dans `loot_spawns.json`, renseigner son
`"poiId": "quarry-east"` (ou l'alternative). Sans `allowedPOIs`, l'objet conserve
ses règles existantes. Une liste explicitement vide ou invalide est refusée. Les
quantités, durées et catégories continuent d'utiliser le système natif existant.
Prévoir au moins deux routes d'approvisionnement et des alternatives de craft
pour les ressources de progression. Cette option ne crée pas de géographie.

### Panneaux originaux

`scripts/world-features/build-place-sign.py` construit un GLB original déterministe
à l'échelle métrique : plaque arrondie, faces émaillées, bordure rouge, poteaux,
pieds et fixations métalliques. Il n'utilise aucune œuvre téléchargée.

`unreal/Scripts/place_named_signs.py` peut ensuite importer cet asset et ajouter les
panneaux aux entrées des localités issues du plan de population validé. Il refuse
les identités en conflit et les espaces d'import non possédés, conserve les panneaux
existants et rejette les points sans terrain chargé correspondant ou trop proches
des bâtiments. Première exécution réelle : **46 panneaux enregistrés pour 26 localités** sur
`ANOMALIA_Inhabited_v2`, avec 8 entrées refusées pour absence de sol sec compatible.
Le second passage cherche des alternatives dans les couloirs de la même localité,
puis près de ses parcelles réellement bâties. **Le second passage a enregistré
54 panneaux pour les 27 localités, sans rejet** (run `40176065521`). Preuves :
`docs/world/named-signs-40174606857.json` puis
`docs/world/named-signs-40176065521.json`. Le rendu graphique reste à contrôler.
Les noms des bases et ports sont configurables avec les mêmes acteurs ; aucun
placement militaire ou portuaire inexistant n'est annoncé comme achevé.

## Tests et preuves

- Suite locale : `python -m unittest discover -s tests -p 'test_ue5_*.py'`.
- Tests natifs ajoutés : `Anomalia.Native.ReactiveWorldPersistenceAndPower` et
  `Anomalia.Native.POIResourceExclusivity`.
- Workflow Windows isolé : `.github/workflows/ue5-reactive-world.yml`, compilations
  Editor et Game UE5.8.3, suite `Anomalia.Native.*`, artefacts d'évidence.
- Preuve du commit `c10abd2b770894bbe49db21eb0148e57a7cd5f0f` :
  [exécution 40173632649](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40173632649),
  Editor et Game **compilés sous UE5.8.3**, **22 tests natifs réussis**, dont
  `ReactiveWorldPersistenceAndPower` sans erreur ni avertissement.
- Preuve du commit `f512684ccd69c8d684062a56526c8bb68023bc02` :
  [exécution 40174606857](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40174606857),
  Editor et Game compilés ; **23 tests natifs réussis**, y compris
  `POIResourceExclusivity` et la stabilité de l'identité des cartes entre sessions
  PIE. Le placement des panneaux se déroule après cette validation native.
- Suite locale : **124 tests réussis** (ces tests Python ne sont pas des playtests).
- Les premières compilations ont identifié des erreurs d'en-têtes, de réplication
  de dictionnaires et d'API : corrigées, aucune réussite native inventée.
- Ce workflow ne copie pas une build non validée dans le jeu installé et ne publie
  pas une release automatique.

Validation encore obligatoire : deux clients déposant ensemble, panne/reprise
pendant transaction, traversée du pont par véhicule/IA, carte consommée/invalide,
fin de tempête, déconnexion au portail, rechargement réel de cellule, captures GPU
et parcours complet dans la vraie carte. Les tests natifs de règles ne remplacent
pas ces essais.

## P1/P2 restant explicitement incomplets

- **Projet ORACLE** : documents, sous-marin, carte, composants, fabrication complète
  de combinaison avec oxygène/batterie/intégrité, réacteur, installation profonde,
  dimension, créatures, indices, dangers et retours.
- **Archipel PRIMEVAL** : réparation moteur/coque/carburant du bateau, expédition,
  ventilation/toxicité du bunker, codes multiples, IA/animations dinosaures, coffres
  et contrôle de zone configurables.
- **Cryptes d'ANOMALIA** : fragments, énigmes, temple, leviers coopératifs et solution
  solo, pièges, plateformes, récompenses idempotentes et journaux individuels.
- Déploiement cartographique complet, modes PvE/PvP/RP, outils d'édition autonomes,
  profils de progression individuels et tests multi-utilisateurs.

## Véhicules et maisons : travaux conservés

- Bâtiments détaillés et véhicule de revue : PR #31,
  `ue5/realistic-interactive-assets-20261024`.
- Conduite Chaos : PR #37, `ue5/chaos-road-driving-20261025`.
- Cette PR n'absorbe pas ces branches non validées, ne remplace pas les maisons
  existantes et ne présente pas un modèle de revue comme véhicule réaliste fini.
  Habitacles, portières, animations, conduite et intérieurs visitables restent à
  valider dans leurs parcours Unreal respectifs.

### Contrôle des vrais modèles poursuivi le 25 octobre

Les trois captures Unreal de la PR #31 ont été téléchargées et inspectées : maison
bois à étage/balcon, abri de jardin détaillé avec panneaux solaires, voiture sportive.
Ce sont de vrais modèles importés. Le rendu présente encore des hautes lumières
brûlées et un fond de revue noir ; la voiture est trop sombre pour valider son
habitacle. L'abri inclut son propre jardin sur dalle et ne convient pas à un
remplacement générique de toutes les maisons. La longueur déclarée de la voiture
(623,3 cm) exige aussi une revue d'échelle. Aucun test d'entrée, d'animation de
porte ou de navigation intérieure n'est déduit de ces images.

La PR #37 compile, mais son essai de conduite réel échoue encore sur le contact
roue/sol (0 contact dans les mesures). Elle n'est donc pas présentée comme conduite
Chaos validée. Détails et empreintes des captures :
`docs/art/native-assets-visual-review-20261025.json`.

## Écart avec le jeu installé : diagnostic et correction en cours

Le contrôle en lecture seule du PC (run `40176065521`) observe le jeu et son
raccourci actifs sur le commit `656489fff4c2c833058073f23f1ef5e1418007cc`.
Le jeu ouvert utilise bien cette ancienne version ; aucune mise à jour installée
n'est déduite de la seule compilation d'une branche.

La dernière chaîne de production (`40131567570`, commit `250a9b7`) s'est arrêtée
avant le cook sur le contrôle du menu. Installation de l'exécutable et copie du
projet Editor ont été sautées. Le nouvel essai réel (`40176065521`) a passé le
parcours du menu WorkForge et les interactions dans le renderer du jeu Editor.

La correction de chaîne :

- Contrôle géométrique avant import distinct du contrôle des nouveaux assets.
- Import du vrai catalogue 3D avant son utilisation dans la scène jouable.
- Retour explicite à la page Survivant par le bouton réel avant de tester Mods,
  Options et les retours ; diagnostics précis si un contrôle manque.
- 24 rochers et 24 anciennes sphères de buissons remplacés par les modèles CC0
  vérifiés `rock_moss_set_01` et `grass_medium_01`, avec textures et échelle métrique.
- 12 collines sphériques de fond conservées dans les sources mais masquées.
- Ces nouveaux éléments doivent être vérifiés par l'exécutable cuisiné **et** par
  sa copie installée avant activation de la nouvelle version.
- L'aperçu Editor validé peut se synchroniser indépendamment d'un échec du paquet
  Windows ; chacun conserve ses propres preuves d'installation.

Une publication dédiée `[pc-update]`, commit
`12477c96cc9cf6d57ff9b90a14fedabb175eee1c`, a lancé le run `40176847036` pour mettre
à jour l'installation existante après validation. L'étape d'installation Windows a **réussi** : la copie installée a passé ses
essais et le raccourci/version active ont été relus sur ce commit. L'aperçu
Editor a également été installé et rouvert avec vérification GPU (`COPIED_EDITOR_PROJECT_GPU_VERIFIED`). Aucun téléchargement
manuel demandé à l'utilisateur. Une fenêtre de l'ancienne version doit être
fermée puis le raccourci relancé pour utiliser la nouvelle version.

Limite de contenu toujours explicite : l'exécutable livré ouvre actuellement la
petite zone `ANOMALIA_Playable_v1`. La grande carte `ANOMALIA_Inhabited_v2` est
configurée dans l'aperçu Editor ; elle n'est pas encore livrée en jeu complet avec
le loot et les expéditions. Les photos de la PR #31 ne prouvent pas leur présence
sur cette petite carte jouable.

### Résultat d'installation vérifié

Run `40176847036` entièrement **réussi**. Le jeu installé est passé de `656489f…`
à **`12477c9…`**. La version active et le raccourci ont été relus ; les 54 fichiers
existants de données du jeu et les 5 928 fichiers serveur de l'aperçu Editor ont
été conservés. Le nouvel exécutable installé a vérifié WorkForge, les contrôles,
le ramassage, l'inventaire, les sauvegardes et trois véhicules. Les 24 rochers et
24 végétations au sol réels ont été constatés par le jeu installé, en plus des
20 arbres et deux maisons scannées déjà prévus par cette zone.

La copie de la grande carte dans l'aperçu installé a également passé l'ouverture
native et la vérification GPU. Preuve filtrée et empreinte d'archive :
`docs/world/installed-update-40176847036.json`.

**La refonte graphique n'est pas terminée.** La capture du jeu réellement installé
montre notamment un décalage apparent entre les roues du camion et la chaussée.
La physique actuelle et certains modèles restent provisoires ; la PR Chaos #37
n'a pas encore validé le contact roue/sol. Aucune qualité « 16K photoréaliste »
n'est déduite de ces tests de fonctionnement.
