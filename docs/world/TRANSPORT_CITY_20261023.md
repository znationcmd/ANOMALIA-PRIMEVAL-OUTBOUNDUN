# Transport et services urbains — 23 octobre 2026

Changements sur `ue5/driveable-roster-city-20261023`, à partir de la branche gameplay `feature/loot-tiers-radiation-config-20261021` (37dbc31). Aucun véhicule terminé supplémentaire ni téléchargement Sketchfab confirmé dans ce changement.

- Catalogue natif : 45 catégories (13 ajouts : NASCAR, rallye, camion de course, pick-up, bus, minibus, dépanneuse, camion-benne, chasse-neige, bateau F1, yacht, tramway, téléphérique). Les catégories utilisent le pawn possédable existant, son carburant, ses commandes et sa réplication. Les modèles 3D correspondants restent à intégrer lorsqu'ils manquent.
- Téléphérique : déplacement serveur sur spline, cabine verticale en pente, freinage et retour à la vitesse de ligne. La spline utilise `AnomaliaRailTrack` et `InitialRailTrack` ; stations, pylônes et câbles visibles restent des assets distincts. Changer pour un train détache la cabine de sa ligne.
- `create_settlement_review.py` : ajoute trois véhicules possédables police/pompiers/ambulance près de leurs services dans la scène urbaine de 28 bâtiments. Leurs meshes doivent avoir été importés et leur empreinte doit correspondre au manifeste Expansion1. Les bâtiments existants sont conservés. Cette scène utilise encore les prototypes originaux du projet, pas une ville photoréaliste validée.
- `configure_archipelago_transport.py` : ajoute une région marine native à la carte existante de 48 × 48 km, toujours chargée avec World Partition. Elle fournit les bornes utilisées par la flottabilité et la plongée ; le paysage conserve ses collisions de fond. Pas de vagues, de nage, de bathymétrie dynamique ni de validation navale multijoueur dans ce lot.

Le workflow `UE5 transport and city services` compile Editor/Game sur l'hôte Windows existant, exige UE5.8, vérifie les nouveaux tests natifs puis exécute les deux scripts. Il ne modifie pas l'installation du jeu sur le PC. Les cartes et assets nécessaires doivent déjà exister sur cet hôte. Les rapports portent le commit testé ; ils ne constituent pas un essai de conduite en jeu.

Vérifications locales : 12 contrôles de portage, 4 tests de placement urbain et scénarios numériques C++ avec UBSan réussis. Unreal Editor absent de l'environnement local : compilation native, importation et playtest ne sont pas déclarés réussis ici.

## Sources supplémentaires pour les services de la ville

Ces pistes sont séparées des assets acceptés. Le statut gratuit/CC BY vient de l'index public, les archives n'ont pas été reçues. Conserver la licence et l'attribution exactes à réception ; contrôler provenance, textures, échelle, intérieur et performances avant intégration.

| Cible | Source | État |
| --- | --- | --- |
| Caserne | [Fire station — Jawws](https://sketchfab.com/3d-models/fire-station-34988c59a010496cacc06d0580a116dd) | CC Attribution affichée ; 16,8 k triangles ; textures, OBJ et FBX annoncés. Modèle simple, rendu photoréaliste à vérifier. |
| Commissariat | [Police Station — Abdallateef Abdalla](https://sketchfab.com/3d-models/police-station-3d-model-b66a480d200149cc83bbc78ab20a0b71) | Page de téléchargement indexée ; page directe HTTP 403. Licence et archive à revérifier avant utilisation. |
| Hôpital | [Hospital — Neo_minigan](https://sketchfab.com/3d-models/hospital-e16d1661b7d44949b52d8dbf44168b14) | Page de téléchargement indexée ; page directe HTTP 403. Licence et archive à revérifier avant utilisation. |
| Ambulance britannique | [Ambulance — silaspaige1998](https://sketchfab.com/3d-models/ambulance-41574a23a9ae4c9d990ffe672af6281e) | CC Attribution affichée ; 41,1 k triangles. Aucune description de provenance ou d'intérieur : candidat à vérifier. |
| Ambulance américaine | [2007 Baird C-Series — Andrew Duong](https://sketchfab.com/3d-models/2007-baird-c-series-ambulance-fcc1aed5629849e6bc6d01bd1ca3c7e6) | CC Attribution affichée ; 27,8 k triangles ; Maya/Substance annoncés. Vitres opaques : décor de fond, inadéquat comme cockpit final. |

Ambulance HSE Irish écartée à ce stade : l'auteur du véhicule d'origine est indiqué comme inconnu. Aucun achat, extraction de jeu tiers ni usage d'une licence non commerciale pour une sortie commerciale.

## Travail restant pour la carte complète

Cette modification ne termine pas la carte : le quartier urbain reste séparé de l'archipel. Restent l'implantation des villes sur le terrain, les réseaux routiers/rail/câble, stations et ports, tous les modèles réalistes sous licence, les intérieurs, la végétation et les circuits demandés. Les véhicules au sol conservent une conduite de prototype, sans suspension Chaos validée ; les places indiquées au catalogue ne prouvent pas un système passagers. Essais UE5.8 nécessaires : entrée/sortie, sol et collisions à l'échelle du modèle, conduite/freinage, routes, eau, rail, streaming et réplication à plusieurs joueurs.
