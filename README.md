# ANOMALIA PRIMEVAL OUTBOUNDUN

Projet de **jeu de survie 3D original en monde ouvert**, sur navigateur PC, en cours de développement. **Pré-alpha** — pas encore un jeu complet comparable en production à DayZ, ARK, Red Dead Redemption ou Arma Reforger.

## Démarrage local

Installer Node.js 20+ puis :

```bash
npm install
npm run dev
```

Ouvrir l'URL locale indiquée par Vite. Production : `npm run build`, puis servir le dossier `dist/`.

## Fonctionnalités de cette première version

- Exploration en vue subjective avec WebGL / Three.js, relief procédural généré par secteurs sans chargement d'écran lors des déplacements.
- Villes et bâtiments 3D répartis dans un monde **de test ~20 × 20 km**, continents, montagnes, plages et archipels; un module de terrain à **échelle cible de 96 × 96 km** est également présent mais pas encore raccordé au moteur principal.
- Sites intégrés : bunkers et conteneurs fermés à clé, caches à clés, villages cachés, accès au métro et catacombes, zones portuaires, bateau de base, ponts.
- Système de survie : santé, faim, soif, endurance, météo/biomes, progression locale, adversaires rudimentaires et tir.
- Vêtements interchangeables, sac à dos qui agrandit la capacité de transport, poids, température, maladies et soins.
- Créatures préhistoriques stylisées : nourrissage progressif, apprivoisement, selle et reproduction de base.
- Construction d'abris, collecte de ressources, inventaire, carte, sauvegarde locale de la partie.

Ce sont des mécaniques **pré-alpha**; les modèles, animations, comportements d'IA, physique des véhicules, intérieurs souterrains et combats restent expérimentaux. Les îles accessibles en bateau ne disposent pas encore d'une navigation maritime réaliste. Aucun mode multijoueur opérationnel à ce stade.

## Compatibilité des commandes

**Clavier et souris PC** : ZQSD/WASD, mouvements de souris, clic, touches d'inventaire et interactions restent fonctionnels.

**Manettes Xbox et PS5 DualSense sur PC/navigateur compatible** (USB ou Bluetooth, API Gamepad standard) : stick gauche pour marcher, stick droit pour regarder, clic stick gauche (L3) pour courir, RT/R2 pour tirer, X/□ pour interagir, Y/△ pour l'inventaire, A/✕ pour valider, B/○ pour revenir, RB/R1 pour recharger, LB/L1 pour la lampe, View/Create pour la carte, Menu/Options pour l'aide, croix directionnelle haut pour monter, bas pour le bateau, gauche pour la reproduction et droite pour construire. Dans les menus, stick gauche ou croix directionnelle pour sélectionner et A/✕ pour activer. La manette peut être branchée/débranchée pendant le jeu sans désactiver le clavier.

**Limite :** compatibilité prévue avec une manette reconnue par le navigateur via une disposition « standard ». Il ne s'agit pas d'un portage natif Xbox ou PlayStation 5. Les vibrations, gâchettes adaptatives et fonctions exclusives DualSense ne sont pas encore implémentées ; les essais physiques sur les deux manettes restent à réaliser.

## Commandes

| Action | Touche |
| --- | --- |
| Avancer / reculer / côtés | ZQSD ou WASD |
| Regarder | Souris |
| Interagir / fouiller / nourrir | E |
| Tirer | Clic |
| Recharger | R |
| Inventaire, vêtements, soins | I |
| Carte du monde | M |
| Construire un abri | B |
| Monter/descendre un dinosaure sellé | T |
| Tenter une reproduction à proximité | Y |
| Lampe | F |
| Libérer la souris | Échap |

Les commandes tactiles sont expérimentales. Le stockage utilise `localStorage` dans le navigateur; il ne synchronise pas encore la partie entre appareils.

## Architecture

- `index.html` et `src/style.css` : interface et HUD.
- `src/main.js` : moteur de rendu, chargement progressif du monde, jeu en temps réel.
- `src/mechanics.js` : règles déterministes du territoire de démonstration, villes et lieux.
- `src/world.js` : esquisse de carte procédurale cible 96 × 96 km, à intégrer ultérieurement.
- `src/systems.js` : systèmes d'équipements, poids, maladies, apprivoisement, craft.
- `tests/game.test.mjs` : tests automatiques sans navigateur.
- `.github/workflows/test-game.yml` : compilation et tests à chaque modification.

## Étapes suivantes

1. Faire tourner et tester le jeu sur PC et mobiles; éliminer les défauts de collision, pathfinding, équilibrage et performance.
2. Relier entièrement le monde 96 × 96 km, la génération persistante d'îles et les réseaux souterrains.
3. Créer des bâtiments et des intérieurs détaillés avec objectifs, cartes d'accès, niveaux de sécurité et butin distinct.
4. Développer les cycles de vie des dinosaures (sexe, génétique, incubation, croissance), le système de selles et l'équilibrage.
5. Développer l'arsenal, l'état des armes, le système balistique, les maladies, météo, nutrition, véhicules et réseau.
6. Ajouter un véritable serveur multijoueur, la base persistante, la modération et des pipelines de contenu.

Aucun modèle 3D ni marque appartenant aux jeux cités comme inspirations n'est recopié.
