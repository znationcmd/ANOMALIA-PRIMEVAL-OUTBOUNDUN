# CMD Studio — Game Creator (MVP Windows)

Atelier 3D **local**, indépendant d'ANOMALIA, embarqué dans ce dépôt sans modifier les fichiers du jeu. Ce MVP est du code opérationnel et non un jeu complet ni une suite comparable à Enfusion Workbench.

## Ce qui fonctionne dans cette version

- Application de bureau Electron avec navigation, tableau de bord et bibliothèque 3D locale persistante.
- Importation de fichiers .blend, .fbx, .obj, .glb, .gltf, .usd/.usdz et de textures depuis ton PC. Calcul SHA-256, copie sécurisée, détection des doublons.
- Recherche de modèles via **Poly Haven** (API publique) et **Sketchfab** (API de recherche publique).
- Téléchargement Poly Haven CC0 pour les fichiers individuels reconnus (limite 350 Mo). Les archives, textures séparées ou dépendances complexes ne sont pas encore traitées.
- Lien vers la fiche officielle des modèles Sketchfab. **Téléchargement Sketchfab via OAuth non développé** : une session Sketchfab dans Chrome ne peut pas être réutilisée silencieusement.
- Pont local Blender : conversion de plusieurs formats vers GLB, avec Blender installé.
- Pont local Unreal 5.8 : commande Python d'importation automatique vers /Game/CMDStudio du projet Unreal choisi.
- Association d'un ou plusieurs projets Unreal .uproject. Les projets originaux ne sont pas modifiés lorsque tu les ajoutes.

## Installer sur un PC Windows 11

1. Installer Node.js LTS (>= 20), Blender et Unreal Engine 5.8.
2. Télécharger les sources du dépôt, ouvrir un terminal dans tools/cmd-studio.
3. Exécuter : npm install
4. Exécuter : npm start
5. Dans Paramètres, sélectionner blender.exe puis UnrealEditor-Cmd.exe. Dans Mes projets, sélectionner unreal/AnomaliaPrimeval.uproject situé **sur ton PC**.
6. Activer dans Unreal le plugin **Python Editor Script Plugin** avant une importation automatique.

Pour créer un installateur Windows depuis un ordinateur Windows : npm run package:win.

**Icône Windows (depuis la version 0.1.1)** : le véritable logo CMD Studio est intégré dans `resources/cmd-studio.ico`, dans l'exécutable Windows, l'installateur NSIS, les raccourcis Bureau/menu Démarrer et la fenêtre. L'icône est embarquée automatiquement lors de la construction avec GitHub Actions. Réinstaller la nouvelle version pour remplacer les anciens raccourcis. L'installateur n'a pas de signature commerciale vérifiée.

L'installateur Windows précompilé est disponible dans les artefacts du workflow GitHub Actions `CMD Studio - tests & Windows` lorsque la compilation est réussie.

## Sécurité et licences

- Pas de clé API ni identifiant demandé. Ne jamais ajouter de mot de passe ou token aux fichiers GitHub.
- Application Electron isolée (contextIsolation, sandbox, pas de Node dans la page), appels IPC limités.
- Les scripts s'exécutent localement depuis un chemin de programme que tu as choisi ; ils peuvent manipuler le modèle et le projet. Préférer des fichiers de sources fiables, conserver une copie de sécurité des projets.
- Les modèles téléchargés via Poly Haven sont CC0. Chaque modèle Sketchfab conserve sa licence affichée ; l'utilisateur doit vérifier ses droits pour les autres sources.
- Les données et catalogues locaux sont conservés dans le répertoire de données de CMD Studio (Electron appData), pas envoyés sur Railway.

## Tests

npm test

Les tests valident le catalogue local, la persistance, les doublons, la sélection des projets et les erreurs. Les importations dans Unreal et Blender nécessitent une machine Windows équipée : **elles ne sont pas validées par les tests unitaires**.

## Étapes ultérieures

Authentification Sketchfab OAuth2 approuvée et téléchargement des modèles autorisés, import des textures et archives dépendantes, vraie prévisualisation 3D, shaders PBR, modèles riggés, import Fab depuis son intégration Unreal, CMD World Editor, outils de mods, pipeline CI pour Windows, connexion contrôlée à CMD NEURIA et CMD Hosting.

Ne pas supprimer ni remplacer les assets, maps ou branches d'ANOMALIA pour installer CMD Studio.

## CMD Studio 0.2.0 : refonte premium et véritable aperçu 3D

Toutes les pages Electron sont retravaillées : accueil, recherche 3D,
bibliothèque, projets, outils connectés et paramètres. La nouvelle interface
noir/bleu/violet intègre des visuels paysagers photographiques d'ambiance
pour rappeler ANOMALIA. Ces photographies Unsplash ne sont PAS des captures
d'ANOMALIA. Elles nécessitent Internet ; les dégradés locaux restent
disponibles hors ligne.

**Visionneuse locale 3D réelle :** affichage des fichiers GLB (24 Mo max)
avec leurs maillages et textures PBR, rotations et zoom, environnement
de réflexion, ombres et animation si présentes. La scène fonctionne avec
Three.js embarqué, sans téléchargement de moteur supplémentaire lors
de l'utilisation. Les textures PNG/JPEG s'affichent aussi dans une
vue 3D. Le nombre de triangles est calculé sur le modèle réel.

