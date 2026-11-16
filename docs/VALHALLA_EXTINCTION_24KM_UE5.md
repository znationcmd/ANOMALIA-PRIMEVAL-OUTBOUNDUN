# ANOMALIA’Z PRIGIMALIA — VALHALLA EXTINCTION

**Nouvelle carte distincte : 24 × 24 km = 576 km².**
**Univers : exclusivement viking / horreur nordique.**
**Statut vérifié : données de relief réelles RAW16 + implantation de 12 lieux + 168 positions de Draugr. Aucune carte .umap native ni zombie jouable n'a été produit ou lancé sur le PC.**

## Ce que contient ce kit

- `VALHALLA_EXTINCTION_2017x2017.r16` : vraie heightmap 16 bits, 2017 × 2017, couvrant 24 km de côté.
- `tiles/height_x*_y*.r16` : 16 tuiles 505 × 505, bords vérifiés et continus.
- `valhalla-layout.json` : 12 lieux vikings, 8 sanctuaires runiques, 168 candidats d'apparition des morts-vivants.
- `valhalla-placements.csv` : positions en centimètres pour les futurs acteurs UE5.
- `terrain-manifest.json` : dimensions, SHA-256, import Landscape, limites connues.
- `generate_valhalla_extinction.py` : générateur de relief déterministe (Python 3 + numpy).
- `stage_valhalla_extinction_world.py` : création sécurisée d'un niveau World Partition dans une copie de projet UE5.8, et placement des vrais assets par chemin d'asset **uniquement lorsque ceux-ci existent**.
- `valhalla-assets.template.json` : chemins à relier aux vrais bâtiments, drakkars et Blueprints de zombies du projet ANOMALIA.

## Direction artistique et gameplay à construire

Viking pur, VIIIe-XIe siècles, dark fantasy : maisons longues, halls du jarl, palissades et fortins en bois, temples (hof) et pierres runiques, tertres funéraires, forges, cabanes de pêche, drakkars et ports ; forêts de conifères et bouleaux, marais, vallées glaciaires, montagnes enneigées, fjords et archipels. Sentiers de terre et chemins de bois seulement. **Aucun bâtiment moderne, aucune route bitumée, voiture, arme à feu, vêtement moderne ou casque à cornes**.

Zombies **uniquement habillés à la viking** : Draugr thrall (tunique en lin et laine), Huskarl (cotte de mailles, casque de fer sans cornes), Berserker (peaux de bête, hache), Shieldmaiden (robe de laine, gilet de cuir, bouclier), Seidr (robe rituelle). Les modèles 3D, squelettes, vêtements, animations, AI Controllers, Behavior Trees, NavMesh, loot et combat sont **à relier/construire dans le jeu réel** : le kit fournit les définitions et les emplacements, pas un simulacre d'IA.

## Import dans Unreal Engine 5.8

1. Créer une **copie de sauvegarde** du vrai projet ANOMALIA ; ne pas écraser SKARVIK, RACCONIA ni un autre niveau.
2. Activer **Python Editor Script Plugin**. Depuis la console Python d'UE5.8, inclure le dossier contenant `stage_valhalla_extinction_world.py`, puis appeler :

   ```python
   import sys
   sys.path.insert(0, r'C:\VALHALLA_EXTINCTION_24x24_SOURCE')
   import stage_valhalla_extinction_world as valhalla
   print(valhalla.create_level(r'C:\VALHALLA_EXTINCTION_24x24_SOURCE\valhalla-layout.json'))  # vérification sans écriture
   print(valhalla.create_level(r'C:\VALHALLA_EXTINCTION_24x24_SOURCE\valhalla-layout.json', confirm_create=True))
   ```

   Le niveau indépendant est créé sous `/Game/Maps/VALHALLA_EXTINCTION_24KM` avec des **TargetPoints de repérage**, pas des bâtiments réels.
3. Dans **Landscape > Import from File**, importer `VALHALLA_EXTINCTION_2017x2017.r16` dans **ce nouveau niveau seulement**. Paramètres :

   - 2017 × 2017 points = **16 × 16 composants**, 63 quads par section, 2 × 2 sections par composant.
   - X = Y = **1190.476190476 cm**, Z = **800 cm**. Ces valeurs correspondent à exactement 24 × 24 km, relief compris environ -340 m à +1850 m.
   - Position du bord supérieur gauche recommandée **(-1 200 000, -1 200 000, 0) cm**, mais l'acteur Landscape utilise parfois une origine différente : **aligner visuellement les marqueurs avant toute construction**.
   - Vérifier la case **Flip Y** selon le sens Nord→Sud ; vérifier collisions, accès au rivage, streaming, et la densité de vertex (~11,9 m entre points).
4. Importer les véritables assets 3D vikings et remplir `valhalla-assets.template.json` avec leurs **vrais** chemins `/Game/...`, en le renommant `valhalla-assets.json`. Aucun asset n'est inventé ou installé depuis Internet par le script.
5. Après validation du Landscape et des assets, appeler `place_real_assets(layout, bindings, confirm_place=True)` dans le nouveau niveau. Un appel sans `confirm_place=True` est un diagnostic de chemins uniquement. Les positions des bâtiments doivent être ajustées à la pente et aux dimensions réelles de chaque mesh.
6. Connecter les 5 Blueprints de zombies aux vrais vêtements vikings et aux AI/AnimBP/BT. Ajouter loot/crafting Viking, chemins/splines, navigation, eau, météo, éclairage et tester **PIE puis build Windows**.

## Ce qui n'est PAS fait

- Le projet Unreal local `D:\ANOMALIA` n'est pas accessible ici. Aucun fichier `.umap`, `.uasset`, build Windows ou installation sur le PC n'a été réalisée.
- Aucun bâtiment, drakkar ou personnage Viking 3D sous licence n'est dans le kit. Les points de spawn ne suffisent pas pour une IA fonctionnelle.
- Aucune compilation Unreal, contrôle visuel dans le jeu, sauvegarde du jeu existant, ou test de connexion multijoueur n'a eu lieu.

## Références Unreal

- Landscape 2017 x 2017 validé par Epic : https://dev.epicgames.com/documentation/unreal-engine/landscape-technical-guide-in-unreal-engine
- Import R16 et World Partition : https://dev.epicgames.com/documentation/unreal-engine/importing-and-exporting-landscape-heightmaps-in-unreal-engine