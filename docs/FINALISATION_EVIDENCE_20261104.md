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
