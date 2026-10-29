# ANOMALIA’Z PRIGIMALIA — migration du nom

## Identité commerciale

Titre public exact : **ANOMALIA’Z PRIGIMALIA**
Titre technique sans ponctuation : `AnomaliaZPrigimalia`
Nom de distribution Windows : `ANOMALIAZ-PRIGIMALIA`

La migration est réalisée sur une branche distincte du projet existant. Le nouveau nom
est destiné au jeu, aux menus, aux fichiers publics, aux installateurs et aux
outils associés. Les anciens identifiants d'exécution et chemins Unreal doivent
être traités séparément et jamais remplacés par un simple rechercher/remplacer.

## Conserver les données existantes

- `/Script/AnomaliaPrimeval` et les noms des classes C++ sont utilisés par des
  Blueprints et assets ; les modifier nécessite des Core Redirects vérifiés
  sous Unreal Editor 5.8 et une recompilation C++.
- `/Game/Anomalia/*`, les cartes `ANOMALIA_*.umap`, les textures et fichiers
  `.uasset` doivent être renommés **depuis Unreal Editor** avec les redirectors,
  puis *Fix Up Redirectors* et validation des références.
- Les clés de sauvegarde `anomalia-*`, le schéma `anomalia://`, les identifiants
  RPC et les chemins historiques de sauvegarde restent inchangés pour ne pas
  supprimer les parties ou casser le multijoueur.
- Le repo GitHub et les URLs des mises à jour restent l'adresse existante tant
  que le propriétaire n'a pas renommé le dépôt dans les paramètres GitHub.
- Les images binaires JPG/ICO existantes peuvent encore contenir l'ancien
  graphisme ; elles doivent être remplacées et revues par l'auteur, sans
  supprimer les ressources actuelles.

## Vérification Windows et Unreal requise

1. Sauvegarder D:\\ANOMALIA, notamment le projet Unreal, `Saved`,
   `FabImports`, `sketchfab` et les sources non suivies par Git.
2. Fusionner la branche de changement de nom seulement après vérification.
3. Exécuter `python scripts/rebrand-public-identity.py --apply` sur
   un checkout propre si d'autres fichiers textuels portent l'ancien titre.
4. Lancer `npm ci`, `npm test`, `npm run build` et l'installateur Windows.
5. Ouvrir le projet dans Unreal Engine 5.8, recompiler C++, ouvrir cartes et
   Blueprints, vérifier inventaire, DataTables et assets, lancer PIE et
   vérifier les sauvegardes, réseau et manettes.
6. Effectuer plus tard la migration des noms de module / packages à l'aide de
   redirections Unreal, puis reconstruire les exécutables et icônes.
7. Avant commercialisation, terminer les recherches de marques et les licences
   commerciales des assets Fab et Sketchfab.

Ce document ne prétend pas que la migration technique native a déjà été testée.
