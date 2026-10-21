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
- Dernier lot natif exécuté : `e990adf53df99dff53a5e2fb3e6112f586d4bc9c`.
- Exécution : https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/39490454207
- Routes/pont : traversée PIE réussie, **3490,4 m**, 50 travées en ordre.
- Rendu réel : tentative D3D11/SM5 échouée ; zéro capture validée.
- **Priorité de reprise : tester le correctif de réentrance Slate des captures, puis la démo graphique demandée le 21 octobre.**

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

Les tests actuels utilisent **NullRHI**, donc sans rendu GPU. Aucun résultat visuel,
FPS, 4K/60, conduite réseau ou jeu complet n'en découle.

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
