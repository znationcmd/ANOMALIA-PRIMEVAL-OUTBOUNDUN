# Générique ANOMALIA'Z PRIGIMALIA — introduction cinématique (branche isolée)

Cette intégration est volontairement distincte des cartes et des sauvegardes UE5.

## Fonctionnement prévu

1. Sur la carte de démarrage **ANOMALIA_Playable_v1**, en **standalone/solo uniquement**, le GameMode essaie d'ouvrir la vidéo de 30 secondes.
2. Pendant la vidéo : le bouton **PASSER** coupe la projection.
3. À la fin : le bouton **CLIQUER POUR COMMENCER** apparaît.
4. Au clic : lecture de **SW_IntroTitle** (voix grave prononçant le nom), puis ouverture du véritable **UAnomaliaZPrigimaliaSessionWidget** existant. Ce n'est pas une image de menu.
5. Si la vidéo est absente ou si l'import de voix a échoué : repli sur le menu existant. Aucun profil/joueur/monde n'est supprimé.

## Installation des médias sur la copie Windows

Les binaires MP4/WAV sont fournis **séparément** : ils ne sont PAS poussés en tant qu'assets Unreal par cette PR.

* Décompresser le kit dans le dossier racine de travail qui contient **unreal/AnomaliaZPrigimalia.uproject**. Le ZIP ajoute `unreal/SourceAssets/Intro/`.
* Après avoir synchronisé/compilé cette branche **sans fusion aveugle** des autres travaux, ouvrir **ce projet exact** dans Unreal Engine 5.8.
* Activer le plugin **Python Editor Script Plugin** puis exécuter `unreal/Scripts/install_prigimalia_intro.py` via **Tools → Execute Python Script**. L'installateur vérifie le projet et les fichiers et **refuse d'écraser** un média différent. La voix est importée en `/Game/AnomaliaZPrigimalia/Branding/SW_IntroTitle`; la vidéo est copiée vers `Content/Movies/`.
* Vérifier le packaging Windows : le fichier du dossier `Content/Movies` doit être **staged** dans le build. Pour un build distribué, vérifier la présence du MP4 dans le dossier livré.
* Tester en **Standalone Game** : démarrage → cinématique → clic/voix → vrai menu → jouer; puis refaire le test avec **PASSER**. Vérifier que menu, inventaire et chargements multi-cartes ne régressent pas.

## Points importants / limites vérifiées

* La vidéo jointe anime l'image d'origine en **compositing 2D** (travelling, effets de fumée, mouvement apparent du survivant et du berger allemand) : **elle ne contient pas de modèles squelettiques 3D**.
* Le dépôt référence bien un personnage Survival et des assets/animations de berger allemand, mais cette branche ne les convertit pas en **Level Sequence 3D**; le vrai rendu animé 3D devra être construit et testé sur la copie UE5 contenant ces assets (marche, respiration, orientation du regard, pas du chien), avec validation des rigs et des droits de chaque asset. Ne pas prétendre que cela est déjà fait.
* La vidéo de jeu est la version **instrumentale seule** : ainsi, le titre n'est prononcé **qu'au clic**. La version vidéo déjà livrée avec annonce vocale intégrée reste une bande-annonce/aperçu distinct. La bande-son est originale pour la démonstration. La voix `SW_IntroTitle` est une **voix synthétique provisoire**. La remplacer par un master vocal validé si nécessaire.
* Les tests de compilation UE5, de média WMF Windows, d'affichage en packaging et de lecture du son **nécessitent la machine contenant Unreal**. Aucun test UE5 réel n'a été exécuté depuis ce chat.
* Pour un lancement directement dans un niveau multijoueur, le générique n'est pas activé par ce patch; le serveur et ses profils restent inchangés.

## Revenir en arrière

Retirer/annuler le commit de l'appel à `UAnomaliaZPrigimaliaIntroWidget::Open` dans GameMode pour rétablir l'ancien affichage. Les médias ajoutés sont indépendants. Ne supprimer aucun fichier sous `Saved/`.
