# Mission de finalisation — preuves P0, 4 novembre 2026

## Périmètre et préservation

Base : `e2f901d8d9857b0fe899dbe515dedf40bcec9d76`, branche demandée `feature/skarvik-citysample-sm5-20261031`.
Travail isolé : `mission/finalisation-20261104`, PR #64.
Aucune modification de D:\ANOMALIA, de PostgreSQL, des sauvegardes, des assets ou des cartes installées. Aucun merge, suppression de branche ou force-push.

## État réellement constaté

- Inventaire réutilisé, run [41794604995](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/41794604995) : 127 .umap, 24 999 packages .uasset/.umap. Un seul projet, AnomaliaPrimeval.uproject.
- Les niveaux identifiés par le filtre SKARVIK/City/Archipelago sont CitySampleVehicles, ANOMALIA_Archipelago_v1 et ANOMALIA_Archipelago_v2. Ce filtre ne constitue pas une inspection des acteurs. Aucun nombre de villes ou de routes praticables n'en est déduit.
- Inspection ciblée [41798193651](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/41798193651), artefact 13306197665 : 25 044 fichiers Content, 145 514 FabImports, 253 Sketchfab ; aucune erreur de parcours. D:\ANOMALIA n'est pas un checkout Git. Le descripteur charge le module AnomaliaPrimeval ; son EngineAssociation est un GUID. Ce GUID seul ne prouve pas la version du moteur.
- Processus au moment de cette inspection : EpicGamesLauncher uniquement parmi les processus ciblés. Aucun Unreal/Robocopy ciblé détecté à cet instant ; ce résultat n'est pas une garantie permanente.
- Modèles installés confirmés par chemin : German Shepherd, SK_Wolf, SK_Fox, SK_DeerStag, SK_DeerDoe, SK_Lion_LOD0 et SK_Lioness_LOD0. Il s'agit de présence de fichiers, pas de chargement, de compatibilité d'animations ou d'IA acceptée.
- Archive circuit existante : D:\ANOMALIA\sketchfab\shanghai-international-circuit-2018-layout.zip, 105 849 006 octets. Les deux fichiers formula_one.uasset sont des candidats véhicule, pas la preuve d'un circuit importé.
- L'inventaire antérieur [41663867323](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/41663867323) est récupéré. Ses correspondances par nom comportent des faux positifs : identifiants World Partition contenant DOG/FOX et noms contenant ape. Ne pas compter ces correspondances comme espèces intégrées.

## Résultats historiques conservés, sans les attribuer à D:

Les rapports versionnés CHARACTER_VALIDATION_RESULTS_20261027.md, DOG_COMPANION_AUDIT_20261028.json et BMW_E39_NATIVE_STATUS.md décrivent des validations sur des copies C: distinctes.

- Survival : run 40656105121, marche 449,98 cm/s, course 679,95 cm/s, accroupissement, saut et opérations d'inventaire par API en PIE. Cela ne valide pas toute l'animation, les entrées physiques ni l'installation D:.
- Berger allemand : rapport historique de 28 tests natifs et 16 contrôles PIE. Follow/Stay et blessures non mortelles ; navigation, persistance et ordres manquants restent à traiter.
- Singe B3 : fichiers et 19 noms de sources d'animation historiquement documentés ; compatibilité, présence actuelle dans le projet principal et compagnon non validés.
- E39 : run 40655809703, 26 tests natifs, 64 contrôles physiques, 313 échantillons sur copie isolée. Freinages 30,87 m à 80,32 km/h sur adhérence 0,9 et 56,87 m à 80,04 km/h sur 0,45. Ces mesures ne sont ni des performances actuelles de D: ni une validation de toute la simulation demandée.
- SKARVIK : les scripts existants ciblent notamment C:\ANOMALIAZ_SKARVIK_STAGE_41188816555 et PRIGIMALIA_SKARVIK_FINAL_v1. Leur code attend des comptes d'acteurs ; ces nombres ne sont pas des résultats réobservés. Ne pas recopier ce stage vers D: sans validation des dépendances et des différences.

## Changements et erreurs de ce lot

