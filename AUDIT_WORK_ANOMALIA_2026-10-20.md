# ANOMALIA — audit de reprise technique

Dernière mise à jour : 21 octobre 2026, Europe/Paris. Ce fichier décrit les preuves disponibles,
pas un pourcentage de réalisation. Les anciennes preuves JSON et les anciens modèles
sont conservés. **Le jeu complet n'est pas terminé.**

## Où reprendre

- Dépôt : https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN
- Branche active : `ue5/integrate-world-homestead-20261020`.
- PR d'intégration : https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/pull/4
- Pas de fusion vers main autorisée avant validation. Aucun force-push.
- Projet : `unreal/AnomaliaPrimeval.uproject`.
- Carte réelle : `/Game/Maps/ANOMALIA_Archipelago_v2`.
- Rapport détaillé historique : `docs/world/ARCHIPELAGO_PROGRESS_2026-10-20.md`.
- Dernier lot natif terminé : `cca28b25431eba5093e064957f56e4724f32c13f`.
- Exécution : https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/39576659556
- Compilation Editor/Game, tests natifs et traversée PIE : réussis.
- **Relief désormais visible dans une vraie session GPU DX11/SM5 : cinq images inspectées.**
- Correctif : forcer la fusion des couches existantes avec le GPU après leur import
  initial NullRHI. Aucun réimport, niveau remplacé ou sauvegarde supprimée.
- Preuves et images : `docs/world/render-reviewed-39576659556.json` et
  `docs/world/captures/2026-10-21/`.
- Limites : couleurs de biomes provisoires, mer visuelle, végétation absente ;
  sauvegarde des sorties GPU et réouverture indépendante encore non testées.
- **Priorité suivante : pérenniser puis recharger le rendu corrigé avec sauvegarde
  préalable, améliorer matériaux/texture/végétation, puis démo Windows testée.**


La réconciliation complète de toutes les branches et de toutes les autres PR n'est
pas déclarée achevée. Conserver leurs développements ; ne pas réécrire main ni
remplacer une branche existante par ce seul lot de travail.

## Environnement réel disponible

Le runner GitHub **ANOMALIA-PC**, Windows X64, label `anomalia-ue5`, exécute réellement
Unreal Engine **5.8.3**, installé dans `C:/Program Files/Epic Games/UE_5.8`.
Le workflow `.github/workflows/ue5-native-build.yml` compile Editor et Game, lance
trois tests natifs, importe les ressources et lance une vraie session Play In Editor.

Chemin du projet sur le runner :
`C:/Users/utilisateur/actions-runner/_work/ANOMALIA-PRIMEVAL-OUTBOUNDUN/ANOMALIA-PRIMEVAL-OUTBOUNDUN/unreal/AnomaliaPrimeval.uproject`.

Le runner est sur le PC du propriétaire, pas sur une machine distante indépendante.
Il doit rester allumé, connecté et le runner lancé. Aucun hébergement de compilation
permanent indépendant du PC n'est validé. La connexion Epic/GitHub ne prouve pas à
elle seule qu'une telle machine existe. Ne pas facturer ou créer d'abonnement.

La machine de travail de l'assistant ne contient pas Unreal : ses tests Python/C++
isolés ne remplacent jamais les résultats natifs du runner Windows.

## États et portée des preuves

`ABSENT` : absent du port UE5 concerné. `SOURCE ONLY` : code non validé nativement.
`COMPILES` : source comprise dans une compilation native réussie, gameplay non prouvé.
`TESTED IN EDITOR` : fonctionnement précis vérifié en PIE. `TESTED MULTIPLAYER` :
plusieurs clients réels validés. `PACKAGED AND TESTED` : distribution testée.
`BLOCKED` : échec ou ressource manquante documenté.

Les tests de gameplay actuels utilisent **NullRHI**, donc sans rendu GPU. Les
captures sont exécutées séparément avec un vrai GPU DX11/SM5 ; leurs pixels
doivent être inspectés. Aucun FPS, 4K/60, conduite réseau ou jeu complet ne se
déduit du succès des tests de gameplay.

