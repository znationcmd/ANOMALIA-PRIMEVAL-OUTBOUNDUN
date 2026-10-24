# ANOMALIA Editor 0.1 — éditeur de cartes 3D autonome

**Application publique, distincte de CMD Studio (outil privé du créateur).**
Code neuf inspiré du workflow de DayZ Editor, sans copier ni redistribuer le mod DayZ Editor, ses assets ou son système de fichiers. Ce n'est ni un mod DayZ ni le moteur Unreal Engine.

## Fonctionnel dans cette préversion

- Vue 3D navigable en caméra orbitale, sol, grille, ombres, éclairage et inspection.
- Catalogue de 20 objets de démonstration (maisons, immeubles, végétation, véhicules, routes, mobilier) fabriqués avec des géométries **provisoires**, pas avec des modèles AAA.
- Placement et sélection par clic, hiérarchie des objets, propriétés XYZ, rotation et échelle.
- Manipulateurs de déplacement, rotation, échelle ; pas de grille 0,5/1/5 m pour placement ; pinceau de placement.
- Duplication, suppression, annulation/rétablissement, raccourcis clavier.
- Importation de modèles .GLB locaux (limite 14 Mo), intégrés au fichier de projet, sans serveur.
- Sauvegarde automatique et manuelle en IndexedDB **sur l'appareil du visiteur uniquement**, chargement à la prochaine ouverture, export/import JSON .anomalia.json, export positions CSV.
- Aucun système de compte public, aucun catalogue partagé, aucun upload de contenu, aucune télémétrie.

## Vie privée et séparation

Les projets ne quittent jamais le poste de l'utilisateur : ils restent dans la base IndexedDB de son profil navigateur, ou dans les données locales de l'application Electron par utilisateur du système d'exploitation. Le code ne comporte aucune API distante ni téléchargement de bibliothèque depuis l'app. Sur un **ordinateur partagé avec la même session Windows/le même profil navigateur**, il faut utiliser des profils distincts pour isoler les données. Supprimer le profil ou effacer les données du navigateur peut effacer les projets : exporter régulièrement ses cartes JSON.

La publication en ligne est **statique** : servir le dossier dist/ suffit, aucun backend ni base de données commune. Avant d'ajouter une synchronisation cloud, il faudra une véritable authentification et une isolation vérifiée par utilisateur côté serveur.

## Tester en local

Node.js 20+ requis :

    cd apps/anomalia-editor
    npm install
    npm test
    npm run dev

Ouvrir http://127.0.0.1:4174 dans le navigateur.

Pour créer la version statique :

    npm run build

Pour lancer l'application Windows localement après compilation :

    npm run desktop:dev

Sur Windows, installer l'installateur :

    npm run desktop:package

GitHub Actions peut fabriquer l'installateur Windows sur un runner Windows ; le fichier exécutable n'a pas de signature commerciale et n'inclut aucun asset de Bohemia/DayZ.

## Raccourcis

Q sélectionner, W déplacer, E rotation, R échelle, B pinceau, F centrer, Suppr supprimer, Ctrl+D dupliquer, Ctrl+Z annuler, Ctrl+Y refaire, Ctrl+S sauvegarder.

Clic droit + souris = orbite ; molette = zoom ; clic milieu = déplacer la caméra.

## Limites actuelles et prochaines étapes

Le système de sélection et le pinceau placent des objets 3D, mais il n'y a **pas encore** de terrain modifiable, brush de végétation 100k objets, navigation libre FPS, catalogue Workshop ou Fab, streaming World Partition, export natif .umap/.uasset, synchronisation cloud privée, ni format .dze DayZ Editor Loader garanti. Le CSV permet uniquement de préparer l'importation dans Unreal après association des vraies ressources 3D.

Les objets inclus sont des références visuelles. La physique, les comportements de zombies, les constructions persistantes en multijoueur et la compatibilité réelle ANOMALIA/UE5 nécessitent d'autres modules.

