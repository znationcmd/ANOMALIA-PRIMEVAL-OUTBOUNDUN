# Validation personnages — résultats confirmés et blocages

## Actions réellement exécutées sur le poste Windows

- Audit disque et version : `C:\ANOMALIA\unreal\AnomaliaPrimeval.uproject` présent, Unreal 5.8.3 confirmé.
- Commandlet Unreal de chargement des packs : succès, zéro erreur de chargement des objets inventoriés. Une référence de Control Rig de pied vers Survival_01 manque.
- Création réelle de `BP_Anomalia_Manny`, `BP_Anomalia_Quinn`, `BP_Anomalia_Survival` sous `/Game/Anomalia/Characters` : compilation Blueprint, vérification du corps/de la classe d’animation sur le CDO puis sauvegarde réussies.
- Preuve : https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40543337391 ; artefact 12752758014.
- Ces trois nouveaux Blueprints utilisent la classe native déjà installée. Aucun Blueprint préexistant ni personnage par défaut n’est remplacé.
- Quantum est inventorié mais n’a pas de Blueprint ANOMALIA créé : ses séquences et son squelette sont présents, aucun AnimBlueprint compatible n’a été trouvé dans le pack installé.

## Compilation native de la branche

La tentative isolée 40543166274 a réellement compilé les sources Editor, puis échoué, code de sortie 6. Game et les tests natifs n’ont pas été exécutés dans cette tentative.

Erreurs constatées :
- C2672 dans AnomaliaTacticalSpeedTests.cpp : TestNotNull ne déduit pas un pointeur à partir d’un TObjectPtr.
- C2065 dans Vehicles/AnomaliaVehicleSurvival.cpp : DOREPLIFETIME attend le paramètre OutLifetimeProps, nommé Out dans la définition.

Corrections enregistrées :
- Utilisation de VitalsComponent.Get() dans le test.
- Paramètre OutLifetimeProps et appel Super concordants dans le composant véhicule.
- Remplacement de l’accès déprécié à CrouchedHalfHeight par SetCrouchedHalfHeight/GetCrouchedHalfHeight.

La reprise 40546939481 utilise uniquement la copie isolée `C:\ANOMALIA-Validation\c40543166274`. Les trois sources sont vérifiées par leurs blobs Git avant et après correction ; les octets originaux sont sauvegardés avant écriture.

Pour conserver le cache de compilation, le marqueur embarqué reste le commit de base `3d044d6de6108eb99dc15a597920828e6dab79f5`. **Ce marqueur seul ne décrit donc pas le code corrigé.** Le reçu `source-patch-receipt.json` identifie séparément le commit des corrections `0a60cda9b31aaff1e38ba7a4caec0a1fae27d809` et les blobs de chaque fichier. Ne pas confondre ce résultat avec une compilation sans modification du commit de base.

## État non encore validé

La sauvegarde des Blueprints ne prouve pas une session de jeu. À ce point, déplacements en PIE, évaluation des animations en mouvement, collisions visuelles, vêtements équipés depuis l’inventaire, sauvegarde/reconnexion et deux joueurs ne sont pas validés.

Les sources installées sont plus anciennes que celles de la PR #43 ; elles ne contiennent pas son API de vêtements. Les corrections natives et la scène modulaire doivent d’abord être validées dans la copie isolée. Aucun remplacement large de l’installation n’est effectué.

La carte de test séparée et ses vérifications de rechargement sont en cours de contrôle. Les rapports finaux des exécutions font autorité sur les seuls outils de test ajoutés au dépôt.

## Préservation

La BMW E39 et ses assets sont conservés. La compilation a également révélé un blocage réel dans son composant de survie ; la correction de compilation n’équivaut pas à un test natif complet des clés, pièces ou échanges de cargaison.

Les modèles Fab ne sont pas publiés dans GitHub. Les PR #44 et #45 restent en brouillon, sans fusion.

## Résultats ultérieurs effectivement vérifiés

