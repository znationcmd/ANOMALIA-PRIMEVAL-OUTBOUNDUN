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