- Branche sécurisée et PR brouillon créées.
- Inspection Windows sans checkout ni écriture dans le projet.
- Premier essai d'inspection arrêté par l'absence de Git sur D:. Reprise : rapport complet publié, mais job rouge car le code de sortie Git 128 subsiste dans le wrapper PowerShell. Correction explicite de sortie enregistrée ; pas de nouveau scan automatique inutile.
- Cause de l'échec natif antérieur 41699761070 vérifiée dans le journal : chemins UBT de 261 à 264 caractères, sortie 6, pas de PIE exécuté.
- Nouvelle validation : checkout clairsemé dans un emplacement propre, export du commit exact vers un dossier court et unique C:\ANOMALIA-Validation\m<run>. Aucun projet alternatif conçu ; c'est une copie de compilation des sources existantes.
- Première tentative courte 41798564805 : checkout arrêté par un long chemin d'asset. Correction par checkout clairsemé avant export complet.
- Reprise native [41798670858](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/41798670858) : prévalidation et export réussis, compilation en cours lors de rédaction. Tests natifs non encore acceptés.
- Inspection de l'archive circuit [41798766216](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/41798766216) programmée dans le même groupe exclusif.

## Acceptation fonctionnelle et progression

Aucune carte, animation, espèce, circuit ou physique de véhicule n'a été modifiée ou nouvellement acceptée en jeu par ce lot. Aucun FPS, temps de frame ou budget mémoire en gameplay mesuré.

Les pourcentages globaux de réalisation ne sont pas calculables à ce stade : absence de correspondance vérifiée entre le projet installé, les copies validées et leurs ressources. Leur attribuer arbitrairement un taux serait trompeur. Les compteurs ci-dessous mesurent seulement les nouvelles acceptations de cette mission, pas l'absence du travail historique.

| Domaine | Critère d'acceptation actuel | Résultat |
|---|---|---|
| SKARVIK | 10 groupes de la mission validés sur la carte principale | 0/10 nouvellement acceptés (0 % de couverture nouvelle) |
| Personnage | Scénario complet demandé en première/troisième personne | Non exécuté ; progression globale indéterminée |
| Animaux | Espèces et deux compagnons simultanés testés sur la carte principale | Aucune nouvelle espèce acceptée ; progression globale indéterminée |
| Circuit | Archive identifiée, licence, import, collisions, tour complet | Archive identifiée uniquement ; aucune acceptation de conduite |
| Véhicule | Conduite sur route/circuit et fonctions complètes dans D: | Non exécuté sur D: ; preuves historiques distinctes |
| Validation générale | Compilation + Blueprints + PIE + sauvegardes + performances sur version finale | En cours / non accepté |

## Suite nécessaire

1. Terminer et lire les journaux de compilation ; corriger les erreurs démontrées avant relance.
2. Identifier les écarts exacts de modules/source entre D: et la copie SKARVIK avancée C:, ainsi que les dépendances de la vraie carte.
3. Vérifier l'identité de l'archive circuit, sa licence et son contenu avant toute importation.
4. Valider SKARVIK par chargement World Partition, navigation et parcours ; ne pas confondre nombre de meshes et villes complètes.
5. Compléter les systèmes et tester chaque comportement dans le projet retenu, puis seulement installer les changements validés.

## Preuves SKARVIK antérieures récupérées pendant la compilation

Les artefacts suivants ont été ouverts, sans réexécuter leurs audits :

- [41317643889](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/41317643889), artefact 13087689621 : réouverture du niveau final, 720 composants City Sample des quatre premiers secteurs et 121 du cinquième, soit 841 composants. 12 meshes du cinquième secteur effectivement chargés ; 906 acteurs de bâtiments continentaux et 128 insulaires, soit 1 034. Cela ne prouve ni 841 bâtiments complets, ni des intérieurs explorables.
- [41656792535](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/41656792535), artefact 13239289055 : 663 tronçons régionaux persistés, 6 130 anciens tronçons secs, lots locaux de 1 674 et 1 298. Échantillonnage de 12 acteurs à mesh réel ; reçu de construction régional 2 971,6 mètres. Le rapport déclare explicitement all382RoadsConnected=false, allVillageRoutesComplete=false, SM5Driven=false. Ne pas additionner ces nombres pour annoncer des routes complètes ou uniques.
- [41655148263](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/41655148263), artefact 13238749705 : présence et empreintes des niveaux FINAL, GRADED, ISLANDS et Big_City_LVL dans C:\ANOMALIAZ_SKARVIK_STAGE_41188816555. Des lignes de journaux antérieurs signalent des matériaux City Sample introuvables ; leur résolution actuelle reste à vérifier.

