# ANOMALIA'Z PRIGIMALIA — préproduction du vrai générique 3D

Le code de cette branche prépare une **véritable Level Sequence 3D** Unreal Engine 5.8 utilisant **les squelettes et clips d'animation du projet**, sans générer de faux modèles et **sans modifier de carte existante**.

## Créer la séquence dans Unreal, sans solliciter le travail en cours

1. Synchroniser cette branche indépendamment de la branche Work en cours. **Ne pas fusionner automatiquement**. Garder les sauvegardes Windows.
2. Dans le projet **AnomaliaZPrigimalia.uproject**, préparer un **niveau de prévisualisation distinct**, dont le chemin contient **IntroStage** (par exemple `/Game/AnomaliaZPrigimalia/Cinematics/Maps/L_IntroStage`). Ne pas utiliser une carte principale ni remplacer une carte existante.
3. Dans ce niveau, placer le **véritable personnage Survivor** et le **German Shepherd 3D** de la copie Unreal avec des animations compatibles; positionner les deux à moins de 15 m.
4. Sélectionner **seulement ces deux acteurs** dans le World Outliner. Renommer au besoin le label du chien en `GermanShepherd_Intro`, sans altérer son Blueprint source.
5. Activer les plugins Python Editor Script / Level Sequence Editor ; exécuter `unreal/Scripts/create_prigimalia_sequencer_3d.py` depuis l'éditeur.
6. Vérifier que l'asset **`/Game/AnomaliaZPrigimalia/Cinematics/LS_IntroSurvivorDog_30s`** est créé ; inspecter 900 frames à 30 FPS, les rigs, les deux pistes d'animation, et le mouvement de caméra.
7. L'export MP4 doit ensuite être réalisé avec **Movie Render Queue**. Remplacer le média instrumentale seulement après validation du rendu, de la musique et du son vocal au clic.

## Ce qui est automatisé dans ce script

- Refuse un projet Unreal différent et refuse de fonctionner en dehors d'un niveau explicitement nommé `IntroStage`.
- Refuse d'écraser un Level Sequence portant déjà ce nom.
- Exige une sélection précise des deux acteurs; vérifie leurs véritables SkeletalMesh et Skeleton.
- Identifie dans le registre d'assets des **AnimSequence réellement compatibles** avec chaque squelette et vérifie leur durée. Aucun asset n'est retargeté ou remplacé automatiquement.
- Crée un Level Sequence dédié de 30 secondes, ajoute les deux acteurs et leurs Animation Tracks.
- Ajoute une caméra cinématique temporaire et six positions clefs pour faire progresser le cadre sur le survivant et le chien.
- Écrit un rapport sous `Saved/Intro3D/intro3d_preview_audit.json` sans toucher aux profils joueurs.

## Limites et validation

- **Non exécuté sur le PC** : le script doit encore être testé dans le projet Unreal contenant les assets, car il dépend de plugins et clips locaux.
- Sélection par compatibilité de squelette ne garantit pas que l'animation retenue soit la meilleure. Un animateur doit valider/ajuster la démarche, les raccords et les mouvements du chien, éventuellement retoucher avec Control Rig.
- Les acteurs sont liés au niveau `IntroStage` comme **possessables**. Ne pas supprimer le niveau de staging ni supposer qu'ils sont automatiquement présents dans une map du jeu.
- Le script **n'effectue pas l'export vidéo** et ne remplace pas encore la cinématique 2D dans le jeu. La PR #65 configure déjà le système de lecture vidéo, mais il faut un MP4 3D vérifié pour remplacer son média.
- Travail réalisé sur une branche séparée afin de ne pas interférer avec Work, la migration, les quinze cartes et les sauvegardes.

## Validation de sortie

- Ouvrir la séquence ; lecture 0–30 s sans animation manquante ; mouvement visible du survivant et du chien ; caméra bien cadrée.
- Vérifier que `IntroStage` seulement héberge les poses temporaires.
- Effectuer rendu MP4 ; écouter la piste instrumentale ; cliquer sur le bouton intégré au jeu et contrôler que la voix grave annonce le nom **une fois**.
- Refaire des tests d'ouverture du menu, saut de cinématique, « Jouer » et sortie du menu. Seul le résultat de tests réels peut valider la fonctionnalité.
