# ANOMALIA'Z PRIGIMALIA — Générique original, 30 secondes maximum

PR GitHub #65 — branche de test **non fusionnée**. Préserve les cartes, les sauvegardes et le travail de Work.

## Fonctionnement

- **24 premières secondes :** la scène VISUELLE DE LA VIDÉO D'ORIGINE ENVOYÉE par l'utilisateur (survivant, chien, ville) avec ajout d'une musique originale horrifique et des bruitages de zombies et de bois qui craque. Ne pas remplacer le décor par une image générée artificiellement.
- **À la fin de ces 24 secondes, ou plus tôt via PASSER :** bouton **CLIQUER POUR COMMENCER**.
- **Au clic :** jusqu'à 6 secondes de sang coulant sur la scène de départ ; déclenchement du **son vocal directement extrait de la vidéo originale** (pas de doublage robotique, pas de pitch modifié). Le menu natif du jeu s'ouvre à la fin du son.
- **Durée totale de la démonstration MP4 : 30.000 secondes**, avec un clic simulé au temps 24s. Dans l'expérience interactive, un clic anticipé réduit la durée plutôt que de l'allonger.

## Pack média à télécharger séparément

Le ZIP `ANOMALIAZ_PRIGIMALIA_KIT_ORIGINAL_30s_CLIC.zip` livré dans la conversation contient :

- `INTRO_JEU_24s_MUSIQUE.mp4` — images originales, musique et bruitages d'horreur, aucune voix de synthèse.
- `CLIC_SANG_6s_SANS_AUDIO.mp4` — coulées de sang, scène originale.
- `VOIX_ET_SON_ORIGINAUX_NON_MODIFIES.wav` — bande audio EXTRAITE du MP4 original reçu, sans changement de timbre ni de hauteur. Elle contient les sons originaux autour de la voix, car elle n'est pas isolée par stem.
- `OUVRIR_GENERIQUE_CLIC.html` — aperçu où le bouton déclenche réellement l'animation et l'audio, séparément du MP4 de démonstration.
- `LISEZ_MOI.txt`.

## Installation UE5.8

Décompresser les trois médias sous `unreal/SourceAssets/Intro/` dans une **copie test** du projet `unreal/AnomaliaZPrigimalia.uproject`. Sur la branche PR #65, exécuter le script `unreal/Scripts/install_prigimalia_intro.py` dans Unreal Editor avec Python Editor Script Plugin. Il refuse d'écraser un média existant différent, copie les deux MP4 dans `Content/Movies`, et importe l'audio original en SoundWave sous `/Game/AnomaliaZPrigimalia/Branding/SW_IntroTitle_Original_v5`.

Tester compilation native, playback MediaPlayer, fin de vidéo, clic, fin de l'audio, transition dans le **vrai menu**, puis packaging Windows. Tous ces tests UE5 restent à faire sur le PC contenant le jeu. Le script n'a pas été exécuté sur ce PC depuis ce chat.

## Limites

- Le rendu animé du personnage et du chien provient encore des images du MP4 d'origine. Il n'est pas une animation squelettique 3D exportée depuis Sequencer (travail séparé de la PR #66).
- Le MP4 d'origine comporte déjà des éléments de texte/logos : ils sont préservés pour ne pas modifier le visuel demandé. Aucun titre supplémentaire n'est introduit.
- La musique de TheTrapLabb **n'est pas incluse** : les nouvelles pistes sont originales, en l'absence d'une licence de synchronisation/master.
- Les fichiers binaires audio/vidéo doivent être importés depuis le ZIP ; les commits GitHub contiennent le code et l'installateur, pas le master commercial ni un build Unreal testé.

## Retour arrière

L'appel d'introduction depuis GameMode peut être retiré dans une copie test afin de revenir au menu standard. Ne jamais supprimer les fichiers `Saved/` ni les 15 cartes.