| Fonction | État au dernier contrôle | Preuve et limite | Reste à faire |
|---|---|---|---|
| Projet C++, Editor et Game UE5.8.3 | COMPILES | Plusieurs compilations natives réussies, notamment run 39485038140 | Maintenir les builds après chaque lot ; packaging distinct |
| Carte 48 × 48 km | TESTED IN EDITOR | Vrai .umap et Landscape : 576 composants, 576 collisions, 144 proxies + Landscape principal ; PIE réel | Continuer les régions et leur contenu, navigation/HLOD et mesures de performance |
| Terres et relief | TESTED IN EDITOR, portée limitée | Environ 890,634 km² de terres mesurés sur le générateur à pas 25 m ; 8 masses >1 km² à l'import, sommet 1757,97 m ; collision testée localement | Vérifier toutes les régions ; pas une inspection visuelle exhaustive de 2304 km² |
| Biomes et océan | COMPILES / création native réussie | Matériau de biomes et plan marin visuel sans collision | Vrais matériaux PBR, eau/vagues, nage et flottabilité, fonds marins aménagés |
| Végétation 3D, météo, rendu réaliste | ABSENT du niveau pour la végétation et météo complète | Réglages Lumen/Nanite/TSR présents ; ils ne prouvent pas le rendu demandé | Ressources détaillées, animations, cycles/météo, rendu GPU et profils mesurés |
| Personnage et déplacement | TESTED IN EDITOR, base | Personnage natif possédé, au sol sur Landscape et déplacement réel | Personnalisation, animations, nage/plongée, commandes complètes |
| Inventaire | TESTED IN EDITOR, opération limitée | Composant présent sur personnage ; ajout/retrait d'un bandage sur acteur transitoire isolé | UI complète, équipements/vêtements/sacs, interactions et persistance réelle après reconnexion |
| Santé, faim, soif, endurance, fatigue, sommeil, température | COMPILES pour les classes incluses | Bases dans Survivor/Vitals/Homestead ; pas de validation de tous les états de survie | Tests des transitions, maladies/blessures/soins, cuisine/pêche/chasse/fabrication |
| Pont du Détroit 2,5 km | TESTED IN EDITOR | Modèle original, 50 travées, 102 piles ; marche continue **2450,3 m** et 50 travées en ordre, run 39485038140 | Rendu, traversée en véhicule et multijoueur |
| Deux routes d'accès de 500 m | TESTED IN EDITOR | Correctifs de géométrie et de persistance appliqués ; **3490,4 m** de marche continue, routes et 50 travées, run 39490454207 | Rendu graphique, conduite et multijoueur restent à valider |
| Réseau routier global, chemins et randonnée | ABSENT du niveau hors approches ci-dessus | Pas de réseau de circulation complet intégré | Trajets adaptés au terrain, carrefours, signalisation, collisions/navigation |
| Villes/villages et bâtiments RP | ABSENT du niveau archipel | Des systèmes/ressources JS existent ; leur présence ne vaut pas port UE5 | Maisons accessibles et meublables, commerces, hôpitaux, police/gendarmerie, pompiers, garages, églises/cimetières |
| Ports, bases militaires, aéroports/pistes | ABSENT du niveau | Aucune validation native de ces infrastructures dans ce lot | Modèles, accès, collisions, circulation et interactions |
| Construction et ameublement | COMPILES pour la base Homestead | Base native distincte d'une construction libre complète ; autres branches/PR à réconcilier | Placement 3D, propriété serveur, escaliers/portes/mobilier et armoires ordinaires/pharmacie/armes, undo/redo, sauvegarde/redémarrage |
| Agriculture et élevage | COMPILES pour les bases Homestead | Aucun cycle complet de ferme/animaux validé dans le niveau | Champs, croissance, récolte, saisons, animaux animés, production/reproduction, tracteurs |
| Civils/militaires/policiers et IA ennemies | ABSENT du niveau | Aucun lot d'IA native intégré/testé ici | Navigation, perception, comportements, interactions, permissions et sauvegardes |
| Zombies, animaux sauvages, compagnons et dinosaures | ABSENT du niveau | Fonctionnalités JS à conserver et porter | Modèles/licences, animation, IA, combat, apprivoisement, selles/croquettes, reproduction, persistance |
| Véhicules génériques | COMPILES | Catalogue natif 31 entrées et calculs de dynamique testés ; aucun véhicule complet déduit du catalogue | Physiques adaptées, collisions, conduite réelle, sièges, carburant, dégâts/réparation, caméras, stockage et réseau |
| Modèle d'avion de ligne | Import natif réussi, conduite non testée | Véritable modèle importé et lié à la présentation native ; ne correspond pas aux avions militaires demandés | Vol réel, intérieur, passagers, animations et tests en jeu |
| 210 lignes groupées de véhicules précis demandés | ABSENT pour les modèles UE5 correspondants | 156 anciennes + 54 nouvelles demandes conservées ; index `docs/vehicles/requested-models-index.json` | Tous les modèles exacts/variantes et fonctionnalités ; ne pas confondre lignes et nombre de variantes |
| Berline détaillée existante | SOURCE JS disponible, port UE5 à faire | `src/sedan-asset.js`, modèle CC0, 72 meshes et 9 matériaux | Réutiliser sans perdre 71 pièces via un importeur limité à un seul mesh |
| Quad, motoneige, jet-ski, trains, navires, sous-marins, aéronefs, drones | Pas de validation de véhicules complets | Catégories ou prototypes ≠ véhicules utilisables | Intégration des modèles demandés, physique spécifique, conduite/pilotage et persistance |
| Configurations et profils par serveur | COMPILES pour la base | Test natif ProfileIsolation réussi ; ne prouve pas deux serveurs dédiés réels | Adaptateurs explicites XML/JSON/INI, catalogue central des réglages fonctionnels, migrations et restaurations |
| ANOMALIA Editor et administration | Base partielle ; pas de validation d'éditeur complet | Outils sources à conserver ; pas d'équivalent complet VPP/AW/DayZ Editor validé | UI 3D, permissions serveur, import/export, terrain, ressources, annulation/rétablissement |
| Serveurs dédiés, PVE/PVP/RP et 100 joueurs | BLOCKED pour la validation réelle | Aucun test multiclient ni charge 100 joueurs validé | Build serveur, authentification, sessions, réplication, monde persistant, dormance/loot et sécurité |
| CMD Hosting | Intégration native non validée | 15 configurations prévues ne sont pas 15 machines en service | Binaire serveur vérifié, installation/console/fichiers/mods/sauvegardes et tests réels |
| Menu principal, UI UMG, langues, manettes | COMPILES pour les bases d'inventaire/navigateur, menu complet non validé | Tous les boutons et toutes les langues ne sont pas testés | Menu français complet, localisation demandée, paramètres et navigation manette |
| Installateur/mises à jour Windows UE5 | ABSENT comme distribution validée | Le build/installeur Electron ne vaut pas distribution Unreal | Cook/package, install/désinstall, téléchargement intègre/reprise, mises à jour et conservation des données |
| PS5/Xbox/cross-play | ABSENT comme port validé | Aucune certification ni autorisation console déduite du PC | Étude et procédures séparées |

