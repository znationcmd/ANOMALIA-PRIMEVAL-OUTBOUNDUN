# ANOMALIA’Z PRIGIMALIA

Projet de **jeu de survie 3D original en monde ouvert**, sur navigateur PC, en cours de développement. **Pré-alpha** — pas encore un jeu complet comparable en production à DayZ, ARK, Red Dead Redemption ou Arma Reforger.

## Installer Windows (PC 64 bits) — Pré-alpha

L'application Windows n'exige pas l'installation de Node.js ni l'ouverture d'un navigateur Web.
Une compilation GitHub Actions produit un **installateur Windows NSIS** qui installe le jeu, ajoute un raccourci sur le bureau et dans le menu Démarrer, et permet sa désinstallation via les paramètres Windows.

**Télécharger :** [GitHub Actions — installateur Windows](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/workflows/windows-installer.yml). Ouvre la dernière exécution réussie, puis le fichier **ANOMALIAZ-PRIGIMALIA-Installateur-Windows** dans la section *Artifacts*. Décompresse l'archive obtenue pour récupérer le fichier `.exe`, puis exécute-le sur Windows 10/11 x64.

**Avertissement :** l'installateur de pré-alpha est actuellement **non signé**. Windows SmartScreen peut afficher une alerte. N'utilise que le fichier issu du dépôt GitHub officiel, et n'ignore pas un avertissement de sécurité si tu ne reconnais pas son origine. Les performances WebGL et la prise en charge des manettes devront être testées sur un véritable PC Windows. Il ne s'agit pas encore d'un jeu achevé.

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
- Animaux sauvages terrestres (cerfs, sangliers, oiseaux et jaguars), crocodiles sur les berges, requins en mer et poissons pêchables : modèles 3D stylisés, chasse et butin.
- Viande et poisson crus, cuisson près d'un feu de camp, eau potable, rations, baies et œufs à trouver. La faim et la soif restent actives.
- Fléchettes tranquillisantes pour endormir les dinosaures, puis croquettes herbivores/carnivores pour les apprivoiser. Le réveil interrompt un apprivoisement incomplet.
- Quatre zones de jungle distinctes, végétation plus dense et marquage visible sur la carte ; repères personnalisés conservés dans la sauvegarde locale.

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
| Pêcher près de l'eau | P |
| Installer un feu de camp (5 bois) | G |
| Cuire une viande ou un poisson près du feu | K |
| Changer fusil / fléchettes tranquillisantes | V |
| Ouvrir les recettes (croquettes, canne, fléchettes) | I, puis les boutons du sac |
| Poser un repère sur la carte | M puis clic gauche |
| Supprimer un repère sur la carte | M puis clic droit sur le repère |

### Manettes Xbox, PlayStation et compatibles PC

Le jeu prend en charge simultanément **clavier + souris** (AZERTY : ZQSD / QWERTY : WASD) et **manette** via l'API Gamepad du navigateur. Branchez la manette en **USB** ou associez-la en **Bluetooth**, puis appuyez sur un bouton une fois la page ouverte pour l'activer. Le moteur reconnaît les dispositions standard Xbox et PlayStation (DualShock / DualSense) lorsque le navigateur les expose.

| Action | Manette Xbox | Manette PlayStation |
| --- | --- | --- |
| Se déplacer / diriger le bateau | Stick gauche | Stick gauche |
| Regarder | Stick droit | Stick droit |
| Tirer | RT | R2 |
| Interagir / ouvrir un bunker | X | Carré |
| Courir | L3 | L3 |
| Inventaire / vêtements | Y | Triangle |
| Recharger | RB | R1 |
| Lampe | LB | L1 |
| Carte | View | Create |
| Pause / aide | Menu | Options |
| Valider / retour | A / B | Croix / Rond |
| Monture / bateau / reproduction / construction | Croix directionnelle ↑ / ↓ / ← / → | Croix directionnelle ↑ / ↓ / ← / → |

Les sticks ont une zone morte pour limiter la dérive ; les boutons d'action ne se déclenchent qu'une fois par pression. Les menus prennent en charge les boutons de validation et le déplacement au stick gauche ou à la croix directionnelle. En cas de déconnexion, le clavier et la souris restent utilisables. Les manettes avec une disposition non standard ou les fonctionnalités propres à certains modèles (gâchettes adaptatives, vibrations, gyroscope) ne sont **pas garanties**.

Le stockage utilise `localStorage` dans le navigateur; il ne synchronise pas encore la partie entre appareils. Les commandes tactiles sont expérimentales.

## Animaux, pêche et apprivoisement (pré-alpha)

La chasse à l'arme à feu récupère les ressources d'un animal abattu **une seule fois**. La pêche exige une canne, une berge accessible ou un bateau ; elle a un délai entre les lancers et une chance d'échec. Le poisson et la viande crus ne peuvent être mangés tant qu'ils ne sont pas cuits. Dans l'inventaire, il est possible de fabriquer une canne (bois/fibres), des fléchettes (ferraille/tissu/baies) et les croquettes spécifiques.

Pour endormir un dinosaure, active le mode fléchettes (V sur clavier, clic sur le stick droit R3 à la manette), vise et tire plusieurs fois. Approche l'animal endormi et appuie sur E / X / □ pour lui donner des croquettes adaptées. Deux nourrissages réussis complètent actuellement l'apprivoisement. Il peut se réveiller si le processus est trop lent. Ce système n'est pas une reproduction exacte des statistiques d'ARK.

Quatre secteurs de jungle sont représentés en vert et sont nommés sur la carte. Le clic sur celle-ci ajoute un repère local, le clic droit supprime un repère proche. Les zones comprennent une végétation plus dense et peuvent accueillir des jaguars. L'IA, les animations et le réalisme de ces animaux restent à améliorer.

**Limitations :** aucun test physique d'ergonomie ni de performances en conditions réelles n'est confirmé, les poissons sont actuellement représentés par des captures de pêche plutôt que par des bancs animés indépendants. Les règles de combat, les interactions et l'écologie restent des systèmes de pré-alpha.

## Architecture

- `index.html` et `src/style.css` : interface et HUD.
- `src/main.js` : moteur de rendu, chargement progressif du monde, jeu en temps réel.
- `src/mechanics.js` : règles déterministes du territoire de démonstration, villes et lieux.
- `src/world.js` : esquisse de carte procédurale cible 96 × 96 km, à intégrer ultérieurement.
- `src/systems.js` : systèmes d'équipements, poids, maladies, apprivoisement, craft.
- `src/ecology.js` : faune, zones de jungle, chasse, pêche, cuisine, recettes, croquettes et torpeur.
- `tests/ecology.test.mjs` : tests de chasse, de pêche, de cuisson, de sédation et d’habitats.
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