## Icône officielle Windows (0.1.1)

Le logo ANOMALIA Editor validé est intégré à l'application sous forme d'une icône Windows multi-résolutions. L'installateur, les raccourcis Bureau/menu Démarrer, la fenêtre et la barre des tâches utilisent cette identité. La source est un recadrage du véritable logo montrant le « A » futuriste et le cube au centre, pour rester lisible à petite taille. La commande `npm run desktop:package` génère automatiquement le fichier ICO 256 px avant la création de l'installateur. Les utilisateurs de la version précédente doivent installer 0.1.1 pour actualiser les raccourcis.

## Version 0.2.0 — interface professionnelle et mises à jour automatiques

**Refonte complète de la véritable application**, sans simulation visuelle :
- Barre supérieure plus soignée : identité ANOMALIA, nom de la scène et commandes clairement séparées.
- Bibliothèque 3D : recherche, catégories, import GLB, hiérarchie avec contraste et sélection améliorés.
- Barre d'outils de la scène : sélection, déplacement, rotation, échelle, pinceau, aimantation, annuler/rétablir et duplication préservés.
- Espace 3D : surfaces plus lisibles, mode actif et indications de caméra, barre de statut.
- Inspecteur : sélection, propriétés, export JSON et CSV avec sections hiérarchisées.
- Panneau « Mises à jour » dans la version Windows seulement ; la version web garde sa confidentialité et ne demande pas de permissions Windows.

**Le rendu PBR Three.js dépend toujours de la qualité des fichiers GLB réellement importés.** Les 20 exemples géométriques sont encore des *objets de démonstration*, pas des véhicules ou bâtiments photoréalistes. Leur remplacement par des modèles professionnels nécessite l'intégration de vraies ressources 3D sous licences adaptées.

### Fonctionnement des mises à jour Windows

Une fois la version **0.2.0** installée, l'application Windows peut vérifier au démarrage (après 12 secondes) et toutes les **6 heures** les nouvelles versions, télécharger une version plus récente en arrière-plan et l'installer automatiquement lorsqu'on ferme le logiciel. Le panneau permet aussi de demander une vérification ou une installation immédiate. Il faut installer 0.2.0 une dernière fois manuellement : 0.1.1 ne contient pas de système de mise à jour.

Canal public exclusivement ANOMALIA Editor (aucun fichier CMD Studio ou ANOMALIA Tools) :
https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/releases/tag/anomalia-editor-latest

L'exécutable cherche `latest.yml` dans les pièces jointes de la release portant ce tag. **Le canal est inactif tant qu'une première release n'a pas été publiée.** Le projet GitHub Actions `.github/workflows/anomalia-editor-release.yml` publiera l'installateur, les empreintes SHA-512 et le manifeste `latest.yml` après création d'un tag Git `anomalia-editor/vX.Y.Z` depuis du code validé ; le manifeste est envoyé en dernier. La publication doit avoir un compte GitHub autorisé.

Sécurité : connexions HTTPS, hachage SHA-512 du binaire via electron-updater, Windows installateur NSIS, pas d'autorisation de baisse de version et pas d'installation depuis les branches en développement. Les exécutables ne disposent **pas encore d'un certificat de signature Authenticode commercial** : il faut le prévoir pour un déploiement public de confiance et accepter qu'un avertissement Windows SmartScreen puisse apparaître. Sans signature de code, ce mécanisme ne constitue pas une chaîne de confiance aussi forte que le ferait une mise à jour signée.

Les scènes des utilisateurs sont enregistrées dans IndexedDB, dans le contexte de leur profil Windows/Electron. La mise à jour n'effectue aucune suppression des données locales. Chaque utilisateur doit toutefois exporter ses créations importantes avant une installation majeure. Les utilisateurs qui partagent un même compte Windows partagent potentiellement l'accès aux données de ce compte.

