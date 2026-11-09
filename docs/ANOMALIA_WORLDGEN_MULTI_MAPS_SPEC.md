# ANOMALIA’Z PRIGIMALIA — Générateur procédural multi-cartes (RWG/PCG)
Version de conception 0.1 — 9 novembre 2026

## Statut et objectif
**Spécification technique, PAS un générateur UE5 exécuté.** Cible: Unreal Engine 5.8/5.8.3, PCG, World Partition, Landscape, Water, Houdini facultatif (aucune dépendance requise). Cible: les **20 cartes de référence** dans `config/worldgen/worlds.json`, sans effacement ni altération des mondes existants. **UNKNOWN HORROR** reste une idée de carte supplémentaire, non ajoutée au catalogue des vingt.

GitHub contient déjà `scripts/ue5/generate-terrain.py`, générateur RAW 16 bits **spécifique à 48 × 48 km**, et `src/racconia-varkovia.js`, fiche de conception 16 × 16 km. Le fichier `.uproject` active le plugin PCG; cela ne prouve pas l'existence d'une carte UE5 jouable. Le jeu JS/Electron et les vrais niveaux Unreal sont distincts; ne pas assimiler une prévisualisation web à une `.umap`.

## Principes non négociables
1. **Aucune écriture dans `D:\\ANOMALIA`, `FabImports`, `sketchfab`, `Content/Maps` ou dans une carte réelle sans inventaire, sauvegarde et validation.** Les scripts doivent fonctionner dans un dossier de sortie isolé, à un emplacement explicite.
2. Mode par défaut `--dry-run`: calculer un manifest, un aperçu et un rapport de conflits **sans toucher aux niveaux source**. `--generate` exige un dossier de sortie inédit; pas d'option `--force` destructrice.
3. Préserver les acteurs à la main via identifiants stables, couche `Protected/HandAuthored`, géométries d'exclusion, zone tampon et version du catalogue. Les emplacements préexistants sont des contraintes, pas des suggestions.
4. Un `worldId` permanent, une graine par monde et une version d'algorithme constituent la clé de reproductibilité. Sous une même version, même entrée → mêmes manifestes et placements, quel que soit l'ordre des tuiles.
5. Terrain/côtes, routes, implantations urbaines, placements d'assets, gameplay et optimisation sont des **phases séparées**. Un échec n'efface pas les phases validées.
6. Toute ressource importée doit comporter provenance, licence, échelle, collision, LOD/Nanite éventuel et statut de validation. Aucune reproduction directe d'assets ou de lieux protégés de Resident Evil.
7. Le générateur ne remplace pas les tests natifs UE5, le packaging ou le profilage en jeu.

## Données d'entrée
`config/worldgen/worlds.json` constitue le **catalogue de conception**; les dimensions absentes restent `null` tant que le rapport hauteur/largeur n'a pas été validé. Ne pas déduire `30 × 30 km` du seul chiffre `900 km²` sans confirmation. Les surfaces indiquées incluent terre et eau selon chaque fiche.

Chaque monde accepte ensuite un profil de production indépendant:
```json
{
  "worldId": "racconia-varkovia",
  "seed": "ANOMALIA-2026",
  "generatorVersion": "worldgen-v1",
  "boundsMeters": [16000,16000],
  "landTargetFraction": 0.65,
  "eligiblePlacementDensity": 0.65,
  "tileMeters": 1000,
  "sourceAssets": [],
  "protectedActorsManifest": "inputs/racconia-varkovia/protected-actors.json",
  "reservedSitesManifest": "inputs/racconia-varkovia/landmarks.json",
  "outputRoot": "GeneratedWorlds/racconia-varkovia/worldgen-v1"
}
```
**Important :** pour RACCONIA-VARKOVIA, le terrain est projeté à 65 % de terre / 35 % d'eau dans `src/racconia-varkovia.js`. La **densité de placement 65 %** demandée pour le générateur est un paramètre **distinct**: proportion de cellules éligibles recevant des propositions de végétation/bâtiments selon leur usage, jamais « 65 % de toute la carte couverte de maisons ».

Les **29 sites** de RACCONIA-VARKOVIA sont planifiés dans la fiche source; `plannedSites:29` ne signifie **pas** que 29 bâtiments jouables existent dans Unreal. Les sites sont des zones réservées, avec verrouillage de placement jusqu'à disponibilité d'un asset validé.

