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
puis près de ses parcelles réellement bâties. Le rendu graphique n'est pas encore
contrôlé. Preuve : `docs/world/named-signs-40174606857.json`.
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
