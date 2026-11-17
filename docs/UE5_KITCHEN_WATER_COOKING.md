# ANOMALIA’Z PRIGIMALIA — eau, marmite et poêle (Unreal 5.8)

## État exact
Fonctionnalités **implémentées en code source C++ sur une branche séparée** ; pas encore compilées/validées dans le projet Windows ni prouvées jouables sur les cartes installées. Les anciens mondes, inventaires, objets existants, profils et paramètres ne sont pas supprimés.

## Objets et actions native UMG
- `empty_water_bottle` + eau potable => `water_bottle`; eau naturelle => `dirty_water_bottle`.
- `empty_military_canteen` => `military_canteen` ou `dirty_military_canteen`.
- `empty_filter_canteen` => `filter_canteen` ou `dirty_filter_canteen`.
- `cooking_pot` => `cooking_pot_water` ou `dirty_cooking_pot_water`. Une marmite pleine représente **1 L** dans cette V1 (pas encore de portions graduées).
- Pour une bouteille/gourde sale, `RequestTreatWater` consomme une vraie `water_purification_tablets` et rend l'eau potable. La gourde filtrante **ne purifie pas automatiquement** dans cette V1, pour ne pas inventer une cartouche filtrante fonctionnelle.
- Marmite d'eau sale : 20 s au feu allumé => marmite d'eau potable. Aucun résultat si le feu s'arrête ou si le joueur s'éloigne.
- `frying_pan` : cuisson 30 s, sans consommer la poêle. `cooking_pot_water` : cuisson 40 s, une dose d'eau utilisée, la marmite demeure vide.
- Ingrédients autorisés : `raw_meat -> cooked_meat`, `raw_fish -> cooked_fish`, `egg -> cooked_egg`, `potato -> cooked_potato`, `vegetable -> cooked_vegetable`.
- Boutons **Remplir d'eau**, **Purifier**, **Faire bouillir**, **Cuire : ...** dans le panneau de l'objet sélectionné de l'inventaire **natif**; messages du serveur répliqués au joueur.

## Préparation dans le VRAI monde UE5.8
1. **Sans remplacer les niveaux existants**, ajouter `AAnomaliaZPrigimaliaWaterSource` (ou un Blueprint dérivé) sur les points d'eau visibles et accessibles. Poser le point au bord à portée physique (max 250 cm par défaut). `bPotable=false` pour rivières/lacs, `bPotable=true` pour fontaines/puits d'eau propre. Les vrais plans d'eau ne sont **pas** automatiquement détectés par cette V1 : placer ces points dans les cartes officielles du jeu.
2. Sur un vrai acteur de feu de camp/réchaud avec meshes/FX licenciés, raccorder l'**existant** `UAnomaliaZPrigimaliaHeatSourceComponent`, lui donner du carburant `FuelSeconds>0` et déclencher `Ignite()` côté serveur. La cuisson exige que ce composant soit **en combustion**, dans le rayon du joueur et sans obstacle (contrôle de visibilité).
3. Garder les chemins d'assets existants ; l'ajout C++ ne génère aucun faux mesh de marmite/poêle/feu ou animation.
4. Charger le catalogue JSON `public/config/loot_items_catalog.json` **étendu sans écraser les entrées existantes** et vérifier l'inclusion effective par le système de packaging du projet Windows.
5. Compiler `AnomaliaZPrigimaliaEditor` + jeu, relancer UHT, puis test PIE 2 joueurs avec sources propres/sales et vrais feux. Tester aussi le bouton manette, la distance, le feu éteint, la conservation des aliments, l'inventaire plein, le stockage sur la ceinture, les stacks multiples et la récupération après redémarrage.

## Transactions et limites
Les transformations ne se font qu'avec l'autorité serveur ; aucune requête client ne fournit de résultat cuisiné, de qualité d'eau, ni de position. Le moteur utilise les IDs exacts de piles, la validation des quantités affichées, le cooldown, les contrôles de portée et de feu. Avant publication, le profil de joueur est sauvegardé une seule fois. Toute opération impossible conserve l'état précédent et signale l'erreur ; les ingrédients d'une cuisson interrompue ne sont pas consommés.

**À ne pas confondre :** les anciennes recettes `public/config/dinosaurs/cooking_recipes.json` restent **CONFIG_ONLY**. Ce lot réalise une première cuisson native des ingrédients simples, **pas** toutes les soupes, mijotés et effets ARK. Pas de gestion des portions partielles, de la graisse, du brûlé, ni des infections complexes. Ces ajouts nécessitent une itération ultérieure.

**Statut final uniquement après compilation native et parcours de la vraie carte.**
