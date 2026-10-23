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
