# ANOMALIA — reprise technique du 20 octobre 2026

## Branche de travail et conservation

Branche : `ue5/native-validation-homestead-fixes-20261020`. Base : intégration `3804684`, puis reprise `e6de81a`. Aucune fusion vers `main`. Aucun fichier utilisateur, monde, sauvegarde ou branche supprimé. Aucun force-push, abonnement, machine cloud ou dépense créée.

- Reprise `ue5/homestead-layout-edit-undo-20261020` : descend déjà de l'intégration ; ses trois derniers commits sont documentaires. Le nom de branche ne prouve pas un éditeur 3D avec undo/redo.
- Branche JS `feature/anomalia-homestead-editor-server-browser-20261020` : fusionnée sur la branche de travail. Sept fichiers de gameplay/UI conservés, dont `src/homestead.js`.
- Monde/World Partition : contenu de la branche `ue5/first-world-partition-bootstrap-20261020` déjà présent par intégration ; aucune deuxième copie de carte créée.
- Survie/Vitals : contenu de `ue5/survival-stamina-temperature-20261020` déjà présent.
- Ferme/rest : contenu de `ue5/homestead-farming-rest-editor-20261020` déjà présent.
- Ancienne branche `ue5/migration-native-20261019` : contient une autre définition de `FAnomaliaServerSettings` et de `AAnomaliaGameMode`. Importer aveuglément ses dossiers Public/Private produirait des types dupliqués. La bibliothèque ConfigLibrary active assure déjà chargement/sauvegarde par serveur. La branche ancienne est conservée intégralement et son exporteur distinct est récupéré sous `unreal/Scripts/export_legacy_configs.py`. L'ancien Subsystem et son mécanisme .bak restent historiques, non activés ; leur compatibilité Blueprint et stratégie de sauvegarde demandent encore une réconciliation native.

## Corrections réalisées

1. Pilote UBT : exige UE 5.8 (toutes révisions), enregistre un blocage même si Build.version est invalide, borne les processus et conserve commande, codes de sortie et journaux. Le batch Windows est lancé avec CALL pour les chemins contenant des espaces.
2. Tests UE : retrait du Quit anticipé ; sortie après fin de la file Automation. La liste des tests attendus est découverte dans les inscriptions C++ ; rapport absent, incomplet, mal typé, non réussi ou processus en échec refuse la validation.
3. Option `--create-first-world` : appelle le vrai Unreal Editor après compilation, attend un rapport unique pour cette exécution et exige le vrai fichier .umap. Aucun rapport précédent ne peut être accepté. Cela ne valide pas le gameplay.
4. FirstTest : conserve les cartes existantes, tente de les ouvrir avant de les accepter ; sauvegarde les packages des acteurs World Partition. Le scénario neuf prévoit six acteurs C++ de test (lit, table, chaise, vache, poule, ruche), encore représentés par des cubes. Aucune création native de cette scène n'a été exécutée ici.
5. Ferme/inventaire : conserve les deux identifiants `egg` (sauvage) et `eggs` (ferme). Le poids du lait correspond à la source JS intégrée : 0,5 kg. Les anciens profils ne sont pas réécrits par cette reprise.
6. Test natif catalogue : attend 28 définitions avec le tracteur, contre 27 dans le test périmé. Ce sont des définitions, pas 28 véhicules finis.
7. CI : tests de cycle de connexion ajoutés au workflow source ; workflow natif manuel avec Git LFS et création optionnelle FirstTest. Aucun déclenchement natif sans hôte identifié.

## Tests exécutés et preuves

- `python -m unittest discover -s tests -p 'test_*.py' -q` : **73 tests réussis**. Ils comprennent des contrôles statiques et des tests fonctionnels des outils Python ; ils ne compilent pas Unreal. Les fixtures UBT simulées servent uniquement à tester la détection d'échecs.
- `npm test` : **74 tests réussis**, dont quatre nouveaux tests de repos/production/horloge/persistance JS.
- `npm run build` : compilation Vite réussie de l'ancienne version web ; avertissement de taille du bundle conservé.
- `npm run test:browser` : **ÉCHEC**. Chromium headless se termine par SIGSEGV pendant la première navigation, avant les assertions de jeu. Le diagnostic est conservé dans `2026-10-20-browser-failure.txt`. Pas de réussite navigateur annoncée.
- `python scripts/ue5/validate-build.py --create-first-world --run-tests --output unreal/Saved/BuildValidation/host-preflight-20261020` : **code 2 / BLOCKED**. Rapport réel conservé dans `2026-10-20-native-preflight.json`. Aucun compilateur Unreal lancé ; aucun .umap produit.