- Reprise native 40546939481 : Editor et Game compilés, code de sortie 0 ; **26 tests natifs réussis**, dont TacticalMovement.SpeedLoadFatigueAndCrouch et VehicleKeyPartsCargoAndRecovery. Le job a ensuite échoué dans une première version du script de scène Python ; cela n’annule pas les compilations et tests précédents.
- Scène installée 40547916155 : trois personnages créés dans une carte séparée, caméra/inventaire/vitals/capsule trouvés ; sauvegarde puis rechargement de la carte réussis. L’ancienne classe native installée ne dispose pas de l’API des vêtements.
- Scène modulaire isolée 40549277135 : veste, pantalon, chaussures, gants et sac à dos Survival appliqués, retirés et réappliqués via l’API ; vêtement Quantum au squelette différent rejeté ; carte sauvegardée et rechargée.
- Correction de référence de rig 40550113760 : redirection de package exacte, configuration sauvegardée avant modification, validation avant installation. Aucun asset Fab réécrit.
- Captures GPU réelles 40550553551 : trois personnages visibles ; instances ABP actives ; variations des positions d’os observées dans l’éditeur pour Manny, Quinn et Survival. Les cinq vêtements ont le corps comme Leader Pose et zéro écart observé sur les cinq os comparés. Preuves : artefact 12755186683. Les captures ont été inspectées ; elles montrent le corps habillé, les mannequins et le sac. L’éclairage de la scène de test est encore sommaire.

Ces observations d’éditeur **ne sont pas un test PIE**, ne prouvent pas les commandes du joueur, toutes les transitions d’animation ou l’absence de traversées dans chaque posture. La sauvegarde de carte n’est pas une sauvegarde de profil joueur.

Restent : équipement depuis l’inventaire, validation serveur et réplication, apparence persistante après reconnexion, tous les emplacements, masquage du corps, Quantum animé, position allongée/inclinaison/franchissement, catalogue ANOMALIA Editor et essai deux joueurs. La classe native compilée reste dans la copie isolée.

## Reprise du 27 octobre — sessions PIE effectivement exécutées

Les workflows 40586546392 et 40586806231 ont démarré un vrai monde PIE. Deux erreurs du nouveau script de test ont été corrigées : chargement des classes avant PIE/identification des acteurs placés et vérification de possession via le contrôleur du Pawn. Ces exécutions échouées ne sont pas des tests réussis du personnage.

Le run 40587016325 a effectivement possédé Manny, trouvé sa caméra active et son ABP_Manny, et observé 11,44 cm de variation de l’os mesuré. La marche automatisée n’a pas passé le contrôle (distance et vitesse observées nulles). Cela reste à diagnostiquer ; aucune acceptation de déplacement, sprint, saut, inventaire ou tenue en session n’en découle.

La reprise 40587325434 mesure les phases en temps de simulation et ajoute des diagnostics. Elle a planté avec sortie 3 avant résultat final : GenericPlatformMemory.cpp indique un manque de mémoire et un fichier de pagination insuffisant. Le journal rapporte environ 0,38 Gio de RAM et 0,02 Gio de mémoire virtuelle disponibles, ainsi que ZenLocal HTTP 507 Insufficient Storage. L’audit disque indépendant 40586922691 mesurait 6 491 983 872 octets libres sur C:. Ne pas conclure à un problème de licence ou à la disparition du projet à partir de ce crash.

Journaux conservés dans les artefacts des quatre runs et sous C:\ANOMALIA-Validation\Reports\character-pie-<run>. Le code de test est versionné dans unreal/Content/Python/verify_anomalia_character_pie.py. Aucun changement natif C++ supplémentaire ni remplacement du projet installé dans cette reprise. Les tests clavier/manette, multijoueur et sauvegarde/reconnexion restent non validés.

## Reprise du 28 octobre : essai Survival isolé et garde mémoire virtuelle

Nouveau script verify_anomalia_survival_pie.py préparé : monde transitoire séparé, Survival seul avec ses cinq vêtements, GameModeBase de test, sol à collision explicite et diagnostics de mouvement sauvegardés pendant les phases. Aucun fichier de carte existant, Blueprint de personnage ou réglage de GameMode principal n'est sauvegardé par cet essai. La qualité des textures est réduite pour ce processus de test seulement.

Sa syntaxe Python a été vérifiée. Son exécution Unreal n'a PAS eu lieu : le run 40653389189 a arrêté le lancement au contrôle de ressources. Mesures du 28 octobre à 07:57 UTC : disque libre 10 028 253 184 octets, RAM disponible 3 057 963 008 octets, mémoire virtuelle disponible 7 625 148 Kio. Le workflow exige, comme marges opérationnelles pour cet essai, 10 Gio de disque, 4 Gio de RAM et 8 Gio de mémoire virtuelle ; ces seuils ne sont pas présentés comme les minima officiels d'Unreal.

Le contrôle léger précédent 40652279470 avait mesuré davantage de marge, mais la vérification juste avant lancement fait autorité. Le garde-fou a évité de reproduire le crash mémoire/pagination. Les essais de marche, course, saut, accroupissement, inventaire et équipement en PIE restent à passer.

