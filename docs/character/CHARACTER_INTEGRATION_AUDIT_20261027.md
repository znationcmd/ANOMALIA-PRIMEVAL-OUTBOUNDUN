# Audit réel des personnages ANOMALIA — 27 octobre 2026

## Périmètre vérifié
Poste Windows ANOMALIA-PC, projet `C:\ANOMALIA\unreal\AnomaliaPrimeval.uproject`.
Unreal chargé : `5.8.3-58210709+++UE5+Release-5.8`.

Preuves :
- Audit disque : https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40541978287
- Chargement réel par commandlet UE : https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40542226182
- Inventaire détaillé : `INSTALLED_CHARACTER_ASSETS_20261027.json`.

## Constats
- `/Game/BP_AnomaliaSurvivor` hérite de la vraie classe native ANOMALIA, mais son `CharacterMesh0` n’a ni mesh ni classe d’animation.
- Les sources installées sont antérieures à la branche de la PR #43 : pas de composants de vêtements, de système d’allures tactiques ou d’ItemEffects dans le Survivor installé. Le script d’intégration n’est pas installé.
- `C:\ANOMALIA` n’est pas un checkout Git. Aucun HEAD local ne peut être assimilé à la PR.
- `Content`, `Source`, `Config` sont présents ; aucun dossier `Plugins` de projet. Le fichier projet installé déclare EnhancedInput, ChaosVehiclesPlugin, Water, PCG et PythonScriptPlugin, avec EngineAssociation 5.8. La version exacte a été vérifiée dans Build.version puis dans Unreal.
- 26 SkeletalMeshes, 3 Skeletons, 8 AnimBlueprints et 87 AnimSequences chargés dans les trois racines inventoriées. Aucun échec de chargement de ces assets.
- Avertissement Unreal : référence manquante `/Game/Survival_01/Demo/Characters/Mannequins/Rigs/CR_Mannequin_BasicFootIK`. Un rig portant ce nom existe sous Survival_Character, mais aucun redirect n’a été appliqué à ce stade.

## État des packs
| Pack | Corps / animation constatés | Modularité et limites |
| --- | --- | --- |
| Manny | SKM_Manny et Simple, ABP_Manny ; squelette ControlRig/Characters/Mannequins/Meshes/SK_Mannequin | Aucun vêtement compatible certifié dans cet audit |
| Quinn | SKM_Quinn et Simple, ABP_Quinn ; même squelette que Manny | Aucun vêtement compatible certifié dans cet audit |
| Quantum | SKM_QuantumCharacter, NoHead, squelette SK_Military_Character_Skeleton ; 10 AnimSequences | Aucun AnimBlueprint du pack trouvé ; pas de transfert implicite vers Manny/Quinn |
| Survival | SK_Survival_Character, Body, Body_Parts ; ABP_Manny/ABP_Quinn du sous-dossier Demo utilisent réellement SKEL_Survival_Character | Veste, jeans, gants, chaussures et sac séparés, tous sur SKEL_Survival_Character. Ajustement et clipping non validés |

Les noms des AnimBlueprints Survival n’impliquent pas une compatibilité avec le squelette ControlRig : leurs TargetSkeleton réels sont distincts.

## Les 17 éléments Quantum/Modules
8 meshes squelettiques :
SKM_Arms, SKM_Bulletproof_Bege, SKM_Drops_1_Bege, SKM_Head, SKM_Holster_Hard_Bege, SKM_Jeans, SKM_Patch_Back, SKM_Shirt_RolledUp_Blue.

8 assets physiques :
PA_Arms, PA_Bulletproof_Physics, PA_Drops_1_Physics, PA_Head_PhysicsAsset, PA_Holster_Hard_Bege_Physics, PA_Jeans, PA_Patch_Back_Physics, PA_Shirt_RolledUp.

1 mesh statique :
SM_Cap_Bege. Cette casquette nécessite un attachement adapté ; elle ne peut pas suivre un Leader Pose comme un SkeletalMesh.

## Correction du script
`unreal/Content/Python/setup_anomalia_character.py` :
- Mode audit par défaut ; création uniquement par sélection explicite.
- Plus de recherche approximative ni de choix du premier résultat.
- Un nom distinct par profil, aucun changement de GameMode ou de carte existante.
- Refus des assets existants avant modification ; pas de suppression.
- Animation obligatoire, identité exacte du squelette exigée, absence de classe générée refusée.
- Modification de la template Mesh héritée dans le package du Blueprint enfant, avec contrôle de propriété ; pas d’édition de la template native du parent.
- Compilation Blueprint et contrôle du corps et de l’animation sur le CDO après compilation ; sauvegarde uniquement après ces contrôles.
- Rapport JSON à nom unique dans Saved/CharacterAudit.
- Si une création échoue en cours de lot, les assets déjà sauvegardés sont conservés et le rapport indique les créations et l’erreur. Le script ne prétend pas assurer une transaction globale.

Ancienne version préservée dans l’historique Git : blob `9e755bbf7f3000fd918011bfaef521e3157f9463`, commit de base `eb9706558744d3e926ffdf0633e710316798105f`.
Les fichiers existants du projet installé ne sont pas remplacés.

## Validation et travaux restant à couvrir
7 tests Python de prévalidation réussis : chemins stricts, absence de fallback, type manquant, conflit de nom, squelette incompatible, animation Quantum non vérifiée et nom de Blueprint.
Ces tests utilisent un double minimal du module unreal et ne constituent ni une compilation UE ni une session de jeu.

La première tentative de validation isolée s’est arrêtée au checkout : chemins Windows trop longs, avant compilation. Le workflow a été corrigé avec une configuration Git limitée au processus de checkout et un répertoire de compilation court et unique. Aucune politique Windows globale n’a été modifiée.

Compilation native, création effective des Blueprints et résultats finaux : voir le complément de validation enregistré après les exécutions.

Le système demandé de 9 emplacements, l’équipement depuis des piles d’inventaire, les validations serveur, le masquage du corps, les sockets, la persistance, les statistiques de protection/isolation/capacité et la réplication ne sont pas achevés par cet audit. La fonction cosmétique de la PR #43 n’est pas une implémentation de ce système.

Le poids de l’inventaire et les déplacements tactiques existent dans la branche #43, pas dans les sources installées observées. Reptation, inclinaison, franchissement et transitions réalistes restent à implémenter et tester.

Aucun catalogue interactif ANOMALIA Editor, aperçu d’animations ou bouton décoratif n’est ajouté dans ce lot. Aucun test PIE, deux joueurs, sauvegarde/reconnexion ni capture de rendu ne doit être déduit de l’audit en NullRHI.

## Ressources et préservation
L’audit constate la présence locale des packs ; il ne certifie pas leurs licences ou les droits de redistribution. Aucun mesh, texture ou animation Fab n’est publié dans GitHub. Les validations isolées utilisent des copies locales.

Aucun véhicule E39, bâtiment, carte existante, sauvegarde utilisateur, serveur ou configuration du jeu installé n’a été remplacé. Aucune fusion dans la branche principale.
