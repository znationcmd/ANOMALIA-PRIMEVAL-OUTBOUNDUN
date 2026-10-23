# ANOMALIA Tools 0.1.0 — suite de création de mods

Application Windows x64 indépendante, séparée de CMD Studio (réservé au propriétaire) et de ANOMALIA Editor (éditeur de cartes). Dans apps/anomalia-tools/ sur une branche dédiée : aucun autre logiciel ni fichier du jeu n'est modifié.

Inspiré des rôles de DayZ Tools : Workbench, Object Builder, Terrain Builder, Central Economy Editor, Addon Builder et Publisher. Aucun code, fichier, texture ou format propriétaire de DayZ Tools n'est copié.

## Modules présents dans la première version

- Workbench : explorateur de fichiers, lecture/édition/sauvegarde de code, JSON, XML, INI et configurations. Pas de compilation C++ ni débogueur Enfusion intégré.
- Object Builder : import de GLB/GLTF/FBX/OBJ/USD, aperçu 3D réellement fonctionnel pour GLB. Pas de modélisation vertex, LOD, rig ou collisions.
- Terrain Builder : génération procédurale de heightmaps PNG 128 à 1024 pixels et metadata JSON. Pas encore de World Partition ou d'import Landscape automatique Unreal.
- Central Economy : fichier Config/economy.json, objets de butin, min/max/chance et validations. Pas encore raccordé au spawn du jeu.
- Texture Tools : import et aperçu PNG/JPEG/WebP et dimensions. Pas de conversion PAA/EDDS.
- Addon Builder : archive ZIP des fichiers du projet, manifeste et empreintes SHA-256. Pas de .pbo ni de .pak UE5 cuisiné.
- Publisher : export local du ZIP à l'emplacement choisi. Pas de publication Steam Workshop ni Epic Marketplace sans intégrations autorisées.

## Vie privée / séparation stricte

Le dossier app.getPath('userData')/private-workspaces est propre au profil Windows de l'utilisateur. Pas de compte commun, serveur de transfert, de synchronisation ni de télémétrie dans cette version.

Les fichiers de chaque projet sont isolés dans un dossier, avec rejet de traversal de chemins et de liens symboliques. Sur un ordinateur partagé avec le MÊME compte Windows, les données seront également visibles aux personnes ayant accès à cette session : utiliser des comptes Windows distincts.

Aucune publication ni export public sans action manuelle de l'utilisateur.

## Lancer les sources sous Windows

Installer Node.js 20+, puis ouvrir un terminal dans ce dossier et exécuter :

    npm install
    npm test
    npm start

Installer Windows depuis les sources :

    npm run package:win

Un installateur Windows est compilé via GitHub Actions et fourni sous forme d'archive ZIP. Le binaire n'est pas signé commercialement.

## Limites

L'édition du code est locale et non exécutable. Les ressources peuvent peser jusqu'à 150 Mo par fichier, aperçu jusqu'à 18 Mo, archives ZIP jusqu'à 250 Mo.

Pour compiler un vrai mod jouable dans ANOMALIA, il faudra un SDK du jeu, des modules Unreal, un workflow de packaging UE5, des versions validées des assets et des tests dans le jeu. Cette première version prépare les données ; elle ne remplace pas Unreal Engine, Blender ou les outils de production professionnels.

Les trois applications restent séparées : CMD Studio, ANOMALIA Editor, ANOMALIA Tools.

## Icône officielle Windows — 0.1.1

Le logo ANOMALIA Tools métallique orange/noir sélectionné est utilisé pour l'exécutable, l'installateur NSIS, les raccourcis du Bureau/menu Démarrer et la fenêtre/barre des tâches Windows. L'icône carrée reprend le symbole A, l'engrenage et les outils croisés du logo original pour rester lisible à petite taille. Le script `npm run prepare:icon` convertit `assets/anomalia-tools-icon.png` en `assets/anomalia-tools.ico` multi-résolutions (16 à 256 px). Réinstaller la version 0.1.1 pour actualiser l'icône. Aucune autre application CMD ou ANOMALIA n'est modifiée.