### Compiler et tester

    cd apps/anomalia-editor
    npm install
    npm test
    npm run desktop:package

La compilation Windows génère `ANOMALIA Editor Setup 0.2.0.exe` et le manifeste de mise à jour `latest.yml` dans `release/` ; seul l'installateur sera partagé par la CI de vérification. Les mises à jour futures passent par le workflow de publication des versions validées.

## Version 0.3.0 — espace de travail professionnel

Deuxième refonte d'ANOMALIA Editor :
- barre d'activité verticale pour ouvrir/masquer bibliothèque et inspecteur ;
- panneaux ajustables par glisser-déposer ou touches fléchées sur le séparateur ;
- mode concentration (plein espace 3D) et retour aux panneaux ;
- bouton de réinitialisation de la disposition ;
- disposition de panneaux conservée **localement** dans `localStorage`, sans modifier les fichiers de scène ni accéder aux autres utilisateurs ;
- barre de transformations avec raccourcis Q/W/E/R/B, aide de navigation et meilleure lisibilité des champs X/Y/Z.

Les fonctions de création 3D et le moteur Three.js ne changent pas. Les ressources géométriques de démonstration restent provisoires : ce travail ne prétend pas remplacer les modèles par des assets photoréalistes. La version 0.3.0 doit être compilée et testée avant publication de son installateur ; les mises à jour automatiques restent conditionnées au canal officiel de distribution.

## Version 0.3.1 — Bibliothèque ANOMALIA synchronisée

Dans ANOMALIA Editor Windows, choisir une seule fois le bouton
« Lier les fichiers ANOMALIA » dans la barre gauche, puis le dossier du
projet Unreal ou celui où Work télécharge les vrais fichiers. Le chemin
est sauvegardé localement. Le logiciel analyse les nouveaux fichiers
toutes les **45 secondes**, sans relancer l'installateur ni copier les
fichiers : véhicules, bâtiments, routes, équipements, végétation,
textures, cartes et secteurs sont classés automatiquement d'après leur
chemin et leurs extensions.

- Modèles GLB réels : ajout volontaire dans la scène avec « Placer »,
  jusqu'à 80 Mo par GLB, pour éviter de superposer tous les modèles.
- Secteurs au format ANOMALIA JSON : ouverture après confirmation et
  sauvegarde de la scène précédente recommandée, jusqu'à 45 Mo.
- Cartes Unreal .umap et ressources .uasset : visibles dans le catalogue,
  mais ouverture uniquement dans Unreal Engine, pas dans Three.js.
- FBX, OBJ, GLTF, USD, BLEND et images : indexés comme sources et à
  convertir si nécessaire pour un placement direct.
- Protection des projets : le scanner ignore liens symboliques,
  Intermediate, Saved, Binaries et node_modules ; aucun fichier du
  jeu n'est déplacé, effacé ou partagé par le catalogue.

**Important :** ANOMALIA Editor reste pour le moment limité à 4 000
objets par scène JSON. La carte Unreal complète avec World Partition
et des dizaines de milliers d'objets doit être compilée et inspectée
dans Unreal Engine. Un inventaire ou un plan théorique (maisons,
végétation, véhicules) ne crée pas automatiquement les vraies cartes
et les vraies ressources 3D.

Work doit réellement déposer/synchroniser les nouveaux fichiers dans
le dossier lié sur le PC. ANOMALIA Editor détectera ces changements,
mais n'importe pas tout le dépôt du jeu à partir d'Internet et ne
télécharge pas d'assets soumis à licence sans autorisation.

Tests : npm install, npm test, npm run build puis npm run desktop:package.

