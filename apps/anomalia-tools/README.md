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

## ANOMALIA Tools 0.2.0 — interface professionnelle et mises à jour Windows

Le **véritable logiciel Electron** a été modernisé intégralement, avec un design
graphite et cuivre/orange assorti au logo ANOMALIA Tools. L'interface comprend
désormais une barre latérale plus structurée, un nouvel accueil, des compteurs
réels de projets et de fichiers, des cartes de modules plus lisibles, ainsi
qu'une présentation unifiée du Workbench, des modèles 3D, des terrains, de
l'économie, des textures et des pipelines ZIP.

Les commandes existantes et leurs API locales sont conservées. Les outils ne
sont pas simulés : les limites fonctionnelles indiquées dans chaque page
subsistent. Les modèles 3D GLB conservent leur prévisualisation réelle sous
Three.js ; les autres formats et les heightmaps ne deviennent pas
automatiquement photoréalistes.

### Mises à jour automatiques

**ANOMALIA Tools pour Windows**, à partir de 0.2.0, interroge son propre
canal de publication officiel 12 secondes après le lancement puis toutes
les **6 heures**. Lorsqu'une nouvelle version est disponible, le téléchargement
s'effectue en arrière-plan. Après téléchargement, l'installation se produit
lorsqu'on ferme normalement le logiciel, ou avec le bouton d'installation
dans la nouvelle page « Mises à jour ». La version 0.1.1 doit être mise à
jour manuellement une dernière fois vers 0.2.0.

Canal public de ANOMALIA Tools uniquement :
https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/releases/tag/anomalia-tools-latest

La publication est gérée par le workflow
`.github/workflows/anomalia-tools-release.yml`, lancé à la création d'un
tag `anomalia-tools/vX.Y.Z` pour une version contrôlée. Il compile et teste
l'application, charge le Setup et les fichiers blockmap, puis publie
`latest.yml` **en dernier**. Les fichiers et identifiants de CMD Studio et
ANOMALIA Editor restent totalement distincts.

**Activation réelle :** le canal `anomalia-tools-latest` doit d'abord
exister et contenir un installateur et un manifeste valide. Sans cette
première publication, les vérifications afficheront une erreur non bloquante
et aucune installation automatique n'aura lieu. Les utilisateurs doivent
conserver leurs propres sauvegardes avant une mise à jour majeure.

**Sécurité :** HTTPS via GitHub Releases, empreintes SHA-512 vérifiées par
electron-updater et impossibilité de revenir à une version plus ancienne
par la fonction automatique. Les installeurs Windows ne disposent pas encore
d'une signature commerciale Authenticode. Leur acceptation par SmartScreen
et leur mise à jour doivent être validées sur une vraie machine Windows ;
une empreinte seule ne remplace pas une signature Authenticode de confiance.

### Validation

    cd apps/anomalia-tools
    npm install
    npm test
    npm run build
    npm run package:win

La compilation Windows de la branche de développement produit un fichier
d'installation manuel en artefact GitHub Actions. Il ne publie aucune
mise à jour publique sans tag de version. Aucun fichier d'autres
utilisateurs ou des autres applications CMD/ANOMALIA n'est modifié.

## Mod UE5 natif : ANOMALIA Tools (version de développement)

Dans Addon Builder, le bouton « Créer / vérifier le plugin UE5 » génère un squelette réel de plugin Unreal dans Plugins/ANM.../ (descripteur .uplugin, module C++ et Build.cs). Les fichiers existants ne sont jamais écrasés.

« Vérifier environnement » contrôle le projet et RunUAT.bat d'Unreal Engine. « Compiler le plugin sur ce PC » lance explicitement RunUAT BuildPlugin pour Win64 après confirmation de l'utilisateur ; le code C++ du mod est alors compilé localement. Le poste Windows doit disposer d'Unreal Engine compatible, de Visual Studio et des SDK.

Un succès de BuildPlugin signifie seulement que le plugin a été compilé. Il ne signifie PAS que les assets ont été cuisinés pour ANOMALIA, ni que le jeu possède un chargeur de mods, ni que le multijoueur est compatible. L'import GLB/FBX existant ne crée pas de .uasset : ces ressources doivent être importées dans Unreal Editor puis cuisinées avec le jeu cible.

Le ZIP produit par l'Addon Builder classique reste une ARCHIVE DE SOURCES. Il n'est pas présenté comme un mod jouable. Les sources de chaque utilisateur restent privées et locales. Compiler uniquement des mods de confiance : du C++ provenant de tiers peut être dangereux.

Validation : npm test et npm run build vérifient la logique et l'interface, mais la compilation de vrais mods reste à tester sur Windows avec Unreal Engine installé, puis en jeu après développement d'un chargeur ANOMALIA.

## ANOMALIA Workshop 0.2.4 — interface reliée aux vrais mods locaux

- Onglet Workshop aux couleurs ANOMALIA, fond volcanique original, recherche, catégories, cartes et bibliothèque « Mes mods ».
- Les fiches proviennent exclusivement des vrais projets locaux de l'utilisateur. « Ajouter au Workshop » crée ou met à jour Config/workshop.json. Aucun chiffre communautaire fictif.
- Les abonnements locaux et les états activé/désactivé sont conservés dans le fichier privé _workshop/library.json sous les données ANOMALIA Tools.
- « Préparer le mod » exige un plugin UE5 compilé et son rapport de build par Addon Builder ; les fichiers sont vérifiés puis copiés dans _workshop/installed.
- Un bouton Workshop · Mods dans le menu du jeu Windows tente d'ouvrir ANOMALIA Tools via le protocole sécurisé anomalia-tools://workshop. La version navigateur explique que la liaison Windows n'est pas accessible.
- La version 0.2.4 installe le gestionnaire de protocole sur Windows et assure la mise à jour automatique depuis le canal anomalia-tools-latest.

### Limitations encore visibles dans l'interface

Le Workshop est connecté à l'atelier ANOMALIA Tools, **pas encore au chargeur UE5 du jeu, à ANOMALIA Editor ni à un service communautaire en ligne**. « Préparé » signifie uniquement copié dans la bibliothèque locale : aucun chargement runtime, installation serveur, multijoueur, signature de contenus tiers ou synchronisation distante n'est démontré. Les utilisateurs doivent vérifier les droits de distribution de leurs créations. Le bouton du menu du jeu dépend d'une nouvelle compilation/installation du jeu Windows.

### Vérification

npm test, npm run build, npm run package:win, puis tester sous Windows : créer un projet, créer une fiche Workshop, s'abonner, compiler un plugin avec une installation UE5 compatible, le préparer, et ouvrir le Workshop depuis le bouton Mods du jeu.
