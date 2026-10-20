# AUDIT TECHNIQUE & MISSION CHATGPT WORK — ANOMALIA PRIMEVAL OUTBOUNDUN
**Date : 20 octobre 2026**  
**Projet : CMD / ANOMALIA PRIMEVAL OUTBOUNDUN**  
**Priorité : critique — achever la migration réelle vers Unreal Engine 5 sans perdre l'existant**

## 0. Règle principale
Intervenir sur le dépôt réel https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN, pas uniquement rédiger des conseils. Ne supprimer, écraser ou réinitialiser **aucun** fichier, branche, système, monde, configuration, sauvegarde, historique ni fonctionnalité existante. Faire les développements sur une branche de travail, commits traçables et tests. Ne fusionner vers `main` que lorsque les preuves sont réunies. Les dépenses, souscriptions, intégrations de comptes et actions sensibles exigent les validations nécessaires ; ne jamais prétendre les avoir exécutées.

## 1. Références vérifiées (lecture GitHub)
- `main` : **ancienne pré-alpha JavaScript / Three.js / Electron**, maintenue pour préserver la version existante, et fondation Unreal C++.
- Branche UE5 intégrée : `ue5/integrate-world-homestead-20261020` (commit `380468406a58a198118fe6231bb707225b980969`).
- PR d'intégration en brouillon : https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/pull/4
- Branche de reprise : `ue5/homestead-layout-edit-undo-20261020` (créée au-dessus de l'intégration ; aucune modification de gameplay supplémentaire confirmée au moment de cet audit).
- Autres branches spécifiques à NE PAS perdre : `ue5/homestead-farming-rest-editor-20261020`, `ue5/survival-stamina-temperature-20261020`, `ue5/first-world-partition-bootstrap-20261020`, `feature/anomalia-homestead-editor-server-browser-20261020`, `ue5/migration-native-20261019`.
- `unreal/AnomaliaPrimeval.uproject` existe, avec EnhancedInput, ChaosVehiclesPlugin, Water, PCG, PythonScriptPlugin activés.
- GitHub Actions contrôle les sources : https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/39386194420 et https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/39386310493 (succès). **Cela ne constitue pas une compilation Unreal native.**
- Build natif préparé : `.github/workflows/ue5-native-build.yml` — runner Windows **self-hosted** doté d'Unreal Engine requis; aucune compilation native passée n'a été démontrée au cours de cet audit.

## 2. État confirmé et limites
| Domaine | Sources observées | État vérifié |
| --- | --- | --- |
| Ancien jeu | `src/`, `server/`, `desktop/`, `package.json`, workflows | Pré-alpha Three.js/Electron conservée ; pas version UE5 |
| UE5 C++ | `unreal/Source/AnomaliaPrimeval/` | Socle écrit ; compilation et exécution **non démontrées** |
| Survie/persistance | Survivor, Vitals, Inventory, GameMode, ConfigLibrary | Code pour faim, soif, santé, endurance, fatigue, température, inventaire et profil par serveur ; jeux et réseau non validés dans UE |
| Maison/ferme | HomesteadStation, scripts `anomalia-editor-tools.py` | Meubles/ferme représentés par cubes temporaires ; repos, récolte serveur ; outils de placements JSON hors ligne ; **pas d'éditeur 3D utilisable en jeu** |
| Terrain | `scripts/ue5/generate-terrain.py`, `generate-playtest-terrain.py` | Sources heightmap 48 × 48 km, 144 tuiles test et 264 bords vérifiables ; **aucun import Landscape ou .umap jouable confirmé** |
| World Partition | `create-first-world.py`, `create-terrain-draft-level.py` | Scripts pour l'éditeur Unreal ; création native d'un niveau non démontrée |
| Véhicules | VehicleCatalog / VehiclePawn | 27 définitions de catégories (avec tracteur supplémentaire sur branche UE5) et prototype de déplacement ; ni modèles définitifs, ni Chaos complet, ni navigation/vol complets |
| Réseau et modes | ServerBrowserLibrary / GameMode | 5 PVE + 5 PVP + 5 RP = 15 **modèles de serveurs**, non hébergés et non vérifiés en ligne ; règles PVE/PVP/RP partielles |
| Hébergement CMD | Projets séparés | **Pas de serveur de jeu UE5 en ligne et raccordé à CMD Hosting confirmé** |
| Configuration | `unreal/Config/Anomalia/settings-catalog.json` | Certains réglages fonctionnels au niveau du code ; beaucoup partiels ou non implémentés (port, mot de passe, capacité, mode, horloge, etc.) |
| Qualité/packaging | `ue5-source-checks.yml`, `ue5-native-build.yml` | Tests de sources exécutés ; binaire Windows Unreal, signature, console et performance non validés |

**Point de cohérence à trancher avant terrain final :** la version JS documente un monde actif d'environ 20 × 20 km et une cible de module 96 × 96 km, tandis que l'amorce UE5 utilise 48 × 48 km. Ne pas modifier arbitrairement la dimension ; proposer une configuration extensible et confirmer les objectifs de carte à partir du dépôt/cahier des charges.

## 3. Écarts bloquants (ordre de traitement)
### P0 — Preuves de fonctionnement
1. Examiner la PR #4 et les branches sans supprimer l'existant ; consolider uniquement les changements compatibles, résolution raisonnée des conflits.
2. Installer/utiliser **Unreal Engine 5 et toolchain Windows C++** sur une machine/cloud de build approprié **si légalement et matériellement disponible**, sans imposer l'installation sur le PC du propriétaire. Identifier et documenter clairement tout accès, licence, paiement, capacité GPU/stockage ou interaction impossible. Ne pas faire croire qu'un simple GitHub Actions Linux compile UE5.
3. Exécuter réellement `scripts/ue5/validate-build.py` sur le runner natif, corriger les erreurs C++/UBT, produire logs et `unreal/Saved/BuildValidation/report.json`.
4. Générer un **vrai .umap UE5** (FirstTest), lancer Play-in-Editor, tester clavier AZERTY/QWERTY, manette quand disponible, inventaire, caméra, saut, interactions et arrêts/reprises ; enregistrer des preuves.
5. Activer les tests automatisés UE et rejouer après chaque correction importante. Aucune fonctionnalité n'est « terminée » sur simple présence d'un bouton, fichier ou API.

### P1 — Monde, survie, habitation et fabrication
6. Importer et vérifier le paysage (d'abord profil 144 tuiles réduit) en Landscape/World Partition, collisions, hauteur, eau/océan, streaming, position du joueur et budget de performance. Préserver les heightmaps HD.
7. Réaliser véritable éditeur de maison/ferme : inventaire des objets, sélection, placement 3D, rotation, déplacement, suppression avec confirmation, annulation/rétablissement, sauvegarde/rechargement persistant, droits de modification et isolation des mondes par serveur. Démarrer en intégrant les outils JSON existants, sans réécriture destructive.
8. Créer une UI réelle UMG pour construction/ameublement, inventaire, crafting, progression, interaction, alimentation, sommeil et statistiques ; boutons actifs et ergonomie manette.
9. Remplacer **progressivement** les cubes de travail par assets 3D originaux/licenciés avec collisions, animations, LOD/Nanite lorsqu'adapté ; IA des animaux, vaches/poules/ruches et ferme : séparer ce qui est encore à simuler de ce qui est réalisé.
10. Porter sans régression les mécaniques du jeu JS (inventaire/poids/compartiments, récolte, fabrication, bâtiments, ressources, maladies, soin, chasse, faune et créatures, dinosaures, apprivoisement, météo et biomes). Pour chaque mécanique, inventorier l'ancienne implémentation et la nouvelle preuve UE ; ne pas perdre les fonctions existantes.

### P2 — Déplacement, multijoueur, serveurs et réseau
11. Terminer véhicules terrestres (camions, remorques, fourgons, SUV, police/secours, quad, buggy, moto, kart, F1, motoneige, blindés, etc.), maritimes (bateaux, jet-ski, zodiac, navires, sous-marin) et aériens (avions et hélicoptères) ; physique dédiée, sièges, carburant, collisions, possession, sauvegarde, permissions, tests réseau. Une « définition » ne vaut pas modèle jouable.
12. Mettre en place de **vrais serveurs dédiés** et un navigateur avec états en ligne vérifiés ; tester sessions de deux clients puis multi-joueurs, connexion/reconnexion, latence, sécurité RPC, anti-triche, persistance, isolation des serveurs, sauvegardes, permissions et gestion des administrateurs.
13. Configurer réellement les règles de serveur PVE/PVP/RP, mot de passe et accès, profils, slots, réseaux, paramètres temps/météo, logs, console et mise à jour.
14. Préparer le raccordement **CMD Hosting** (agent/machine, état on/off, déploiement de binaire, sauvegardes, paramètres, ports, restauration). Ne déclarer aucun des 15 serveurs « online » tant qu'il n'existe pas une instance fonctionnelle contrôlée.
15. Préparer les formats de mods UE natifs et une documentation développeur ; distinguer le catalogue JSON PC « data-only » du packaging réel. Ne pas promettre publication PS/Xbox/crossplay sans accord, licences, conformité et validations constructeurs.

### P3 — Finition et distribution
16. Environnement HD, textures/matériaux, éclairage Lumen selon matériel, Nanite pour géométrie adaptée, animations, audio, effets et accessibilité ; optimiser plutôt que forcer une fausse « 16K ».
17. Vérifier packaging Windows UE5 propre, signature si disponible, installation, désinstallation, sauvegardes, contrôles, crash reports, mise à jour. Prévoir plans consoles séparés, jamais prétendre leur certification acquise.
18. Tests réels de performance et fiabilité : PC modestes, appareils cibles, plusieurs sessions longues, réseau sous charge, mémoire, disque, menus, manettes, persistance, reprise après plantage.

## 4. Critères de fin obligatoires
Pour chaque fonction, indiquer : `absent`, `source_only`, `compiles`, `tested_in_editor`, `tested_multiplayer`, `packaged_and_tested`, ou `blocked`. Journal avec fichiers modifiés, commits, preuves/logs et prochaine action. Ne jamais déclarer le projet fini à 100 % avant compilation Unreal et validation en conditions réelles.

**Preuves attendues au minimum** : build natif UE5 sans erreur, carte .umap réellement créée et jouée, interface interactive, tests sauvegarde/rechargement/isolation sur deux serveurs, clients multijoueurs connectés, véhicule conduisible testé, livraison PC installable testée. Toute fonctionnalité non testée reste explicitement partielle.

## 5. Politique de sécurité et préservation
- **Ne rien supprimer :** aucune sauvegarde, ancien mod, fichier JS, branche, scène ni données de serveur ; ne jamais faire de reset/force-push/destructive migration.
- Git branches, PRs révisables, commits petits et traçables ; demander validation pour publication/merge risqué.
- Ne pas inventer de résultat de test, disponibilité serveur ou capacité d'hébergement.
- Ne pas exposer de clés API, tokens, identifiants, mots de passe, données utilisateurs ; vérifier la sécurité des RPC, la validité des identifiants et les chemins de sauvegarde.
- Réutiliser ce qui existe et mutualiser les doublons **sans perte de comportement**.
- Respecter les droits sur modèles, musiques, marques, licences et plateformes.
- Privilégier les outils déjà connectés et les options gratuites ; **ne créer aucune dépense ni abonnement sans consentement**.

## 6. Mode de travail demandé pour ChatGPT Work
**Agir, pas refaire seulement l'audit :**
1. Ouvrir le dépôt et comparer `main`, branche intégrée et PR #4.
2. Commencer par les blocages P0 et la **première tranche réalisable** sans installation sur mon PC.
3. Produire et committer des corrections concrètes, lancer tests adaptés, ouvrir/mettre à jour une PR.
4. Si l'environnement n'a pas Unreal Engine, accomplir les correctifs et tests disponibles et identifier précisément l'étape qui exige un runner UE5 réel ; ne pas la simuler ni annoncer de succès.
5. Après chaque lot, réponse **courte** : « modifié », « tests exécutés et résultats », « restant », « bloquants », « lien commit/PR ». Éviter de remplir inutilement la conversation ; permettre de continuer dans une nouvelle conversation avec une référence au dépôt/PR.

**Commencer immédiatement par :** fiabiliser la compilation native et la carte FirstTest, puis terminer l'éditeur d'ameublement (ajout, déplacement, rotation, suppression sûre, annulation/rétablissement, persistance) et ses tests, sans toucher à `main` avant validation.

## 7. Dépendance Epic Games / GitHub — contrôle spécifique

Le propriétaire a transmis `git@github.com:EpicGames/Signup.git`. Ce lien SSH correspond au dépôt public officiel `EpicGames/Signup` (documentation d'accès), **pas** au code source ni à un exécutable UE5. Son README renvoie à la liaison Epic Games ↔ GitHub :
- https://github.com/EpicGames/Signup
- https://www.unrealengine.com/ue4-on-github
- Dépôt source une fois l'accès accordé : https://github.com/EpicGames/UnrealEngine

**Constat vérifié via la connexion GitHub `znationcmd`** : le dépôt `EpicGames/Signup` est lisible, tandis que `EpicGames/UnrealEngine` renvoie `404 NOT_FOUND` au moment du contrôle. Ce 404 ne permet pas de déduire la raison exacte : liaison du compte, invitation non acceptée, permissions ou visibilité du connecteur. Ne jamais présumer que Work dispose du code UE5 avant un nouveau contrôle d'accès autorisé.

**Actions pour Work :**
1. Vérifier les prérequis de compte Epic Games et l'association **du compte GitHub voulu** depuis les paramètres Epic ; laisser l'utilisateur effectuer la connexion, les confirmations et toute acceptation d'invitation, sans demander de mot de passe/token.
2. Re-tester l'accès au dépôt `EpicGames/UnrealEngine` **avec les permissions effectivement disponibles**. En cas de 404, consigner le blocage ; ne pas contourner les permissions.
3. Une fois autorisé, employer une version UE5 compatible et une machine de compilation adaptée ; vérifier espace disque, dépendances, temps de build, licence et GPU. L'accès au dépôt **ne fournit pas automatiquement** une VM, un Windows runner, des crédits cloud ou un jeu compilé.
4. Si le code source Epic n'est pas nécessaire, privilégier l'installation UE5 standard par Epic Games Launcher sur une machine Windows autorisée ; l'utilisateur ne veut pas installer UE5 sur son PC personnel.
5. Garder le build natif en statut `blocked` tant qu'aucune compilation réelle avec rapport n'est prouvée ; continuer pendant ce temps les correctifs hors moteur disponibles.
