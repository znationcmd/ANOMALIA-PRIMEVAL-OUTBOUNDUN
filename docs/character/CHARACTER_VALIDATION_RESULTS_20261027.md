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