Une correction candidate de masse du coffre E39 est également versionnée dans cette branche native commune (commit e36f83420a8c6bd3a4147169e5ec7253755c8048), avec reçu de préparation et workflow de compilation/test dédiés. Le run 40652769294 a été bloqué avant compilation par la réserve disque. Les 26 succès natifs historiques portent sur le code précédemment compilé et ne valident PAS ce nouveau correctif.


## Validation réelle du 28 octobre 2026 — résultats désormais compilés

Les blocages et échecs précédents ci-dessus restent historiques. Après récupération de mémoire, compilation incrémentale réelle **Editor et Game réussie** avec Unreal 5.8.3 : [run 40654988106](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40654988106), artefact 12801262040. Le correctif natif testé est e36f83420a8c6bd3a4147169e5ec7253755c8048 ; les trois fichiers sont contrôlés par empreinte avant le test. Le stamp de build conservé pour le cache est 3d044d6de6108eb99dc15a597920828e6dab79f5 : il ne représente pas à lui seul les sources du correctif ; consulter source-patch-receipt.json et build-provenance.json.

[Run physique 40655809703](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40655809703) : **26 tests natifs réussis, 64 contrôles physiques réussis, 313 échantillons physiques**, état CHAOS_ROAD_PHYSICS_DRIVE_PASSED. Le dépôt/retrait de cargaison modifie et restaure la masse réelle ; une notification répétée n'accumule pas la masse. Les six ouvrants, collisions/verrouillage, batterie dans le coffre, radiateur/bougie sous le capot, clé physique, inventaire conservé entrée/sortie, roues/suspension Chaos, transmission manuelle, éclairage, carburant et freinage ont été exercés. Distances de freinage mesurées : 13,35 m à 50,61 km/h, 30,87 m à 80,32 km/h sur adhérence 0,9 ; 56,87 m à 80,04 km/h sur adhérence 0,45. Ce sont des mesures de la scène de test, pas une certification automobile.

Artefact 12802022147 : accepted-run.json, drive-report.json, journaux natifs/physiques, provenance et captures réelles. La capture coffre ouvert a été inspectée : coffre levé visible, intérieur très sombre. La finition visuelle du coffre/cockpit reste à examiner ; aucun remodelage de la géométrie v7 dans cette correction.

**Portée : copie de validation C:\ANOMALIA-Validation\c40543166274\unreal**, carte /Game/Anomalia/CharacterTests/E39Resume_40587487588/ANOMALIA_E39DriveReview_v1. Aucun nouveau DLL déployé dans C:\ANOMALIA\unreal. Pas de jeu packagé, multijoueur ni animation d'entrée validés. Deux avertissements d'API SetBase/GetMovementBase restent à traiter ; les journaux comportent aussi des erreurs génériques d'automatisation au démarrage GPU non résolues, malgré les rapports structurés réussis. Aucun merge.

## Survival : première session PIE réussie

[Run 40656105121](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40656105121), artefact 12800919597, état SINGLE_PLAYER_PIE_API_CHECKS_PASSED_NOT_FULL_GAMEPLAY_ACCEPTANCE. Monde PIE transitoire réel, Survival possédé, caméra active et instance ABP_Quinn du pack.

- Marche observée 449,98 cm/s ; course 679,95 cm/s ; endurance 100 → 80,485.
- Capsule accroupie 88 → 60 cm puis retour debout ; saut 89,92 cm et atterrissage.
- Mouvement réel d'os : déplacement maximal main 67,68 cm.
- Ajout/retrait d'une pomme dans l'inventaire natif ; poids 0 → 0,15 kg.
- Retrait puis remise de veste par API natif réussis ; cinq vêtements présents dans la scène de test.

Entrées automatisées par API du pawn/composants : clavier physique et UI d'inventaire non testés. Cet essai ne teste ni sauvegarde/reconnexion ni multijoueur. Le script create_anomalia_survival_playtest.py et son workflow préparent une carte persistante avec nouveau pawn, GameMode natif et profil séparé ; son résultat doit être consigné séparément après exécution. La persistance des choix de vêtements par joueur, leur équipement depuis l'inventaire/UI et leur réplication restent à développer/valider. Manny et Quinn restent disponibles ; Quantum n'a pas d'AnimBP compatible validé et n'est pas annoncé jouable.


## Carte Survival sauvegardée et accessible — 28 octobre 08:49 UTC

**Réussite complète du processus** : [40658680443](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40658680443), artefact 12802064916. Nouveau BP_Survival_Playtest, GM_Survival_Playtest enfant du GameMode ANOMALIA et L_Survival_Playtest créés, compilés/sauvegardés puis carte rechargée. Racine : /Game/Anomalia/CharacterTests/SurvivalPlayable_40658680443. Les cinq defaults de vêtements ont été vérifiés. Profil strictement séparé survival-playtest-40658680443, joueur local-owner.