**Optimisation :** les modèles placés depuis la Bibliothèque du jeu sont
référencés par identifiant local plutôt que recopiés en base64 dans chaque
objet. Un même GLB peut être utilisé plusieurs fois avec préchargement
et clonage, ce qui évite de multiplier sa taille dans les sauvegardes.
La scène contenant ces références dépend néanmoins du dossier lié : pour
partager une carte avec une autre personne, fournir aussi les fichiers GLB
correspondants et choisir le dossier correct dans sa version de l'éditeur.
Les modèles GLB importés directement avec le bouton d'import classique
continuent d'être intégrés à la scène comme auparavant.

### Import direct des packs de Work (ZIP)

Un deuxième bouton « Importer un pack 3D ZIP » permet d'importer un ZIP
sur l'ordinateur sans l'extraire manuellement. L'extraction contrôlée
s'effectue dans la bibliothèque privée du profil Windows, avec détection
des collisions et conservation de toutes les anciennes archives. L'éditeur
fusionne automatiquement ces assets avec ceux du dossier Unreal lié,
puis les retrouve toutes les 45 secondes. Les ZIP sont limités à 750 Mo
compressés et 3 Go décompressés ; un modèle individuel à 80 Mo maximum
peut être placé dans la scène, mais davantage nécessite optimisation
ou travail dans Unreal Engine.

Deux archives Work effectivement disponibles le 23 octobre 2026 :
- ANOMALIA_ASSETS_3D_PBR_20261023.zip : 8 modèles GLB PBR réellement
  préparés, crédits inclus ; arbre de 59 Mo, maison, voiture, camion,
  herbe, rocher, sol de forêt et asphalte. Le manifeste de chacun
  des 8 GLB comporte taille et SHA-256. Les textures sont 2K.
- ANOMALIA_Items_Vetements_Batch2_UE5.zip : 104 GLB statiques
  convertis (vêtements, accessoires, argent, etc.), fichiers MakeHuman
  et scripts de préparation. Les 104 fichiers GLB ont une empreinte
  SHA-256 référencée dans conversion-receipt.json.

L'importateur compare automatiquement chaque modèle répertorié aux
empreintes de ces manifestes et refuse un pack altéré. Il n'exécute
aucun script contenu dans les archives. Les licences et crédits sont
conservés. Tous ces GLB restent **des ressources source**, pas des
acteurs Unreal importés, riggés, équipés de collisions ou intégrés dans
le gameplay. Les fichiers de plan de population, y compris
population-plan-NOT-EXECUTED.json, ne sont pas traités comme une
carte existante.

Le fait d'installer ANOMALIA Editor 0.3.1 ne dépose pas automatiquement
les centaines de mégaoctets d'assets sur chaque PC : il faut fournir
les ZIP une première fois sur cet appareil et les choisir dans
l'éditeur, ou synchroniser un dossier local. Les nouveautés suivantes
dans ces dossiers apparaissent automatiquement au catalogue.

## ANOMALIA Editor sur iPhone, iPad et Android (PWA)

La version Web 3D existante utilise maintenant une PWA installable, un cache
hors ligne et une **interface tactile** : les panneaux Bibliothèque et
Inspecteur s'ouvrent par les icônes de gauche et se ferment via l'arrière-plan ;
le viewport est disponible en portrait/paysage, avec les contrôles de caméra
Three.js tactiles et les commandes d'édition habituelles. Les scènes JSON
peuvent être enregistrées/exportées localement dans les limites du navigateur.

`npm install && npm test && npm run build` génère `dist/` pour un
hébergement **HTTPS**. La PWA se met à jour lors de la prochaine connexion,
sans installateur EXE. Pour iPhone/iPad, ouvrir dans Safari puis « Sur
l'écran d'accueil » ; pour Android, ouvrir Chrome puis « Installer ».

**À distinguer** : le catalogue de fichiers locaux `.uasset`, `.umap`
et les imports automatiques par dossier Windows sont **exclusifs à
l'ANOMALIA Editor Windows**. Le navigateur mobile ne peut pas scanner
librement le disque ni afficher une carte World Partition Unreal.
Sur mobile, on utilise les vraies scènes JSON et modèles GLB pris en
charge par la version Web. Les fichiers et projets sont stockés
localement par appareil ; aucune synchronisation automatique entre
profils Windows/iOS/Android n'est encore déployée. Exporter et importer
les scènes pour transférer le travail.

