# UNKNOWN HORROR X — faune et créatures originales

**Ajout au catalogue gameplay** : zombies, animaux sauvages et dinosaures en **surface ET en souterrain**, sans lien avec Resident Evil.

| Couche | Apparitions prévues |
|---|---|
| Surface | Zombies vagabonds/coureurs/colosses, cerfs, sangliers, loups, ours, dinosaures herbivores et carnivores |
| Métro −1 | Zombies, chauves-souris, rats, sangliers/loups et petits dinosaures prédateurs |
| Laboratoires −2 | Zombies contaminés, chauves-souris, rats et deinonychus |
| Ville souterraine −3 | Zombies, animaux cavernicoles, raptors, carnivores et herbivores |
| Grottes profondes −4 | Zombies mineurs/colosses, ours, crocodiles cavernicoles, carnivores et dinosaures |

**Code** : `src/unknown-horror-x-creatures.js`. Types, HP, danger, apprivoisement, probabilités par niveau, déterminisme des positions par secteur et exclusion des zones inondées. **Tests** : `tests/unknown-horror-x-creatures.test.mjs` (cinq scénarios définis).

**Important** : ce module est un catalogue de règles et de données de spawn pour la future carte. Les dinosaures ne sont pas des modèles 3D nouvellement construits, aucune IA/animation/morphologie, capture réelle, navmesh, ni apparition en jeu UE5 n'est intégrée. La carte 20×20 km du projet local `D:\ANOMALIA` reste inaccessible ici. Les tests sont fournis dans le dépôt mais ne sont pas déclarés exécutés sans exécution CI/locale.