## Échec trouvé et correction en cours

1. `e647a39850ad0ce30e8993c988bc9710dbc1a94e` : pont seul traversé avec succès.
2. `6bb306dd6078f09e49b614992c47082b75d4ebbf`, run **39485506803** : deux approches
   importées, mais test de route complète échoué après attente de collision.
3. `63b12a85c3c55a3dce0d6f033fd884682d95a3df`, run **39488011249** : instrumentation
   native ; blocage à X=1345376 cm, trace 30 m devant touchant le Landscape au lieu
   de la route près du raccord ouest. Ce run est volontairement conservé en échec.
4. `730d7d168b5aef5878bea7bacd2441d70258580b` : corrige le raccord en mélangeant
   l'offset vertical du point de jonction, plutôt qu'en aplatissant la pente du terrain.
   Test de non-régression géométrique local réussi. Nouveau modèle v2 ; anciens modèles,
   acteur GUID et marqueur v1 préservés. Le run **39488623890** a encore échoué :
   la nouvelle référence du composant n'était pas persistée dans la carte.
5. `e990adf53df99dff53a5e2fb3e6112f586d4bc9c`, run **39490454207** : objets
   explicitement marqués modifiés avant sauvegarde ; marqueur `detroit-roads-v3.json`.
   Test PIE réussi : **3490,4 m**, **50 travées**, sans téléportation en cours de route.
   Vitesse du personnage de test uniquement : 25 m/s. Ce succès reste sans rendu GPU.