Un service public GitHub Pages (ou autre HTTPS) peut héberger la version Web
si les réglages du dépôt le permettent. La présence du code PWA ne
signifie pas qu'un site est déjà publié.

## ANOMALIA Editor 0.4.0 — World Forge / éditeur d'implantation de type DayZ

Refonte **réelle des fichiers HTML, CSS et JavaScript** pour remplacer le tableau
de bord étroit et les grosses cartes de maquettes par une interface d'édition
de monde : **viewport 3D dominant**, panneau « Objets à placer » à droite
prioritairement consacré aux **vrais assets GLB**, explorateur/inspecteur
rétractable à gauche, barre d'outils compacte, menus Fichier/Édition/Affichage/
Ressources et HUD minimal (coordonnées, outil, FPS).

Fonctions vérifiables dans le code :
- Menus reliés aux commandes existantes, raccourcis Ctrl+N, Ctrl+O, Ctrl+S,
  Ctrl+Z/Y, Ctrl+D et Suppr ;
- Caméra libre : maintenir clic droit et bouger la souris pour tourner ;
  pendant le clic droit, WASD pour se déplacer, Q/E pour monter/descendre,
  Shift accélère, Alt ralentit ; orbite classique toujours disponible ;
- Afficher/masquer la grille et les ombres, centrer la caméra et vue du dessus ;
- Clic sur « Placer » pour un vrai GLB du dossier ANOMALIA : aperçu réel
  3D sur le terrain, puis clic gauche pour valider et activer le gizmo de
  déplacement ; Échap annule le placement ;
- Sélection d'une vieille maison, arbre, voiture cubique ou autre prototype,
  puis « Remplacer par un vrai modèle GLB » et choix de l'asset réel :
  conserve l'ID et les positions/rotations/échelles de l'objet et reste
  compatible avec l'historique Annuler/Rétablir ;
- Commande Affichage → Masquer/afficher les prototypes : n'efface ni les
  créations ni leurs sauvegardes ;
- Les vieux presets géométriques restent disponibles uniquement dans un
  dossier explicitement étiqueté « Formes de démonstration », replié au
  démarrage. Une **nouvelle** scène ne reçoit plus automatiquement la maison
  cubique et la voiture en blocs. Les anciennes scènes locales sont
  restaurées sans effacement.

Ceci s'inspire des **principes de flux de travail** de DayZ Editor (browser
plaçable, liste de scène, barre d'outils, caméras et commandes), sans utiliser
ni republier son code, ses icônes ou ses assets. Le moteur d'affichage est
Three.js : **ce n'est pas DayZ ni l'éditeur Unreal Engine**, et la refonte ne
génère pas par magie des maisons, véhicules ou paysages réalistes. L'utilisateur
doit importer ses modèles GLB sous licences adaptées et la vraie carte
Unreal .umap doit être construite/testée dans UE5. Les scènes ANOMALIA JSON
restent limitées à 4 000 objets ; World Partition demande Unreal Engine.

Le système de mises à jour automatiques Windows existe dans l'application,
mais nécessite encore la publication d'une release officielle compatible
pour mettre à jour la 0.4.0 à distance. Une machine possédant 0.1.1 ou 0.3.x
**ne reçoit pas automatiquement ce nouveau code** sans canal de publication
actif ou installation de la nouvelle version. Vérifier les commandes et le
rendu 3D dans la vraie fenêtre Windows avant de fusionner cette branche.

## ANOMALIA Editor 0.5 — vrai monde Unreal / aperçu de relief