Le GameMode natif a réellement chargé deux pommes, les tests de mouvement/animation/inventaire ont passé, puis RequestUseStack a consommé une pomme et porté la faim de 80 à 94. Après un OpenLevel vers la même carte et le même profil, un nouveau pawn a chargé UNE pomme. Cela valide une sauvegarde/relecture et un voyage de carte dans le même processus, pas une reconnexion réseau. Les cinq pièces réapparaissent par défaut du Blueprint : aucun choix d'apparence par joueur persisté.

**Captures stabilisées et limite de fermeture** : [40659026008](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40659026008), artefact 12802568246. Les contrôles de jeu, inventaire, relecture et les trois captures ont passé ; les fichiers finaux et leurs empreintes ont été vérifiés après téléchargement. Inspection visuelle : personnage vêtu de face, même personnage torse nu après retrait de veste, puis dos avec veste et sac visibles. L'éclairage de face reste sombre. Le processus a néanmoins quitté avec 3221225477 (0xC0000005) après QUIT_EDITOR, arrêt des sous-systèmes et fermeture du journal : le workflow est en ÉCHEC et ce défaut de fermeture reste ouvert. Ne pas le qualifier de réussite globale. La première reprise 40658433626 avait échoué lors de l'initialisation de l'inventaire en monde éditeur ; la préparation a été déplacée après BeginPlay, sans supprimer ses assets de diagnostic.

**Lanceur réellement créé et relu** : [40659474346](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40659474346). Bureau Windows : ANOMALIA_Test_Survival_20261028_40659474346.cmd. Il pointe vers la carte du run 40658680443 terminé avec succès, dans la copie de validation, avec URL de profil isolé. Les trois fichiers assets sauvegardés et les exécutables ont été vérifiés avant création. Aucun raccourci remplacé, aucun lancement interactif ni contrôle clavier/UI annoncé. Double-cliquer ce lanceur permet d'ouvrir le test -game sans dépendre de l'association .uproject.

Le GameMode principal, C:\ANOMALIA\unreal et les profils existants sont préservés. Les recettes JSON runtime_validation_20261028.json et survival_saved_playtest_20261028.json distinguent les succès de jeu du défaut de fermeture. Vêtements depuis inventaire/UI, validation serveur de l'apparence, réplication, masquage du corps et reconnexion restent non acceptés.


## Inventaire hybride et touche Tab — 28 octobre

La première interface proximité/personnage/grille est compilée et disponible dans le test. Run 40669554052 réussi (exit 0) : 11 contrôles de callbacks UMG et caméra restaurée, deux captures UI, séparation/fusion/mains/rangement/rotation/consommation natifs exercés. Clavier/souris physiques et réseau non testés. Voir INVENTORY_HYBRID_20261028.md pour les reçus et limites.

Tab et le DPI ont ensuite compilé avec succès (40678901767). Les nouvelles fonctions ont compilé dans la cible Editor : 40681165103, 40691913211 puis 40692598129. I et Tab sont configurés, sans essai de clavier physique. Le projet installé reste préservé.

Essai réel [40692693342](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40692693342), artefact 12817243545 : **25 contrôles réussis, processus code 0, erreurs du rapport vides, caméra restaurée**. Trois captures UI inspectables : inventaire, transferts et fabrication. Actions UMG liées réellement exécutées : rangement veste/sac, retrait d'une veste vide et refus si occupée, sauvegarde/relecture du cargo de sac manquant en retrait seul, espèces 50 EUR issues d'un billet physique, quatre recettes avec consommation des matériaux, refus de recette inconnue et de ramassable nul. Une volaille crue enregistrée dans un nouveau scope privé a été listée et ramassée par le bouton de proximité, avec augmentation exacte du stock. Les configurations de loot de ce test n'affectent que inventory-hybrid-40692693342. Aucun clavier physique, réseau ou transfert bancaire effectué. Inspection de la capture : vêtements Survival visibles sur le corps, argent au-dessus, proximité gauche ; libellés de petites cases encore tronqués et avertissement moteur de lumière superposé. La finition visuelle complète n'est pas acceptée.

Les miniatures rendues des objets/vêtements, l'équipement des vêtements depuis l'inventaire, la persistance/réplication de l'apparence et le multijoueur restent à développer ou valider. Voir INVENTORY_HYBRID_20261028.md. Aucune fusion.