6. Dans le même run, le vrai rendu **D3D11 SM5** a démarré sur **Intel Iris Xe**,
   CPU **i5-1155G7**, puis a échoué : récursion Python/Slate et
   `DXGI_ERROR_DEVICE_REMOVED / DXGI_ERROR_DRIVER_INTERNAL_ERROR`.
   Le correctif supprime l'attente de chargement réentrante et empêche les captures
   imbriquées. Sa réussite graphique n'est pas encore démontrée.

Rapports conservés dans `docs/world` : `world-pie-39490454207.json`,
`pie-test-results-39490454207.json`, `roads-placed-39490454207.json`,
`real-graphics-39490454207-failed.json`. Artefact original : **12296865190**,
SHA-256 `1daa2b16435bca16dde60291ecf55d4b10e09cf171d09eeda74f6edf2312d89c`.

## Priorité ajoutée — première démo graphique jouable

Conserver intégralement l'archipel de 48 × 48 km, ses huit îles, ses biomes, le pont
et ses routes. Ne créer ni carte de remplacement ni fausses captures.

1. Corriger et vérifier le vrai rendu, avec captures aériennes/enneigées/plage/désert/pont.
2. Réutiliser les textures existantes, configurer eau/ciel/soleil/éclairage et importer
   une végétation 3D représentative. Les modèles préparatoires non publiés ne doivent
   pas être présentés comme intégrés au projet.
3. Mesurer les performances et tester les déplacements avec rendu actif ; proposer
   un mode D3D11/SM5 sans dépendance aux fonctions SM6 avancées. Le démarrage du RHI
   seul ne prouve pas des performances jouables.
4. Produire puis tester un véritable package Windows avec la carte cuite, le personnage,
   les collisions et un véhicule seulement s'il est réellement disponible et testé.
5. Fournir installation/lancement sans import manuel ; préparer la mise à jour automatique
   avec vérification d'intégrité, reprise, conservation des sauvegardes/réglages et retour
   arrière. Aucun installateur UE5 ou canal de mise à jour natif n'est déclaré livré.
6. Vidéo réelle de déplacement si possible. Une séquence synthétique ne vaut pas preuve.

## Ajouts de véhicules du 21 octobre

`docs/vehicles/requested-models-2026-10-21.json` contient **54 lignes groupées** :
7 antiaériens, 10 antichars, 1 antinavire, 6 véhicules/alias civils et utilitaires,
30 lignes BMW par génération (Série 3, Série 5, Série 7, coupés et SUV X).
Les 156 demandes antérieures ne sont pas réécrites. Les familles Jaguar, VBL et
Humvee sont liées aux demandes précédentes ; leurs variantes ne créent pas de
nouveaux véhicules actifs en doublon. Les dates/noms fournis restent non vérifiés.
**210 demandes groupées ne signifient pas 210 modèles importés ou pilotables.**

## Données à préserver impérativement

- Version JS/Electron et toutes les branches existantes.
- `unreal/Saved` du runner : profils/configurations/sauvegardes et marqueurs de migration.
- Marqueurs `detroit-bridge-v1.json`, `detroit-roads-v1.json`, puis `detroit-roads-v2.json`
  sous `unreal/Saved/AnomaliaMigration`.
- Vrai monde généré : `.umap`, `Content/__ExternalActors__`, `__ExternalObjects__`,
  `Anomalia/World/Archipelago_v2` et `Anomalia/Infrastructure` ensemble.
- `checkout` garde `clean: false` : ne jamais nettoyer les sauvegardes ou les cartes
  générées pour « réparer » une compilation.
- Les archives Actions expirent après 90 jours : conserver une copie d'un monde
  personnalisé. Les JSON de preuve copiés dans Git restent disponibles.
- Le projet personnel séparé `ANOMALIA_Relief_Test` n'est pas automatiquement le
  projet du runner contenant cette nouvelle carte.
- Le lanceur `scripts/ue5/open-archipelago-world.cmd` ouvre la carte dans le bon projet.
- Aucun code privé Epic Games n'est copié dans le dépôt public.

## Reprise ordonnée après le lot actuel

1. Vérifier la branche distante avant toute écriture et lire les derniers résultats.
2. Finir le raccord/route et conserver preuves de succès et d'échec, sans assouplir
   les tests pour masquer une collision manquante.
3. Compléter les infrastructures puis une première zone RP accessible avec vrais
   modèles ; ne pas remplacer les bâtiments détaillés par des cubes.
4. Réconcilier les développements construction/ameublement et tester une maison
   complète, sa propriété, son mobilier et le rechargement après redémarrage.