Cette version corrige un point essentiel de la refonte : ANOMALIA Editor était
un éditeur Three.js de **petite scène de démonstration** et non un programme
qui ouvrait automatiquement le véritable monde de jeu. Il ne peut pas charger
directement des `.umap` ni des `.uasset` et ne doit jamais prétendre le faire.

### Vraie carte du jeu (Windows)

Dans le panneau droit « CARTE ANOMALIA / UNREAL 5 », sélectionner
« Lier le projet UE5 » et choisir **le véritable fichier
`AnomaliaPrimeval.uproject`** sur le PC. L'application valide le projet,
répertorie jusqu'à 250 cartes `.umap` dans son dossier Content, conserve le
chemin dans les paramètres privés de l'application, et met à jour cette
liste toutes les **60 secondes**.

« Ouvrir la vraie carte » utilise l'association Windows `.uproject` pour
ouvrir le **véritable Unreal Editor 5** et son projet avec World Partition.
La carte s'ouvre dans **Unreal Engine**, pas à l'intérieur du viewport
Three.js d'ANOMALIA Editor. Il faut que UE5 et les ressources réelles du
jeu soient présents sur ce même PC. Si Windows ne sait pas ouvrir un
`.uproject`, installer/associer Unreal Engine puis relancer.

Le plugin DayZ Editor fonctionne autrement, car il est exécuté dans le
moteur du jeu DayZ lui-même : il peut afficher le monde natif et les
ressources chargées dans ce moteur. Une vraie parité de ce type pour
ANOMALIA nécessiterait un éditeur/in-game tool UE5 intégré au jeu
(ou Pixel Streaming UE5 correctement configuré), et pas un navigateur
Three.js prétendant afficher un fichier Unreal.

### Aperçu de terrains depuis les vrais fichiers

« Charger un relief PNG » accepte une vraie heightmap PNG/JPEG/WebP
de 16 à 8192 px (fichier de 32 Mo maximum), avec échelle 512 m à 4,8 km.
Le moteur Three.js produit un relief 3D maillé avec normales, ombres
et matériaux colorisés **depuis les altitudes réelles de cette image**,
jusqu'à 257×257 sommets. Le rendu est une **prévisualisation** et ne
reproduit pas Nanite/Lumen/World Partition. Il utilise les valeurs
de luminance décodées par le navigateur (precision 8 bits) et n'est
pas adapté comme export final d'un paysage UE5 16 bits.

Dans le catalogue de modèles, tout fichier dont le nom contient
`heightmap`, `terrainheight`, `landscapeheight` ou
`heightfield` au format PNG/JPEG/WebP est reconnu. On peut
l'ouvrir via « Terrain », le recharger lorsqu'il change dans le
dossier associé, et retrouver le relief local après redémarrage,
grâce au cache IndexedDB privé **lié à cette scène**.

Les fichiers `.umap`, les routes du véritable monde Unreal, les
dépendances du paysage et les milliers de bâtiments ne sont pas
automatiquement convertis par ce mécanisme. Ils restent utilisables
et modifiables dans le véritable Unreal Editor.

### Prototypes restaurés

Les scènes précédentes et leurs coordonnées ne sont ni supprimées ni
remplacées. Les maisons/arbres/voitures géométriques provisoires sont
simplement **masqués par défaut** ; un bouton « Voir prototypes » permet
de les réafficher et de sélectionner chaque objet pour le remplacer
par un vrai modèle GLB tout en gardant position/rotation/échelle.

Le panneau DayZ-style est désormais plus compact, avec vue 3D dominante,
inventaire des ressources et panneau du monde réel clairement séparé,
sans reproduction du code ou des assets de DayZ Editor.

Le canal de mises à jour automatiques de Windows doit encore recevoir
des releases officielles signées/validées. Compiler le setup 0.5.0 ne
l'installe **pas** sur l'ordinateur de l'utilisateur ni ne lui pousse
une mise à jour silencieuse tant que cette distribution n'est pas prête.