## Pipeline déterministe
### Phase 0 — audit/gel des éléments actuels
Inventorier les `.umap`, `.uasset`, instances PCG, acteurs placés, références de meshes, chemins, coordonnées géoréférencées/locales, inventaires de véhicules, sauvegardes et fichiers source. Vérifier accès UE5 au projet et versions/branche du code. Exporter un manifeste de préservation; conserver les propriétaires des ressources.
Sortie: `source-audit.json`, `protected-actors.json`, zones d'exclusion et checksums, sans déplacer les sources.

### Phase 1 — macroterrain
Générer à partir d'une graine hachée par `worldId/stage/tile`: altitude, drainage, bassins, rivières, lacs, côtes, îles, pentes et masques de biomes. Les tuiles partagent une même fonction d'altitude en coordonnées **globales** afin d'éviter les coutures; contrôler que la bordure commune est identique.
Produire des tuiles heightmap RAW/R16 + métadonnées, jamais prétendre obtenir automatiquement un niveau UE5. Valider la plage d'altitude et le codage Landscape, les résolutions admises par UE5 et le niveau de mer. Ajouter World Partition et géoréférencement/origin shifting pour grandes tailles; traiter la carte de 10 000 km² **par tuiles**.
Les régions protégées bloquent la modification du relief, ou requièrent une solution de raccordement/smoothing validée autour de leur frontière.

### Phase 2 — climat et biomes
Système de poids pour forêts, marais, plaines, neige, montagnes, zones arides, côtes, îles et zones urbaines contaminées. Les règles prennent altitude, pente, humidité, température fictive, distance à l'eau et biomes voisins. World Partition/PCG générera des instances (HISM/ISM selon faisabilité), avec exclusions de routes, bâtiments, criques et zones de spawn. Ne jamais altérer des biomes manuels sans validation.

### Phase 3 — routes et infrastructures
Construire un graphe de connexions entre villes, ports, bases, villages et POI préservés. A*/Dijkstra ou optimisation de graphe selon pente, franchissement des eaux, valeur des terrains et zones interdites. Hiérarchie: routes principales, secondaires, chemins, pistes. Réserver des volumes pour ponts, viaducs, tunnels, rails, parkings et accès au port. Chaque route doit être **connectée**, praticable en véhicule et sans coupure/cul-de-sac involontaire. Terrain adjustment seulement sur bandes routières non protégées.

### Phase 4 — villes, villages et bâtiments
Conserver des zones réservées pour les POI nommés avant toute population. Générer des parcelles à partir d'un réseau routier; zones résidentielles, commerciales, médicales, militaires, industrielles et rurales. Ne placer que des Blueprints/prefabs autorisés, validés pour taille, orientation, accès, pente, collision, distance de sécurité, allées et évacuation. Les bâtiments existants sont « locked » et non régénérés.
Les bâtiments de survie ont une fiche: niveaux accessibles, portes, intérieur, navmesh, alimentation électrique, loot slots, points de zombies, passages souterrains. Aucun marqueur de planification ne compte comme bâtiment terminé.

### Phase 5 — systèmes de jeu
Brancher les portes clés/cartes/code/Morse, loot, zones contaminées, PNJ/zombies/animaux, navmesh, collisions, physique véhicules, points de sauvegarde, spawn et chemins d'évacuation. Le multijoueur conserve côté serveur les données d'inventaire, véhicules, portes et états des joueurs. Pas de modification de `Saved/Servers` au moment de la génération offline.

### Phase 6 — baking UE5, optimisation et certification
Importer Landscape via API éditeur validée dans **une nouvelle carte/staging**. Configurer World Partition, acteurs externes (OFPA), Data Layers, HLOD, streaming et PCG Partitioned Generation selon tests UE5 5.8. Bake/inspect PCG, water, foliage, collisions et navigation. Qualifier sur PC cible et charger/décharger des cellules; tester sauvegarde, empaquetage, démarrage menu, FPS, streaming, conduite, zombies et coop. Les cartes approuvées sont promues en production **une par une**.

