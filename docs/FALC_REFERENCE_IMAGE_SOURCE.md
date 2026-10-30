# F.A.L.C — 10e carte indépendante d'ANOMALIA'Z PRIGIMALIA

## Source correcte

La seule référence validée est **l'image F.A.L.C fournie par le joueur**, portant notamment les noms Nordskar, Kalten, Drachenfels, Moorgrund, Sonnenfeld, Feuerinsel. **Aucune image trouvée sur le web, carte DRAZOVIA ou heightmap d'un autre monde ne doit la remplacer.** Les images du joueur restent hors du dépôt public.

- F.A.L.C : 26,5 x 26,5 km = 702,25 km², id `falc-v1`, `/Game/Maps/PRIGIMALIA_FALC`
- Objectif théorique : ~500 km² terre / ~202,25 km² mer.
- **Masque réel calculé depuis l'image** : la classification des pixels donne une valeur différente ; ne jamais déplacer arbitrairement les côtes pour forcer l'objectif.
- DRAZOVIA : autre carte indépendante de 48 x 48 km, sauvegardes intactes.

## Fichiers livrés

Exécuter, avec `numpy` et `opencv-python-headless` :

```bash
python scripts/ue5/falc_from_reference_image.py --image /source/FALC_reference.jpg --output /destination/FALC-new
```

Le script n'écrase jamais un dossier existant. Il produit :
- `FALC_26_5KM_MASTER_2017.r16` unsigned RAW16 little-endian 2017²
- `FALC_x00_y00.r16`, `FALC_x01_y00.r16`, `FALC_x00_y01.r16`, `FALC_x01_y01.r16` : quatre quadrants 1009² aux raccords identiques
- `FALC_LAND_MASK_2017.png`, `FALC_SEA_MASK_2017.png`, `FALC_ELEVATION_PREVIEW.png`
- `FALC_IMPORT_MANIFEST.json` : SHA-256 de l'image source et des RAW16, surface dérivée de l'image, incertitudes.

## Précautions UE5.8

Copier les quatre RAW16 dans `<Projet de test>/TerrainSource/FALC/`. L'auteur natif existant `unreal/Scripts/create_falc_native.py` est destiné à un checkout Windows isolé disposant du module C++ compilé. Il **ne doit jamais** écrire dans `D:\\ANOMALIA` ni modifier DRAZOVIA.

Les sorties sont des **heightmaps synthétiques guidées par l'image**, pas des altitudes géodésiques mesurées. La hauteur des montagnes, les pentes, les rivières, textures, routes et biomes nécessitent la sculpture, la vérification et le playtest dans UE5.8. Ni le `.umap` natif ni le jeu jouable ne sont considérés comme validés.

## Ancien générateur

`scripts/ue5/falc_from_composite_r16.py` dérive d'un RAW16 DRAZOVIA : **ancienne proposition incompatible avec la référence du joueur**. Ne pas utiliser cet ancien script pour le rendu final de F.A.L.C. Le nouveau chemin de référence est `falc_from_reference_image.py`.