Le travail avancé n'est donc pas à recommencer. Il faut le réconcilier avec le projet installé et vérifier les dépendances, le streaming et les raccordements avant migration.

## Résultats supplémentaires — compilation et circuit

- Run 41798670858 terminé en échec après 736,99 s, UE 5.8.3 confirmé. Les unités C++ sont compilées jusqu'à l'édition des liens Editor ; trois symboles UNavigationSystemV1 sont non résolus (LNK2019/LNK1120). Game et tests non exécutés. Ce résultat remplace l'état provisoire « en cours » ci-dessus.
- Correctif réel [f0f5144c137e1da1f8dc0a5568dd8de9c29db093](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/commit/f0f5144c137e1da1f8dc0a5568dd8de9c29db093) : dépendance privée NavigationSystem ajoutée au module, car le loot projette des positions sur le NavMesh. Aucun remplacement de système ou d'asset.
- Reprise incrémentale [41800675310](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/41800675310) : ancien et nouveau Build.cs contrôlés par blobs Git avant application sur la seule copie de validation ; original conservé. Le stamp compilé 0360ec9 est volontairement conservé pour le cache : le reçu source-patch-receipt.json identifie séparément le correctif f0f5144. Ne pas assimiler le stamp seul aux sources effectives.
- Le chemin logique C:\ANOMALIA-Validation\m41798670858 se résout dans les journaux UBT en D:\ANOMALIAZ\03_Validation\m41798670858. Ce dossier est distinct du projet utilisateur D:\ANOMALIA ; aucune écriture dans celui-ci.
- Run circuit [41798766216](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/41798766216) réussi, artefact 13307337217. Archive d'origine inchangée, SHA256 DFE2640AAC32D469D36CAF076295BBEB4BCDFDB1D903364C559FE121283D33EC.
- L'archive contient source/shanghai_compressed.glb (92 809 048 octets), des textures de tribunes, stands, pit lane, bordures, asphalte et infrastructure. Des noms de textures ne prouvent pas la géométrie ni les collisions. Aucune notice de licence embarquée trouvée par le filtre documenté.
- Fiche candidate retrouvée : https://sketchfab.com/3d-models/shanghai-international-circuit-2018-layout-4d3365f4de6442a5ae56e8807c518c4f, auteur affiché Dave Love SketchFab (@Tyler_Dave), licence annoncée CC Attribution, environ 1,4 M triangles. Lecture directe bloquée HTTP 403 ; ces informations proviennent du résultat indexé. Correspondance exacte de l'archive et droits sur ses éléments toujours à établir avant intégration.
- Inspection complémentaire GLB préparée pour lire uniquement métadonnées, extensions de compression et bornes avec transformations de scène. Pas de réextraction générale, pas de modification du projet, pas d'import déjà revendiqué.

## Cible Editor compilée et reprise sur volume physique

Le run [41800675310](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/41800675310) confirme **Editor compilé avec sortie 0** après le correctif NavigationSystem. La cible Game échoue ensuite avec C1085 / espace insuffisant lors d'écriture du PCH sur D:\ANOMALIAZ\03_Validation. Les tests natifs n'ont pas été lancés dans ce run. Les avertissements InputKey/SetBase/GetMovementBase restent distincts de ce blocage disque.

Le lanceur validate-build.py cherchait aussi l'ancien préfixe Anomalia.Native alors que les tests C++ sont enregistrés sous AnomaliaZPrigimalia.Native. Correctif 7714659 ; fixtures mises à jour et rejet explicite des rapports anciens. **8 tests locaux du lanceur réussis**, avec staging de données neutralisé pour isoler l'orchestration ; ils ne prouvent ni une compilation ni un test Unreal. Contrôles source GitHub réussis séparément.

Run [41801391717](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/41801391717) : réserve du vrai C: contrôlée avant copie. Source, configuration, contenu versionné et binaire Editor compilé copiés vers un nouveau dossier C:\ANOMALIA_MISSION_<run>, sans Intermediate ni Saved ; empreinte DLL comparée avant/après, reçu de source conservé. Tests natifs avec bon préfixe et cible Game exécutés séparément afin qu'un échec indépendant ne masque pas l'autre. Résultats en attente à ce point.

