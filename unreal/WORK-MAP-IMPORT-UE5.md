## Mise a jour sur le PC en une commande PowerShell

Le fichier `scripts/ue5/update-work-world.ps1` est dans cette branche.
Il verifie `C:\ANOMALIA\unreal\AnomaliaPrimeval.uproject`, telecharge temporairement
le generateur et la geographie Work, puis prepare `unreal/TerrainWorkImport/`.
Il ne modifie pas `AnomaliaWorld`, ne touche pas aux Blueprints et n'ecrase pas
un terrain existant. **Node.js est necessaire** pour executer le generateur JS.

Depuis PowerShell sur Windows :

```powershell
$u='https://raw.githubusercontent.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/ue5/prototype-world-ai-roads-20261020/scripts/ue5/update-work-world.ps1'; $s=Join-Path $env:TEMP 'anomalia-work-map-update.ps1'; Invoke-WebRequest -Uri $u -OutFile $s; powershell -NoProfile -ExecutionPolicy Bypass -File $s -ProjectRoot 'C:\ANOMALIA'
```

Une fois les fichiers sources generes, **un import Landscape dans Unreal Editor reste
necessaire pour produire une vraie carte .umap**. Aucune compilation Unreal, aucun
import Unreal automatique et aucun test PIE ne sont revendiques par la commande.
Conserver le niveau `AnomaliaWorld` comme sauvegarde et importer dans
`ANOMALIA_WorkMap_Test` uniquement.

---

# ANOMALIA — importer la véritable géographie Work dans Unreal Engine 5.8

## Prototype routes, batiments, vegetation et IA — UE5 (non compile ici)

Un acteur C++ independant `AAnomaliaWorkWorldBootstrap` a ete ajoute pour un
**quartier de demonstration**, centré autour du point (0,0). Il n'edite pas le
`.umap` et se declenche **uniquement** quand l'acteur est place sur le niveau
`ANOMALIA_WorkMap_Test`, en mode de jeu local/listen. Il n'est pas active
sur `AnomaliaWorld` ni sur les serveurs dedies.

Quand le Landscape Work est importe et visible, l'acteur produit en Play :
- Deux axes de route de demonstration en cubes instancies, suivant grossierement
  le relief (pas encore des routes aplaties ou des splines).
- Jusqu'a **20 batiments-prototypes** (volumes cubiques avec toit), collisions basiques.
- Jusqu'a **60 arbres** avec geometrie provisoire.
- Jusqu'a **12 agents** (cervides, sangliers, loups, dinosaures, civils,
  gardes) en formes primitives avec deplacement tres simple. Les agents sont
  serveurs; ils ne sont pas de vrais humanoides animes, ni des IA de combat.

**Installation sans effacer les fichiers existants :** relancer
`scripts/ue5/update-work-world.ps1` via la commande PowerShell documentee
plus haut. Elle telecharge les quatre nouveaux fichiers source dans
`unreal/Source/AnomaliaPrimeval`. Si un fichier de meme nom a ete modifie
sur ton PC, l'installateur refuse de l'ecraser.

Apres avoir ferme Unreal, reconstruire le projet C++ et ouvrir
`ANOMALIA_WorkMap_Test`. Dans le panneau **C++ Classes → AnomaliaPrimeval**,
rechercher `AnomaliaWorkWorldBootstrap`, glisser un exemplaire dans ce niveau,
enregistrer et cliquer **Jouer**. Un message de log signale l'absence de Landscape
au point central au lieu de placer des objets dans le vide.

**Limites connues :** le rendu local peut etre lourd, les visuels sont des
placeholders, il faut importer le Landscape avant, et les instances de maillages
ne sont pas repliquees aux clients reseau. Tester d'abord en mode joueur unique,
sur la machine de l'editeur. Les details definitifs de la carte de 2 304 km²,
routes, maisons et faune, restent a produire.

---



## Attention : deux cartes différentes dans le même dépôt

- **Carte Work courante :** `src/mechanics.js`, monde **48 × 48 km**, **8 masses terrestres** (`CONTINENTS`), villes et points d'intérêt (`CITIES`, `SITES`).
- **Ancien prototype d'île Unreal :** `scripts/ue5/generate-terrain.py`, **6 îles à d'autres coordonnées**. **Ne pas l'utiliser pour remplacer la carte Work.**
- Le fichier `src/world.js` contient encore une ancienne géographie **96 × 96 km**. Ce n'est pas celle correspondant à `src/world-metrics.json` (2 304 km²).
- `src/world-metrics.json` indique 374,521875 km² de terres (ancienne mesure). Une mesure directe sur la fonction `heightAt()` actuelle peut être différente selon la révision et l'échantillonnage. Ne pas déclarer ces chiffres vérifiés dans Unreal.

## Export reproductible, sans écrasement

Depuis la racine du dépôt GitHub, avec Node.js installé :

```powershell
node .\scripts\ue5\export-work-map.mjs
```

L'export crée uniquement trois fichiers dans `unreal/TerrainWorkImport/` :
- `ANOMALIA_WorkMap_48km_3025.r16` : **véritable heightmap Work**, une seule image de 3 025 × 3 025 échantillons, ~18,3 Mo.
- `ANOMALIA_WorkMap_48km_3025.json` : étendue, altitudes, échelle et SHA-256.
- `ANOMALIA_WorkMap_Landmarks.json` : coordonnées originales Work des villes, sites, continents et sommets. **Les bâtiments ne sont pas créés par ce fichier.**

L'export ne modifie **aucun** `.umap`, `.uasset`, Blueprint, serveur ou sauvegarde. Il refuse d'écraser un export déjà présent.

## Import dans Unreal Editor 5.8 (sur le PC)

1. **Conserver le monde existant `AnomaliaWorld` intact.** Dans Fichier → Nouveau niveau, choisir **Open World** et sauvegarder sous **`/Game/Maps/ANOMALIA_WorkMap_Test`**.
2. **Dans ce nouveau niveau seulement**, supprimer le Landscape d'exemple créé par le modèle Open World, s'il existe ; laisser les éléments d'éclairage.
3. Aller au mode **Paysage / Landscape** (Maj + 2) → **Gérer** → **Importer depuis un fichier**. Choisir `ANOMALIA_WorkMap_48km_3025.r16`.
4. Configuration à vérifier : résolution **3025 × 3025**, **63 quads/section**, **2 × 2 sections/composant**, soit **24 × 24 composants** (576). Échelle Landscape **X=1587,301587 ; Y=1587,301587 ; Z=800** (valeurs Unreal en centimètres). Cela produit **48 km de côté**.
5. Vérifier visuellement l'orientation nord/sud via **Flip Y Axis** avant de confirmer ; une éventuelle inversion doit correspondre aux coordonnées des villes de la source.
6. Placer un **PlayerStart** au-dessus du sol dans une région de terre. Sauvegarder le nouveau niveau et **tester Jouer**.
7. Ne changer les cartes par défaut du projet qu'**après** vérification de la compilation, du point de départ et du streaming.

**Performance :** cette hauteur est un **brouillon de 15,87 m entre points**, pas du 16K. Sur GPU sans SM6, utiliser un secteur d'essai avant de charger tout le monde et choisir des réglages de rendu compatibles.

**Ce qui reste hors de l'import :** mer et navigation, textures, végétation, villes, bâtiments, routes, circulation, personnages squelettiques, animations, animaux, IA, véhicules Chaos, audio et optimisation World Partition. Les `CITIES` et `SITES` exportés ne constituent pas des acteurs dans Unreal. Ces éléments doivent être construits séparément, puis testés dans l'éditeur.
