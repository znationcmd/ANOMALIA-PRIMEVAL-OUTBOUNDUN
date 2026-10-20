# ANOMALIA — niveau original natif, preuves

Création réelle validée sous Unreal Engine 5.8.3 sur le commit 1b74e33771b82eee3facde5def36e5f0459b1696.
Run : https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/39479732171

- Editor et Game : compilations natives réussies.
- ProfileIsolation, TransportDynamics, VehicleCatalog : tests natifs réussis.
- Carte réellement créée : `/Game/Maps/ANOMALIA_Archipelago_v2`.
- 48 × 48 km, résolution 3025, 576 composants de terrain et 576 composants de collision.
- 145 LandscapeProxy : un Landscape principal et 144 proxies de streaming.
- Mesure analytique indépendante à 25 m : 890,634 km² de terre, sommet 1757,97 m.
- Huit masses terrestres de plus de 1 km² à la résolution d'import.
- Matériau de biomes, surface marine visuelle sans vagues, soleil, atmosphère et point de départ côtier.
- Rapport natif conservé dans `archipelago-created-39479732171.json`.
- Archive Unreal avec .umap, acteurs externes et matériaux : artefact `ue5-archipelago-world`, ID 12291217247, 19 342 101 octets compressés.
- SHA-256 de l'archive Actions : 0ca567ca58c76464a8e22cf84d4a19be3fd37ac5aec70cd72cbce5a33ee5fecd.
- L'archive Actions est conservée 90 jours. La génération reste reproductible à partir du code ; conserver une copie des créations modifiées par les utilisateurs.

Sur le PC du runner : `scripts/ue5/open-archipelago-world.cmd` ouvre le projet correct et cette carte directement. Les anciennes cartes et heightmaps sont conservées. Le brouillon v1 issu d'une tentative échouée n'est pas écrasé.

État prouvé : LEVEL_CREATED_NOT_PLAYTESTED. Le lancement réel du mode Jouer, la marche, les collisions en action et l'inventaire seront vérifiés par le test natif séparé Anomalia.World.ArchipelagoPIE. Le rendu GPU, le multijoueur et les performances ne sont pas validés.

Le test d'inventaire PIE utilise un acteur de test transitoire propre au test pour ne pas modifier un profil joueur chargé. La présence du composant d'inventaire sur le véritable personnage est également vérifiée.

![Aperçu calculé du relief, pas une capture Unreal](ANOMALIA_Archipelago_preview.jpg)

## Éléments encore absents de ce niveau

Ponts, routes, chemins, sentiers, villes, villages, bâtiments RP, ports, bases militaires, aéroport, végétation 3D, navmesh, IA, zombies, animaux, dinosaures et drones pilotables. La présence d'un catalogue ne vaut pas intégration. Ces éléments doivent être ajoutés par lots après validation du niveau en mode Jouer.
