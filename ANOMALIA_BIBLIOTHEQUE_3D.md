# ANOMALIA — Bibliothèque 3D externe, stockage local et packs de jeu

## Objectif
Économiser de l'espace sur le disque de travail, sans supprimer les ressources existantes ni rendre les builds dépendants d'un lien Sketchfab.

**Cette étape est une préparation des dossiers sur Windows, pas une migration automatique des ressources ni un CDN fonctionnel.**

## Configuration initiale sans PowerShell manuel
Exécuter `scripts/ue5/Initialiser_Bibliotheque_3D_ANOMALIA.bat` par double-clic sur le PC Windows. Une boîte Windows permet de choisir un emplacement — idéalement un SSD externe ou secondaire. Le script ne supprime ni ne déplace aucun fichier. Il crée `ANOMALIA_Bibliotheque_3D` et les catégories :
- `01_Originaux/Vehicules`
- `01_Originaux/Personnages_Vetements`
- `01_Originaux/Batiments`
- `01_Originaux/Nature`
- `01_Originaux/Objets`
- `01_Originaux/Textures`
- `02_Licences_Provenance`
- `03_A_Importer`
- `04_Archives_Verifiees`
- `05_Sauvegarde`

L'emplacement choisi est mémorisé localement dans `%LOCALAPPDATA%\ANOMALIA\bibliotheque-3d-chemin.txt` (hors dépôt). **La bibliothèque externe seule ne constitue pas une sauvegarde** : conserver une seconde copie des fichiers importants.

## Flux de production fiable
1. Télécharger seulement les modèles autorisés, en gardant la fiche source et licence, sur l'emplacement externe.
2. Pour importer dans UE 5.8, rendre la source accessible au PC de build (SSD branché ou copie de travail). Le système d'importation Sketchfab existant dans cette PR est **séparé** de cette initialisation : il ne lit pas encore automatiquement le nouvel emplacement.
3. Unreal convertit le modèle en `.uasset` dans `unreal/Content`. Ne jamais enlever les `.uasset` d'une scène ou du projet sans analyser les dépendances. Il faut de la place locale pour les fichiers de travail et le packaging, même si les originaux sont sur disque externe.
4. Ne supprimer un ZIP source que **si** l'import a été validé, la licence enregistrée et une sauvegarde vérifiée. Rien n'est supprimé automatiquement.
5. GitHub public : garder scripts, catalogues et autorisations ; ne pas y pousser automatiquement les archives de tiers, modèles sous licence ou données privées.

## Téléchargement progressif pour les joueurs : étape ultérieure
Unreal Engine 5.8 permet de produire des chunks `.pak` à l'aide d'Asset Manager / Primary Asset Labels et de `Generate Chunks`. `ChunkDownloader` peut télécharger et monter des packs depuis un serveur HTTP et son manifeste. Exemples de catégories : 0 jeu de base ; 1 véhicules ; 2 vêtements ; 3 bâtiments ; 4 cartes/extensions.

**Ce mécanisme n'est pas installé par ce .bat** : il faudra implémenter et compiler le client UE, cuisiner des builds, héberger des packs autorisés, signer/vérifier les fichiers téléchargés, tester leur montage et la gestion des versions. Une connexion Internet est nécessaire pour le téléchargement initial des packs optionnels. Les ressources requises par la scène doivent être déjà présentes ou téléchargées avant leur chargement.

## État réel
- Préparation de dossier et mémorisation locale : créée via script Windows, à tester sur le PC.
- Téléchargement des fichiers 3D Sketchfab : dépend d'une session/autorisation ; **non effectué ici**.
- Import automatique de toute la bibliothèque dans UE 5.8 : **non implémenté**.
- Packs téléchargeables et mise à jour UE en production : **non implémentés / non vérifiés**.
- Jeu Windows Electron/Three.js et système de mises à jour déjà existants : **inchangés**.
- BMW E39, profils, scènes, sauvegardes, branches et modèles existants : **inchangés**.

Documentation Epic officielle :
- https://dev.epicgames.com/documentation/en-us/unreal-engine/cooking-content-and-creating-chunks-in-unreal-engine
- https://dev.epicgames.com/documentation/unreal-engine/setting-up-the-chunkdownloader-plugin-in-unreal-engine