5. Porter progressivement les IA/créatures et les véhicules réellement utilisables,
   en réutilisant les ressources existantes avec leurs licences.
6. Réseau et serveur dédié : au moins deux vrais clients et deux serveurs isolés,
   puis charge et persistance ; enfin CMD Hosting.
7. UI/localisation/commandes, graphismes mesurés, packaging et installateur Windows.

Rapport après chaque lot : MODIFIÉ, TESTS, GITHUB, RESTANT, BLOQUANTS. Aucun
pourcentage global ni déclaration « jeu terminé » sans validations correspondantes.


## Point de reprise du 21 octobre — ajouts de véhicules et captures

Commit `91bfbbfadd3536b4e31152c7c955a6c53368859d` : les 54 nouvelles demandes
(210 lignes groupées au total), leurs relations de familles, les preuves natives
du parcours de 3490,4 m, l'échec graphique et le correctif de réentrance sont
enregistrés dans Git. 62 tests Python UE5 locaux réussis ; les vérifications source
GitHub ont également réussi. Ce résultat ne vaut pas nouvelle compilation native.

Les modèles précis nouvellement demandés restent ABSENT côté UE5 : aucune entrée
de catalogue n'est présentée comme modèle importé, armé, pilotable ou testé.

Les préparations de végétation, packaging, installateur et mise à jour qui ne sont
pas publiées dans cette branche ne constituent pas une livraison. Reprendre leur
développement après vérification de l'arborescence réelle, plutôt que supposer
qu'un travail temporaire est encore disponible. L'archipel généré et les sauvegardes
du propriétaire restent sur le runner et doivent être préservés.


## Reprise du 21 octobre — inspection effective des pixels GPU

Le run [39561443177](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/39561443177),
source `91bfbbf`, a réellement compilé Editor et Game, importé les ressources et
réussi le test PIE de déplacement/collisions/inventaire. Les rapports bruts sont
conservés dans `docs/world/*39561443177*.json`.

Le GPU DX11/SM5 a produit cinq vrais PNG, inspectés visuellement : les vues
montrent du ciel/de l'eau sans les sujets demandés. **Captures refusées pour
valider la démo**. L'ordre positionnel de `unreal.Rotator` est roll,pitch,yaw,
alors que le script lui passait pitch,yaw,roll. Le correctif utilise les noms
explicites et vérifie le vecteur avant de chaque caméra relue dans le viewport.
Un test de régression projette les cinq axes de caméra sur leurs cibles ;
63 tests Python UE5 réussissent. Cela ne valide pas le prochain rendu natif.

Le processus précédent termine avec `3221225477` malgré un journal de fermeture
normal : ne pas masquer cet échec. Le script libère maintenant sa référence de
tâche de capture avant la fermeture et ne demande plus deux mécanismes de sortie.
Cette correction de fermeture reste à vérifier sur le runner.

Preuve téléchargeable : artifact `12329020076`, SHA256
`66164e4455ab2dcd795c4df0cecb47813ca2c6d25bee6a2e7d43c011abcd114f`.
Le workflow relance les contrôles natifs après publication de ce correctif.
Aucune carte, sauvegarde ou implantation existante n'est remplacée.

Priorité suivante : inspecter les nouvelles images et le code de sortie. Puis
matériaux texturés et végétation représentative, tests de rendu/déplacement,
cook Windows et installation testée avant publication d'un canal de mises à jour.
L'installateur, les mises à jour et les modèles précis demandés restent non livrés.


## Résultat GPU du 21 octobre — succès technique, démo toujours refusée

Run **39566307432**, source `2fe49e0` : compilation Editor/Game, tests natifs,
PIE (routes/pont/inventaire) et capture DX11/SM5 réussis. Fermeture normale, code 0.
Les cinq PNG ont été ouverts et inspectés : pont visible sur la cinquième vue,
mais pas de terres visibles. Les quatre autres vues ne démontrent donc ni îles,
ni neige, ni plage, ni désert. `visual-review-39566307432.json` conserve ce refus ;
un workflow vert ne signifie pas une démonstration graphique réussie.