Les formats FBX/OBJ/BLEND doivent être convertis avec Blender en GLB
pour être inspectés dans ce nouveau viewport. Aucun fichier d'origine
n'est modifié par la visionneuse. Le rendu dépend de la qualité des
véritables ressources fournies : un maillage cubique ne devient pas
automatiquement photoréaliste.

### Compilation Windows

    cd tools/cmd-studio
    npm install
    npm test
    npm run build:viewer
    npm run package:win

Le visualiseur et toutes ses dépendances sont assemblés dans le paquet
Electron. GitHub Actions teste le bundle puis compile le nouvel
installateur CMD Studio 0.2.0. Les anciennes versions restent intactes.

### Limitations explicites

Le viewport n'est pas Unreal Engine : Nanite, Lumen et World Partition
doivent être vérifiés dans UE5. Sketchfab reste limité à la recherche
publique et à l'ouverture de la fiche officielle, sans OAuth.
Poly Haven conserve son système de téléchargement et peut nécessiter
des traitements manuels pour les modèles complexes.

CMD Studio demeure un projet distinct de ANOMALIA Editor et ANOMALIA
Tools. Les projets et assets locaux restent privés au profil Windows.

## CMD Studio 0.2.1 — mises à jour automatiques privées

La version Windows de CMD Studio comprend dorénavant un système de mises à jour
automatiques : recherche au démarrage (12 secondes après le lancement), puis
toutes les **6 heures**, téléchargement en arrière-plan, indicateur de
progression dans Paramètres et installation en fermant normalement le studio.
Un bouton « Vérifier maintenant » et un bouton « Installer et redémarrer »
permettent de déclencher le processus manuellement si souhaité.

La version **0.2.1 doit être installée une fois** sur le PC. Les versions 0.2.0
et antérieures n'incluent pas cet updater : elles ne peuvent pas se mettre à
jour elles-mêmes. L'updater ne modifie pas le dossier de projets ni les
données utilisateur (app.getPath('userData')).

### Activation du canal privé

Le dépôt source GitHub actuel est public, alors que CMD Studio est une
application personnelle. Les artefacts Actions ne constituent pas un flux
d'updates privé. **Ce mécanisme ne publie donc rien sur GitHub Releases.**
Les mises à jour automatiques restent indiquées comme « Configuration
requise » tant que le serveur privé ci-dessous n'est pas déployé.

1. Héberger le serveur Node inclus dans
   `tools/cmd-studio/private-update-server.cjs` derrière un vrai domaine HTTPS
   (Railway ou hébergement déjà possédé) et un stockage persistant.
   Variables requises :
   - `CMD_STUDIO_UPDATE_STORAGE` = dossier de stockage persistant.
   - `CMD_STUDIO_UPDATE_READ_TOKEN` = jeton aléatoire de lecture, 20 caractères
     minimum, réservé au PC utilisateur.
   - `CMD_STUDIO_UPDATE_WRITE_TOKEN` = **jeton différent** de publication,
     réservé au pipeline GitHub, jamais au PC de l'utilisateur.
   - `PORT` = port du serveur (injecté automatiquement par la plateforme).
2. Dans GitHub Actions, configurer les secrets
   `CMD_STUDIO_PRIVATE_FEED_URL` (ex. adresse HTTPS se terminant par
   `/updates/cmd-studio/`), `CMD_STUDIO_PRIVATE_FEED_WRITE_TOKEN`
   et `CMD_STUDIO_UPDATE_SIGNING_KEY_PEM`. Cette dernière valeur doit
   être **la vraie clé privée Ed25519** correspondant à la clé publique
   intégrée à `update-policy.cjs`. Ne jamais ajouter de clé privée dans
   le code, dans les logs ou dans un artefact public.
3. Un tag `cmd-studio/vX.Y.Z` déclenche
   `.github/workflows/cmd-studio-private-update-release.yml` : tests,
   signature des manifestes, compilation NSIS et publication des fichiers
   uniquement sur le serveur HTTPS privé. Le fichier `latest.yml` est
   publié **en dernier**, pour ne pas pointer vers un installateur absent.
4. Dans CMD Studio installé, ouvrir Paramètres puis
   « Mises à jour automatiques », saisir la même URL privée et le jeton
   **de lecture**, et cocher l'activation. Le jeton est chiffré localement
   via `safeStorage` d'Electron (profil Windows), jamais renvoyé à
   l'interface en clair.

**Sécurité** : les manifestes de mise à jour doivent être signés en Ed25519,
vérifiés par une clé publique embarquée dans le programme et les fichiers sont
vérifiés par SHA-512. Le serveur refuse tout accès sans jeton ; l'application
n'accepte que les flux HTTPS avec authentification. La chaîne de publication
refuse une clé de signature ne correspondant pas à la clé publique embarquée.

**Limites actuelles** : le serveur privé n'est pas encore déployé et les
secrets GitHub ne sont pas encore configurés. Il serait faux de prétendre
que ton PC se met déjà à jour tout seul. Le binaire 0.2.1 fournit la
fonctionnalité prête à activer quand l'hébergement privé est opérationnel.
Le Windows installer actuel n'est pas signé par un certificat commercial
Authenticode : SmartScreen peut demander une confirmation et le déploiement
professionnel bénéficierait d'une signature Windows dédiée. Ne jamais
désactiver la vérification cryptographique des manifests simplement pour
faire passer une publication.
