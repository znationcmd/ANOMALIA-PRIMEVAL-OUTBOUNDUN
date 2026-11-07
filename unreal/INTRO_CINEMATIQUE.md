# ANOMALIA’Z PRIGIMALIA — Générique original complet, UN SEUL MP4 de 35 secondes

## Source unique approuvée

**Un seul fichier vidéo et audio, et non un kit de plusieurs clips :**

`ANOMALIAZ_PRIGIMALIA_GENERIQUE_35s_ALERTE_ROUGE.mp4`

- Durée réelle vérifiée avec ffprobe : **35.000 secondes**, 30 images/s.
- Vidéo H.264 910 × 512, audio AAC stéréo 44,1 kHz, le tout intégré dans le **même fichier MP4**.
- Taille : **6 881 352 octets**.
- SHA256 exact : `29e4f8c5f00a08877e49fa856707755e0cd257eead26d4c411a38e1960403ccf`.
- Google Drive : `ANOMALIAZ/04_Intro_Installation/ANOMALIAZ_PRIGIMALIA_GENERIQUE_35s_ALERTE_ROUGE.mp4`.

La musique originale du générique, la voix originale au clic, le sang et l'écran d'urgence rouge/jaune sont **déjà assemblés dans ce fichier** : 24s + 6s + 5s = 35s.

## Fonctionnement dans le vrai jeu UE5

Le widget C++ existant `UAnomaliaZPrigimaliaIntroWidget` est maintenant programmé pour :

1. Lire le **seul MP4 complet** depuis `Content/Movies` au lancement.
2. À environ **24 secondes**, mettre en pause **le même MP4** en affichant « CLIQUER POUR COMMENCER » ; le joueur reste sur ce point tant qu'il n'a pas cliqué.
3. Après le clic, reprendre **ce même MP4** pour jouer directement la voix originale, le sang de 6 secondes et le message rouge de 5 secondes, sans ouvrir de deuxième fichier et sans importer un SoundWave séparé.
4. À la fin du MP4, ouvrir le **vrai** `UAnomaliaZPrigimaliaSessionWidget`.
5. Le bouton **PASSER** saute seulement les 24 secondes d'introduction pour rejoindre la pause avant le clic et conserve donc la voix/le sang/le message rouge.

Note : les **35 secondes correspondent à la durée de lecture cumulée**. Le temps d'attente du joueur sur « CLIQUER POUR COMMENCER » n'est pas compris dans ces 35 secondes.

## Installation réelle et état vérifié

La nouvelle installation est le workflow GitHub `.github/workflows/prigimalia-unified35-real-game.yml` (run **42349330900**, succès).

Le runner Windows `ANOMALIA-PC` a vérifié le hash du MP4 et copié le fichier unique dans :

`D:\ANOMALIAZ-PRIGIMALIA\unreal\Content\Movies\ANOMALIAZ_PRIGIMALIA_GENERIQUE_35s_ALERTE_ROUGE.mp4`

Il a mis à jour **uniquement** les deux sources du widget natif :

- `Source/AnomaliaZPrigimalia/AnomaliaZPrigimaliaIntroWidget.cpp`
- `Source/AnomaliaZPrigimalia/AnomaliaZPrigimaliaIntroWidget.h`

Une sauvegarde précédente est conservée dans :

`D:\ANOMALIAZ-PRIGIMALIA\unreal\Saved\IntroInstall\Unified35-42349330900`

Les anciens fichiers médias séparés n'ont pas été supprimés pour éviter toute perte d'origine, mais **la nouvelle version du widget ne les lit plus**. Les anciens workflows d'installation des médias séparés ont été retirés.

**IMPORTANT : les sources et le MP4 sont correctement transférés au vrai projet, mais le C++ n'a pas encore été recompilé et aucune exécution du jeu n'a été testée.** Il faut une compilation native UE5.8 et un test du clic, du son, du menu et du fichier MP4 dans le build Windows avant de déclarer l'installation entièrement jouable. Les sauvegardes et les cartes ne sont pas modifiées.

## Vérification Windows requise

- Espace C: et D: suffisant avant de lancer UnrealBuildTool.
- Compiler `AnomaliaZPrigimaliaEditor` sur Win64, puis si besoin le module de build du vrai jeu.
- Confirmer que le vrai MP4 se joue sans décalage ou coupure audio, et qu'à 24s la pause et le clic fonctionnent.
- Confirmer que le menu natif s'ouvre automatiquement à 35s (hors durée de pause).
- Vérifier que les cartes, les sauvegardes et les fonctions Work restent inchangées.
