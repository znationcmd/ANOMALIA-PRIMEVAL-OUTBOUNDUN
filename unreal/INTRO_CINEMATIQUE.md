# ANOMALIA'Z PRIGIMALIA — Générique d'horreur original + sang animé au clic

Cette PR reste **en brouillon**, indépendante des tâches en cours sur les cartes, personnages, sauvegardes et serveurs.

## Expérience proposée

1. **Démarrage solo / ANOMALIA_Playable_v1** : lancement de la cinématique 30 secondes, avec **musique horrifique originale**, synthèse de grognements de zombies, craquements de bois, vent et impacts graves.
2. **PASSER** : saute à l'annonce du titre. À la fin de la vidéo : **CLIQUER POUR COMMENCER** apparaît.
3. **Au clic seulement** : passage à un clip muet de six secondes **où des coulées de sang rouge progressent sur le logo**, et **lecture synchronisée de la voix grave** « ANOMALIA'Z PRIGIMALIA ».
4. Dès que la voix est terminée : ouverture du **véritable menu natif UAnomaliaZPrigimaliaSessionWidget**, pas un faux menu imprimé dans la vidéo. En cas de média manquant, repli sur le menu existant.
5. Pas de modification aux profils personnels, sauvegardes, autres maps, ou logique réseau.

## Fichiers médias v2 (nouveaux noms, pas d'écrasement des médias v1)

Décompresser le pack livré indépendamment de GitHub dans le dossier contenant **unreal/AnomaliaZPrigimalia.uproject**, ce qui crée :

- `unreal/SourceAssets/Intro/ANOMALIAZ_PRIGIMALIA_Intro_Horreur_30s.mp4` — vidéo avec musique + sons de zombies + bois qui craque, **sans annonce vocale**.
- `unreal/SourceAssets/Intro/ANOMALIAZ_PRIGIMALIA_Clic_Sang_6s.mp4` — animation sang sur le logo **sans audio**, déclenchée au clic seulement.
- `unreal/SourceAssets/Intro/SW_IntroTitle_Deep_v2.wav` — voix française grave, légèrement réverbérée, **distincte**.
- Bonus facultatif dans le pack : `SW_HorrorAmbience_Original_30s.wav` (musique + bruitages en haute qualité), et `SW_ZombieWood_Foley_30s.wav` (bruitages isolés).

## Installation Unreal 5.8

1. Vérifier qu'il s'agit du bon **AnomaliaZPrigimalia.uproject**.
2. Synchroniser cette PR sur une branche de test **sans fusion non validée**. Il faut une compilation native C++ de `UAnomaliaZPrigimaliaIntroWidget` (MediaAssets déjà ajouté au Build.cs).
3. Activer le plugin **Python Editor Script Plugin** ; exécuter `unreal/Scripts/install_prigimalia_intro.py` dans l'éditeur. Le script vérifie les 3 médias avant de copier, ne remplace jamais une version différente et importe la voix sous `/Game/AnomaliaZPrigimalia/Branding/SW_IntroTitle_Deep_v2`.
4. Tester avec Standalone Game : **30s audio d'horreur → clic / sang coulant / voix → véritable menu**. Tester aussi **PASSER**, média absent, retour au menu, chargement du jeu et sortie.
5. Pour le build distribué Windows, s'assurer que les **deux fichiers MP4** de `Content/Movies` sont inclus lors du packaging.

## Limitations vérifiées

- La musique et les sons sont **une création synthétisée originale**, pas une piste licenciée de Resident Evil. Les grognements et craquements sont générés, non enregistrés à partir de vrais zombies ou planches.
- La vidéo et le sang utilisent du compositing 2D à partir de l'image actuelle du jeu. Ce changement **ne remplace pas le projet de Level Sequence 3D** de la PR #66 (personnage/chien véritablement animés en 3D dans Unreal).
- Depuis ce chat, les médias sont rendus et vérifiables hors Unreal, mais **ni la compilation UE5.8, ni la lecture réelle de MediaPlayer/WMF, ni le packaged build Windows n'ont été testés sur la machine du jeu**.
- La voix grave est encore une voix de synthèse provisoire.
- Cette version est activée uniquement sur la carte solo de démarrage `ANOMALIA_Playable_v1`. Elle ne bloque pas les connexions multi.

## Revenir en arrière

Dans une copie test, retirer l'appel à `UAnomaliaZPrigimaliaIntroWidget::Open` du GameMode et rétablir l'appel direct au menu. Les médias v2 sont isolés. Ne rien supprimer sous `Saved/`.