Archive du vrai monde avec routes et pont : artifact **12329748850**,
25 178 528 octets, SHA256
`75377919c7766db26833c6c159789cff9cdde5c0843e487220caff2251f9c9ad`.
Preuves natives : artifact **12329963421**, SHA256
`58ee3df1369e2e3747ed32c188153635aded599aa1356abd79c6687d8e86356d`.
Ces archives Actions expirent ; aucune prétention de binaire Windows distribué.

Le lot de diagnostic suivant conserve les fichiers du monde. Il vérifie les
576 composants Landscape effectivement chargés, enregistre les classes des
descripteurs World Partition et les états masqués des acteurs, puis force leur
visibilité dans la seule session de capture non sauvegardée. Ne pas refaire
le Landscape pour masquer le problème. Résultat natif de ce lot encore attendu.
Le test de régression des cinq caméras est aussi ajouté au workflow de sources.


## Reprise — Landscape chargé mais invisible, 21 octobre

Run **39567669690** : toutes les étapes techniques réussies. Inspection réelle de
la vue montagne : toujours eau/ciel sans montagne. Le rapport complet
`real-graphics-39567669690-terrain-missing.json` confirme 145 proxies et
576 composants chargés ; les acteurs ne sont ni cachés dans l'éditeur ni en jeu.
Les simples overrides de visibilité n'ont pas résolu le problème.

Archive de preuve **12331026725**, SHA256
`7dacd07bd62c4a4a5881c3f84297d8737ffb8ee42546e1bf6728df34e0ee1956`.
Archive du monde **12331215742**, SHA256
`7ef06cad804415a6b2dc2c351b45de73dc627faa4d196a21a3906ebce9d4dfe7`.

Le nouveau code natif, appelé uniquement dans la session graphique de cette carte,
enregistre les dimensions/source des heightmaps, leurs ressources, les bornes et
matériaux des composants, puis recharge les ressources de texture et reconstruit
les instances de matériau/états de rendu. Le rendu traditionnel est explicitement
demandé pour le test SM5. Aucune hauteur, collision, transformation ou sauvegarde
de package n'est remplacée. Hypothèse à tester, **pas de résolution annoncée**.
63 tests Python UE5 locaux réussis ; nouvelle compilation native encore requise.


### Correction de liaison native — run 39574669396

Le premier lot de rafraîchissement (`12d0463`) a échoué à la liaison :
`ULandscapeComponent::SetNaniteActive(bool)` n'est pas exportée par la DLL
Landscape de cette installation UE5.8.3 (LNK2019). L'appel est retiré ;
le profil de capture utilise déjà la commande publique `r.Nanite 0`.
Le compilateur a compilé le reste de la fonction ; seule la nouvelle liaison
et le rendu restent à revalider. Conserver ce run en échec comme preuve.


## Diagnostic de hauteur visuelle et test de fusion GPU

Run **39575114440** (`c855336`) : nouvelle fonction native compilée et exécutée ;
0 heightmap manquante, 576 ressources présentes, acteurs/composants chargés,
visibles et enregistrés. Les 576 bornes restent centrées à **-2048 m**, avec une
extension verticale de 8 m. Texture source 128×128, mip GPU signalé 32×32.
La vue montagne inspectée reste vide de terrain. La simple réinitialisation des
textures/matériaux ne résout donc pas le défaut.

`docs/world/render-resources-39575114440.json` résume les résultats ; rapport
complet dans artifact **12333393990**, SHA256
`5af9f01116411fb2f0429ed985556f3b406a1ea46f9fcceb627f230be98bbedf`.
La compilation et le PIE sont réussis, aucune réussite graphique globale déduite.

Le lot suivant demande `ForceLayersFullUpdate` puis `ForceUpdateLayersContent`
avec le vrai GPU, avant le rafraîchissement. Cela recalcule les sorties des
couches existantes uniquement dans la session de diagnostic : pas d'import,
pas de remplacement du terrain et pas de sauvegarde. Hypothèse de fusion
NullRHI encore à confirmer par la nouvelle compilation et les images.


## Succès du rendu du relief — 21 octobre

Run **39576659556**, source **cca28b2** : compilation native Editor/Game réussie,
tests natifs et traversée PIE réussis, capture GPU/fermeture réussies. Les cinq
PNG ont été inspectés : îles, relief enneigé, sable/zones sèches et rives du pont
sont visibles. La fusion GPU des couches existantes a rétabli les textures de
hauteur et leurs bornes ; **0 composant sur 576** reste centré à -2048 m.
Les textures GPU ont retrouvé leur résolution signalée 128×128.

