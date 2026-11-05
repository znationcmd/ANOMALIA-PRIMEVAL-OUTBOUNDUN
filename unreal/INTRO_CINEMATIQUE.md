# ANOMALIA’Z PRIGIMALIA — Générique original + écran rouge d'urgence avant menu

**Intégration au vrai projet Unreal Engine 5.8** (PR #65, branche distincte de Work).

## Chronologie exacte

1. **Lancement :** 24 secondes de générique avec le survivant, le berger allemand, la musique originale d'horreur et les bruitages. Le bouton **PASSER** permet de déclencher la suite avant la fin de l'intro.
2. **Après clic ou PASSER :** lecture **exacte et non retouchée** du clip `ANOMALIAZ_PRIGIMALIA_Clic_Sang_6s.mp4` fourni par l'utilisateur, avec la voix originale `VOIX_ET_SON_ORIGINAUX_NON_MODIFIES.wav` déclenchée au même moment. Attendre la **fin du sang ET de la voix**, pas seulement l'un des deux. Ne pas générer de nouvelle voix ou de faux sang.
3. **Après le sang et la voix :** afficher **5 secondes** l'écran rouge approuvé « Système d'urgence intégré », écriture jaune, avec le texte « Anomalia’z » et le logo circulaire modifié (aucune mention « AMERICA »).
4. **Après l'écran rouge :** ouvrir automatiquement le **véritable** `UAnomaliaZPrigimaliaSessionWidget` et permettre au joueur de démarrer le jeu.

**Durée nominale : 24 + 6 + 5 = 35 secondes**, si le joueur attend la fin des 24 secondes avant de cliquer. Un clic anticipé réduit la durée. L'écran rouge joue toujours 5 s après la fin du sang et de la voix.

## Médias transmis dans le chat

Pack version finale : `ANOMALIAZ_PRIGIMALIA_INSTALLATION_VRAI_JEU_ALERTE_35s_v2.zip`, contenant exactement :

- `INTRO_JEU_24s_MUSIQUE.mp4`
- `ANOMALIAZ_PRIGIMALIA_Clic_Sang_6s.mp4` — clip sanguinolent fourni, fichier préservé, copie SHA256 `e9c7b9659babf09bae103b508a2982c528173c6b5a3c1ac34dcfb19cd3900a15`
- `VOIX_ET_SON_ORIGINAUX_NON_MODIFIES.wav` — bande vocale extraite de la vidéo initiale
- `ANOMALIAZ_Alerte_Rouge_5s.mp4` — export sans son, 5 secondes de l'image rouge/jaune choisie
- `ANOMALIAZ_Ecran_Urgence_Rouge_Original.png` — image approuvée et source de l'export
- `INSTALLER_DANS_LE_VRAI_JEU.ps1`, `LISEZ_MOI_INSTALLATION_VRAI_JEU.txt`

Copie vérifiée sur le Google Drive relié au PC : `ANOMALIAZ/04_Intro_Installation/ANOMALIAZ_PRIGIMALIA_INSTALLATION_VRAI_JEU_ALERTE_35s_v2.zip`. Le workflow de déploiement associé est `.github/workflows/prigimalia-install-final-intro-30s.yml` (nom historique, **installation mise à jour pour 35 s**).

## Installation réelle sur ANOMALIA-PC

- Runner Windows self-hosted `ANOMALIA-PC` / UE5.8. **Ne pas interrompre City Sample ni lancer deux modifications concurrentes.**
- Le workflow vérifie le `D:\\ANOMALIAZ-PRIGIMALIA\\unreal\\AnomaliaZPrigimalia.uproject`, la copie source `D:\\ANOMALIA`, son marqueur de sauvegarde, la disponibilité et le SHA256 du pack Google Drive, et l'absence de processus bloquants.
- Il accepte un widget Unreal encore absent, le widget version précédente validée, ou le widget de cette version. **Toute différence non reconnue provoque un arrêt plutôt qu'un écrasement de Work.**
- L'installateur réalise une sauvegarde, copie les trois MP4 dans `Content/Movies`, importe le fichier audio en `/Game/AnomaliaZPrigimalia/Branding/SW_IntroTitle_Original_v5`, met à jour C++/GameMode et compile `AnomaliaZPrigimaliaEditor` et `AnomaliaZPrigimalia`.

## Validation à effectuer

La bande-annonce vidéo démonstrative 35 secondes est rendue et téléchargeable dans la conversation. **Le jeu Unreal n'est PAS déclaré installé tant que le job Windows ne termine pas**, et ne sera déclaré fonctionnel que lorsque l'ouverture réelle du jeu et du menu aura été vérifiée.

Après le job, vérifier dans le jeu :
- Le bouton PASSER, le clic, l'annonce vocale intacte et **l'effet sanguin exact**.
- L'alerte rouge apparaît **uniquement après** la voix et le sang, reste 5 secondes entières, puis le vrai menu fonctionne.
- La carte d'accueil, les sauvegardes, le multijoueur et les quinze cartes restent intacts.
- Les trois MP4 sont copiés dans un véritable build Windows packagé.

Les fichiers MP4 utilisent du compositing 2D ; aucune animation squelettique Unreal du chien ou du personnage n'est prétendue complète. La piste commerciale TheTrapLabb n'est pas incluse, faute de master avec droits d'utilisation.

## Retour arrière

Les sauvegardes avant installation sont conservées dans `Saved/IntroInstall`; ne jamais supprimer les fichiers `Saved/` de joueur.