## Stabilité, reprises, traçabilité
- `seedNumeric = StableHash(UTF8(worldId + "|" + seed + "|" + stage + "|" + generatorVersion))` avec algorithme et codage explicitement versionnés; jamais se reposer sur `hash()` Python aléatoire par processus.
- `manifest.json` par étape: entrée, version, hash, cellules générées, assets placés, collisions et avertissements.
- Artefacts temporaires écrits atomiquement, réutilisation des tuiles dont les entrées sont inchangées. Un arrêt ou crash permet de reprendre sans régénérer les tuiles terminées.
- `--diff` produit changements ajoutés/déplacés/supprimés par identifiants stables. **Toute suppression d'acteur protégé bloque la génération**.
- Exclusions automatiques autour des POI/structures existants et toute zone de danger; mode de correction manuelle de conflits dans ANOMALIA Editor.
- Aucun lancement GitHub Actions ne prouve que les niveaux ont été importés ni que Windows/UE5 a réellement tourné.

## Modules à implémenter (noms proposés)
- `scripts/ue5/worldgen/catalog.py`: lecture/validation des 20 profils.
- `scripts/ue5/worldgen/seed.py`: RNG/hachage stable, tests de déterminisme.
- `scripts/ue5/worldgen/heightfield.py`: tuiles bord à bord, altitude, eau, masks.
- `scripts/ue5/worldgen/biomes.py`: climat/biomes à résolution multi-échelle.
- `scripts/ue5/worldgen/roads.py`: graphe routier, pentes, ponts, tunnels.
- `scripts/ue5/worldgen/settlements.py`: parcels, villes, bâtiments validés.
- `scripts/ue5/worldgen/protection.py`: lecture des vrais niveaux, protections/diff.
- `scripts/ue5/worldgen/manifest.py`: reprises, provenance et changements.
- `unreal/Source/AnomaliaPrimevalEditor`: importer/bake niveaux via API UE5 (à créer).
- `ANOMALIA Editor`: UI de prévisualisation, génération en staging, validation/promote.

## Critères d'acceptation
1. Test reproductible: même graine + monde + version → manifestes identiques; graine différente → monde différent.
2. Test bordures RAW: tuiles voisines, hauteurs identiques sur l'arête commune.
3. Test protection: aucun acteur protégé supprimé, déplacé, remplacé, ni terrain sous ses fondations retouché.
4. Test topologie: tous les POI routiers requis ont un itinéraire terrestre, pont ou liaison explicite; aucun tunnel inaccessible.
5. Test IA: accès navmesh pour entrées principales; loot et événements ne spawnaient pas dans les murs ou océans.
6. Test isolation: modifier une carte n'altère pas les dix-neuf autres, ni les sauvegardes existantes.
7. Test UE5: création du vrai niveau `.umap`, sauvegarde, réouverture, packaging et session joueur validés **sur la machine cible**.
8. Test performance: benchmarking World Partition, mémoire, fps, nombre de draw calls, impacts PCG avant « terminé ».

## Plan d'exécution orienté première semaine (objectif, non garantie)
- J1: audit sources et niveaux, définition des zones protégées, validation des dimensions/biomes et outils UE5.
- J2: passer le générateur relief 48 km à un moteur multi-tailles et streaming tuilé; test de 16 km.
- J3: génération macroterrain + biomes pour RACCONIA-VARKOVIA puis échantillons d'autres tailles.
- J4: graphe routier et réservations de parcelles; création des previews et rapports de conflits.
- J5: placement PCG des végétaux/bâtiments autorisés dans une copie de staging; migration non destructive.
- J6: batch de prévisualisations/génération des cartes configurées, tests de coutures et reprise.
- J7: inspection native, optimisation ciblée et rapport d'état **carte par carte**.

**Résultat réaliste après une semaine si tout passe:** socle générateur validé + plusieurs cartes provisoires produites en staging. **Non garanti:** 20 mondes photoréalistes finis, tous bâtiments intérieurs jouables, 60 FPS sur consoles, véhicules et multijoueur certifiés. Les problèmes doivent être consignés sans augmenter fictivement les % d'avancement.

## Cas RACCONIA-VARKOVIA
Carte indépendante 16 × 16 km = 256 km², 65 % terre (166,4 km²), 35 % eau (89,6 km²), graine `ANOMALIA-2026`, **densité de placement** 65 % dans les surfaces éligibles, ambiance survival horror. Les 29 POI planifiés par `src/racconia-varkovia.js` sont réservés comme landmarks et les 10 lieux sélectionnés de Requiem/Revelations ont priorité de réservation. Aucun modèle de jeu tiers ne doit être copié. Cette fiche ne constitue pas une `.umap`.
