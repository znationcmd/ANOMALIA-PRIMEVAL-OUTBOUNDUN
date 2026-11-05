# ANOMALIA'Z PRIGIMALIA — Intro de survie horrifique v4 (88 secondes, SANS TITRE ÉCRIT)

Branche PR #65 — **draft**, non fusionnée à la branche Work. Préserve les 15 cartes, le multijoueur, les sauvegardes et les fichiers de l'éditeur.

## Fonctionnement souhaité

1. Depuis `ANOMALIA_Playable_v1` en solo, afficher le **film animé de 88 secondes**, centré sur le survivant et son berger allemand. **Aucun nom de jeu ou logo textuel n'apparaît.**
2. L'ambiance utilise **une musique d'horreur ORIGINALE**, des grognements synthétiques de zombies et des craquements de bois. **Ce n'est pas la chanson HA HA HA de TheTrapLabb** : un enregistrement tiers non autorisé n'a pas été téléchargé.
3. Pendant les 88 secondes, le bouton **PASSER** permet d'interrompre la vidéo pour aller directement au clic/voix.
4. À la fin, le bouton **CLIQUER POUR COMMENCER** apparaît. Au clic, le bouton disparaît (aucun titre écrit), la vidéo muette de sang coulant de 6 secondes démarre et la **voix gutturale de zombie** prononce **oralement** « ANOMALIA'Z PRIGIMALIA ».
5. Lorsque la voix est terminée, le véritable menu Unreal `UAnomaliaZPrigimaliaSessionWidget` s'ouvre. En cas de média manquant ou d'erreur, retour au menu d'origine.

## Médias v4 à installer

Récupérer le pack `ANOMALIAZ_PRIGIMALIA_KIT_88S_VOIX_ZOMBIE.zip` livré dans la conversation, l'extraire dans le dossier de la copie de test contenant `unreal/AnomaliaZPrigimalia.uproject`. Les médias suivants seront alors présents :

- `unreal/SourceAssets/Intro/ANOMALIAZ_PRIGIMALIA_Intro_SANS_TEXTE_88s.mp4` — cinématique avec audio original 88s.
- `unreal/SourceAssets/Intro/ANOMALIAZ_PRIGIMALIA_Clic_Sang_SANS_TEXTE_v4.mp4` — clip de sang de 6s sans texte ni audio.
- `unreal/SourceAssets/Intro/SW_IntroTitle_Zombie_v4.wav` — annonce grave/gutturale séparée.

Dans **Unreal Engine 5.8**, activer Python Editor Script Plugin, ouvrir le véritable `AnomaliaZPrigimalia.uproject`, exécuter `unreal/Scripts/install_prigimalia_intro.py`, puis compiler le module C++ de la PR. Le script vérifie le projet et tous les médias avant de copier et **n'écrase pas de fichier différent déjà présent**. La voix est importée sous `/Game/AnomaliaZPrigimalia/Branding/SW_IntroTitle_Zombie_v4`.

## Contrôles obligatoires avant toute fusion

- Vérifier dans une build Windows standalone : vidéo 88s sans nom écrit, titre prononcé une seule fois au clic, bruitages audibles, sang visible, bouton PASSER, absence de titre après clic.
- Vérifier le repli menu en cas de média manquant, la sortie d'écran/retour et les profils de sauvegarde inchangés.
- Vérifier que les **deux films MP4** sont dans les médias packagés de `Content/Movies`.
- Ni la compilation native UE5, ni l'export du jeu, ni les tests sur le PC de l'utilisateur n'ont été effectués depuis le chat.
- Le survivant et le chien dans la vidéo sont animés **en compositing 2D** à partir du visuel initial. La véritable séquence animée avec rigs 3D Unreal reste à produire et vérifier : PR #66.
- La voix zombie est une transformation de la voix synthétique existante. Elle est plus gutturale, mais n'est pas un comédien vocal enregistré.

## Droits musicaux

« HA HA HA » de TheTrapLabb est une **référence demandée**, pas une piste incluse dans le pack. Pour commercialiser ou diffuser le jeu avec la chanson entière, obtenir une licence valide portant sur synchronisation et distribution du master. Remplacer la musique originale dans la vidéo seulement lorsque le fichier autorisé est disponible. Ne pas prétendre que le master commercial est déjà inclus.