Inspection GLB [41800855341](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/41800855341) **réussie** : GLB 2.0, 1 mesh / 1 nœud, 161 matériaux, 145 textures, 1 366 382 triangles d'après les accesseurs de la scène active. Aucune extension obligatoire ; KHR_materials_specular seulement déclarée utilisée. Bornes après transformation : 3 386,661 × 210,706 × 3 507,576 unités du fichier. Ces bornes ne prouvent ni l'échelle du circuit, ni une longueur de tour de 5,451 km, ni les collisions ; pas d'import Unreal effectué.

## État consolidé vérifié — 4 novembre 2026

Cette section remplace les mentions provisoires « résultats en attente » ci-dessus.

### Compilation et tests réellement exécutés

- [41801391717](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/41801391717), artefact 13308500967 : **Game compilé, sortie 0 ; 28/28 tests natifs réussis, 0 échec**, dont les 19 requis présents. Avec Editor réussi dans 41800675310, les deux cibles ont compilé sur la base 0360ec9 + correctif NavigationSystem f0f5144. Cela ne valide pas les changements C++ ultérieurs.
- [41804781472](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/41804781472), artefact 13308509212 : **scénario Survival PIE réussi avec capture réelle 1280 × 720**. BP_Anomalia_Survival, squelette/Animation Blueprint compatibles, cinq vêtements existants. Marche 449,961 cm/s ; sprint 679,923 cm/s ; saut 89,977 cm ; variation osseuse 67,455 cm ; capsule 88 → 60 → 88 ; stamina 100 → 80,336 ; ajout/retrait pomme 0 → 0,15 → 0 kg ; retrait/rééquipement veste réussi.
- [Capture réelle](https://chatgpt.com/library?file_id=libfile_8e42aa12a92c819186eae25ef5587ca9&account_id=personal) : personnage et vêtements visibles dans une scène de vérification transitoire, **pas SKARVIK**.
- Le scénario pilote des API du personnage ; il ne valide pas toutes les touches physiques, les échelles, le franchissement, le rechargement, le multijoueur ou la persistance des compagnons.
- Le premier scénario avait échoué sur un gel du temps simulé pendant l'accroupissement. Correctif du dispositif de test : finir la compilation d'assets et désactiver le throttling de cette session avant les phases chronométrées, sans réduire les seuils fonctionnels.
- Des erreurs génériques LogAutomationTest apparaissent à l'initialisation ; leur origine reste à isoler. Le succès du scénario ne signifie pas que tous les journaux de démarrage sont propres.
- Aucune mesure FPS de SKARVIK ou performance globale de version publiée. Le coût de capture ne constitue pas une mesure de fluidité.

### Conservation et espace disque

[41804514908](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/41804514908), artefact 13309013918 : **1 782 fichiers de validation conservés**, 4 731 164 756 octets, empreintes comparées avant/après. Seul le dossier de validation créé par cette mission a été transféré vers C:\ANOMALIA_MISSION_ARCHIVE_m41798670858. Ancien chemin maintenu par jonction. **4 735 266 816 octets récupérés sur D:**, réserve finale 4 735 844 352 octets. Aucun contenu du véritable D:\ANOMALIA ni sauvegarde utilisateur supprimé.

### Régressions et correctifs candidats encore non validés

- [41805598581](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/41805598581), artefact 13309073582 : **inventaire PIE en échec, phase 5**, dépôt bancaire introuvable. Ramassage physique, relecture de profil et ouverture clavier/manette avaient été atteints.
- Le test utilisait l'ancienne présentation. L'interface actuelle exige de sélectionner une tuile avant d'afficher ses actions, et de choisir l'onglet banque avant retrait. Fixture corrigée sans contourner les transactions ni retirer les assertions de quantité/rotation/pagination.
- Candidat GameMode 0a78c50 : utiliser le véritable BP Survival installé comme personnage par défaut seulement si son mesh et le squelette de son Animation Blueprint correspondent. Le repli natif reste explicite si les ressources manquent. Ce candidat exige encore compilation et PIE ; ne pas l'annoncer déployé dans D:.
- Les premiers essais de relance ont échoué dans l'infrastructure avant compilation : accès raw HTTP 404 puis tableau JSON imbriqué sous Windows PowerShell 5. Récupération authentifiée et lecture du tableau corrigées. Nouvel essai [41809230466](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/41809230466) en cours au moment de cette mise à jour.
- La première comparaison des sources locales a expiré sans reçu exploitable ; le second essai utilisait l'alias Python Microsoft Store absent. Comparaison corrigée pour utiliser Python fourni avec Unreal et écrire un reçu après chaque projet ; aucun résultat de comparaison n'est encore revendiqué.

### Progression sur critères vérifiables

| Domaine | Résultat vérifié | Limite |
|---|---|---|
| Compilation de la base corrigée | 2/2 cibles, 100 % | Pas un pourcentage d'achèvement du jeu ; candidat GameMode exclu |
| Suite native de la base | 28/28 tests, 100 % | Couverture limitée aux règles enregistrées |
| Scénario Survival | 1/1 scénario exécuté réussi | Toutes les animations demandées ne sont pas couvertes |
| Inventaire PIE complet | 0/1 scénario complet réussi | Nouvelle tentative nécessaire |
| SKARVIK | Preuves historiques récupérées | Villes, 7 îles, routes raccordées et entrées de bâtiments non réceptionnées globalement |
| Animaux | Modèles identifiés ; ancien système chien documenté | IA multi-espèces et compagnons simultanés non validés |
| Circuit F1 | Archive et métadonnées vérifiées | Licence exacte, import, collisions et tour conduisible non validés |
| Véhicules | Résultats E39 antérieurs récupérés | Aucune nouvelle réception de conduite sur SKARVIK/circuit |

Les pourcentages globaux par domaine restent **non calculables** tant que les critères de réception et leur comptage ne sont pas vérifiés. Le « 55 % » antérieur n'est pas confirmé par ces preuves. Travail conservé sur mission/finalisation-20261104 et PR brouillon #64, sans fusion.

## Réconciliation achevée et nouveau binaire compilé

- [41809486397](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/41809486397), artefact 13312200664 : comparaison en lecture seule achevée, 130 chemins source attendus. D:\ANOMALIA utilise encore le module AnomaliaPrimeval (129 fichiers source sous cet ancien nom), la carte /Game/AnomaliaWorld et l'ancien GameMode. Les 130 chemins renommés y sont absents ; ce résultat ne signifie pas que son ancien code est vide.
- La copie SKARVIK avancée possède 281 fichiers source, dont les modules CitySample et CitySampleAnimGraphRuntime. 126/130 fichiers du module principal correspondent exactement à la base validée ; les quatre différences sont Build.cs, LootSubsystem.cpp/.h et LootTests.cpp.
- Les trois blobs de loot présents dans SKARVIK ont été retrouvés dans GitHub et comparés aux sources de branche : ils précèdent les ajouts de découverte de loot dans les bâtiments proches et le filtrage par distance. La différence Build.cs est précisément l'absence de NavigationSystem. Aucun de ces fichiers de la copie SKARVIK n'a été écrasé.
- La configuration de cette copie utilise DX12/SM6 et conserve aussi SM5/D3D11 ; cela ne prouve pas une réception visuelle SM5. Sa carte par défaut est ANOMALIA_Playable_v1, pas le niveau final SKARVIK.
- [41809453748](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/41809453748), artefact 13312195539 : le correctif GameMode e705bbf et la fixture 79d1245 compilent **Editor 0 / Game 0 ; suite native 28/28, 0 échec**. DLL SHA256 681E5A01A2F655868712F64131C896F1504139F82FE7572923D07A374B4FABBE ; anciens binaires conservés.
- Les assertions PIE d'apparition effective du BP Survival, de mesh et d'instance d'animation passent dans cette exécution. Le scénario complet échoue ensuite sur la localisation de la tuile du billet. Aucun dépôt/retrait réussi n'est encore revendiqué.
- Fixture 94724d9 : recherche de la liaison SelectStack du contrôle UMG vivant, couvrant mains et stockage ; seul le vrai clic du bouton est ensuite déclenché, sans appel direct de transaction. [Nouvelle validation 41810078053](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/41810078053) en cours lors de cette mise à jour.
- [Plan de transfert 41810344559](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/41810344559) préparé : dépendances du niveau final existant, comparaison de présence/taille sur D:, conflits à préserver, empreinte du .umap avant/après. Ce travail ne copie aucun asset et ne sauvegarde aucun niveau. Une taille identique reste explicitement à comparer par empreinte avant transfert.