## Environnement distant réellement disponible

- Hôte de travail Linux x86_64, environ 9,8 Gio de RAM et 29 Go libres, sans installation UE, UnrealEditor, UnrealBuildTool ni toolchain Windows identifiée.
- Accès `EpicGames/UnrealEngine` via le connecteur : **404**. L'accès du propriétaire est confirmé dans l'audit ; ce contrôle ne remet pas cette confirmation en cause. Aucun code privé Epic récupéré ou copié dans ANOMALIA.
- Consultation GitHub des exécutions `workflow_dispatch` : zéro exécution enregistrée. Cela ne permet pas d'affirmer qu'aucun runner n'est enregistré ; aucun hôte UE 5.8 exploitable n'est confirmé dans les accès actuels.
- Le workflow exige un hôte Windows distant `self-hosted, Windows, X64, anomalia-ue5`, avec UE 5.8, toolchain C++, Python et Git LFS, et `UE_ROOT` configuré. Il n'installe rien sur le PC personnel du propriétaire et ne provisionne pas de service payant.

Commande sur cet hôte distant une fois disponible :

```powershell
python scripts/ue5/validate-build.py --engine-root "$env:UE_ROOT" --create-first-world --run-tests
```

Même en cas de succès, tester ensuite Play-in-Editor, collision/déplacement, inventaire, lit/récolte et reconnexion. Le pilote ne transforme jamais ce succès en `TESTED IN EDITOR` ou `TESTED MULTIPLAYER`.

## États UE5 observés après ce lot

| Système | État | Limite actuelle |
| --- | --- | --- |
| Compilation et packaging natifs | BLOCKED | Moteur et hôte Windows non disponibles |
| Création FirstTest | SOURCE ONLY | Script prêt ; aucune .umap créée ici |
| Terrain 48 x 48 km / 144 tuiles | SOURCE ONLY | Générateurs testés hors moteur ; import Landscape non validé |
| Personnage, inventaire UMG, survie et profils | SOURCE ONLY | Code non compilé, aucune preuve PIE ou réseau UE |
| Lit, ferme et chargement des placements | SOURCE ONLY | Acteurs temporaires, pas de modèles finaux |
| Construction/ameublement 3D avec propriété et undo/redo | ABSENT | Outil JSON hors ligne seulement ; pas d'interface native complète |
| Agriculture saisonnière et IA d'élevage | ABSENT | Prototype de récolte uniquement |
| Véhicules | SOURCE ONLY | 28 définitions et conduite générique, physique finale absente |
| Zombies/dinosaures/IA et animations natifs | ABSENT | Fonctions de la version JS à porter |
| Navigateur de serveurs | SOURCE ONLY | 15 configurations, aucun serveur déclaré hébergé |
| Serveur dédié UE et essais multi-clients | BLOCKED | Pas de binaire serveur ni d'hôte de test confirmé |
| Menu principal/localisation/éditeur UMG complets | ABSENT | Écran d'inventaire natif partiel seulement |
| CMD Hosting / installateur UE Windows | BLOCKED | Dépendent du serveur et du jeu natifs compilés et testés |

Prochain lot : preuve de compilation/FirstTest dès qu'un hôte autorisé existe ; en attendant, développer les transactions de placement et la propriété serveur pour l'ameublement natif, avec conservation des formats JSON existants.

Référence Epic pour l'arrêt Automation : https://dev.epicgames.com/community/learning/courses/Znk/simulating-a-lidar-sensor-using-hardware-raytracing-in-unreal-engine-5/58ELY/simulating-a-lidar-with-hwrt-in-unreal-engine-5-article-8-validation-and-performance