Preuve brute **12334009161**, SHA256
`2c9f92e77b9cc9fb599cdccb93ec6feef0aa6538a6df857c4ad9e9075792dbb6`.
JPEG de consultation conservés dans Git ; aucune image synthétique.
Les rapports source et les anciens échecs sont conservés.

**Portée exacte** : rendu du relief testé dans la session graphique après
reconstruction, pas une démo graphique terminée. Les matériaux sont encore des
couleurs simples ; plage/désert demandent textures et cadrages plus représentatifs,
pas de végétation intégrée et pas de mesure FPS de gameplay.

Le correctif ne sauvegarde volontairement pas les packages. Avant de prétendre
que le monde distribué est corrigé : sauvegarde préalable des fichiers du monde,
persistance ciblée des sorties GPU calculées, réouverture fraîche sans reconstruction
forcée, nouvelle capture et parcours. L'archive de monde du run ne prouve donc
pas encore ce cycle. Ensuite matériaux et végétation, cook Windows, tests de
lancement/installation et mises à jour préservant les données.


## Lot en validation — persistance du relief et réouverture indépendante

Le lanceur de capture crée désormais un ZIP unique et vérifié des packages du
monde existant (carte, acteurs/objets externes, matériau du monde), avant toute
réparation sauvegardée. Les profils/configurations de `Saved` ne sont pas inclus
ni modifiés. Chaque fichier et l'archive ont un SHA256 ; un ancien backup n'est
jamais remplacé. Les tests utilisent de vraies archives pour vérifier leur
contenu, la conservation des octets après modification et l'exclusion des profils.

Première session GPU : fusion des couches, inspection du relief, cinq captures,
puis sauvegarde limitée aux packages de ce monde et de ses composants Landscape.
Pas de sauvegarde globale des assets sales. Deuxième processus Unreal indépendant :
lecture des ressources sans fusion forcée, contrôle des 576 composants et des
hauteurs, cinq nouvelles captures. Le marqueur de migration n'est écrit qu'après
la réussite des deux processus. Un marqueur antérieur reconnu est conservé ;
les runs suivants passent directement à la vérification de réouverture.

66 tests Python locaux réussis, dont 3 tests réels du backup ZIP. Nouvelle
compilation UE5, écriture et réouverture encore à vérifier : **ne pas annoncer
la persistance validée avant résultat natif et inspection des captures verify**.
Textures et végétation attendent la stabilisation de ce cycle.


## Demande du propriétaire — mises à jour PC sans commandes manuelles

Un nouveau lot prépare une copie **de développement Unreal**, distincte d'un
jeu Windows packagé. Après compilation, PIE et preuve GPU de réouverture réussis,
le workflow copie le projet et ses binaires dans
`%LOCALAPPDATA%/CMD/ANOMALIA-UE5/versions/<commit>`. Copie vers un dossier de
staging unique, contrôles SHA256 des fichiers critiques, ancienne version gardée.
Les dossiers personnels existants comme `C:/ANOMALIA` ne sont pas remplacés.
Les sauvegardes/configurations partagent un dossier stable `userdata/Saved` via
une jonction ; seuls les fichiers manquants de Servers/Config sont importés.

La copie est ouverte dans un nouveau processus Unreal sans rendu pour vérifier
le niveau et la résolution de Saved avant activation atomique. Un raccourci
`ANOMALIA - Unreal` ouvre la version active dans Unreal Editor installé. Ce
n'est pas un exécutable autonome ni l'installateur final du jeu. Les modifications
manuelles d'une ancienne carte ne sont pas fusionnées automatiquement dans une
nouvelle version ; les fichiers de chaque ancienne version restent conservés.

Un raccourci de démarrage utilisateur relance le runner existant à la connexion
Windows. Le bootstrap refuse de créer une deuxième session si ce runner est déjà
présent. Aucun service système, abonnement ou redémarrage forcé. L'ouverture
après redémarrage reste à vérifier sur un véritable redémarrage de Windows.

**Statut actuel : code publié pour validation, installation non encore confirmée.**
Le rapport `pc-editor-update.json` doit prouver l'installation des raccourcis et
`pc-editor-open-probe.json` l'ouverture de la copie. Les futures publications
validées passent par ce workflow quand le PC et le runner sont disponibles.
