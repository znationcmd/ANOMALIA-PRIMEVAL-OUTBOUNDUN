# ANOMALIA'Z — Import des topographies issues des cartes préparées

Les fichiers RAW16 ont été réellement produits dans la conversation et mis
dans deux ZIP séparés. Ils ne sont PAS encore dans le dépôt GitHub ; ne
présentez jamais ces sources comme installées sur Windows ou comme des
fichiers .umap prêts à jouer.

## Affectation des sources
- **DRAKHEIM** : photo 1, 20x20 km, 2017² vertices.
- **SOLYNACALYRA** : photo 2, 15x15 km, 1513² vertices.
- **VORGRAD** : photo 3, 30x30 km, 3025² vertices.
- **NEXAVARKHOS** : photo 4, 10x10 km, 1009² vertices.
- **CHERNASKALUXRIA** : photos 5–9, composition finale sans UI comme masque
  principal, 100x100 km, 400 tuiles de 5km avec 253² vertices chacune.

Terrain original dérivé des MASQUES de côtes des photos et de reliefs
synthétiques. Les images satellites n'offrent pas l'altitude réelle. Pas de
réutilisation de textures de jeux comme terrain 3D.

## Déploiement sûr

1. **Ne pas modifier** `D:\ANOMALIA`, les .umap originaux,
   `FabImports`, `sketchfab`, ou les sauvegardes.
2. Dans une copie isolée du projet, extraire les R16 sous :
   `unreal/TerrainSource/DRAKHEIM/DRAKHEIM.r16`,
   `unreal/TerrainSource/SOLYNACALYRA/SOLYNACALYRA.r16`,
   `unreal/TerrainSource/VORGRAD/VORGRAD.r16`,
   `unreal/TerrainSource/NEXAVARKHOS/NEXAVARKHOS.r16`.
3. Pour CHERNASKALUXRIA, extraire les 400 fichiers directement dans
   `unreal/TerrainSource/CHERNASKALUXRIA/`, sans le sous-répertoire
   `WorldPartition_5km_tiles` à cet emplacement.
4. Si et seulement si le niveau n'existe PAS déjà, compiler l'Editor UE5.8
   avec le code de cette branche. Lancer `create_four_additional_maps.py`
   pour chacun des quatre mondes en réglant :
   `PRIGIMALIA_NEW_MAP=... ` et `PRIGIMALIA_USE_IMAGE_TOPO_R16=1`
   et l'argument Unreal `-ANOMALIAUseUserTopoR16`.
   **Les deux paramètres sont indispensables** : l'un sélectionne le R16
   C++, l'autre évite d'estimer le PlayerStart depuis un relief différent.
5. Contrôler le compte de composants, le relief réel des collisions et les
   fichiers sauvegardés après import. Réserver les imports de
   CHERNASKALUXRIA par secteur au workflow natif spécifique, et surtout
   vérifier d'abord pourquoi le précédent workflow Windows n'a pas produit
   un rapport d'enregistrement UE5 validé.

### Échelles Landscape

RAW16 : uint16 LE ; altitude = (valeur - 32768) / 16 (m).
Z scale Unreal = **800** pour toutes ces sources.
XY scale du terrain quatre cartes = **992.063492** cm par sommet.
XY scale des 400 tuiles CHERN = **1984.126984** cm par sommet.
Les tuiles CHERN ont **760 frontières parfaitement identiques en RAW16**.

### Limites prouvées

Le relief CHERN piloté par la composition sans UI donne environ **4 409
km² de terre / 5 591 km² de mer**, pas la cible de 6 750/3 250 km²
initialement souhaitée. Pour atteindre cette cible il faut agrandir des
terres ou déplacer des côtes : cela doit faire l'objet d'une révision
géographique sans prétendre préserver exactement la photo.

Les RAW16 ne représentent ni la route, ni les modèles 3D, ni les bâtiments,
ni les ponts, ni les tunnels, ni la simulation de l'eau. Le PCG, les
navigation meshes, l'asphalt/road mask, les surfaces de construction,
la collision et les performances multijoueurs restent à tester.

### Statut
- [x] Photos étudiées, ordre confirmé.
- [x] Cartes RAW16 construites dans la conversation et archives vérifiées.
- [x] Taille et surface terrestre mesurées.
- [x] 400 tuiles du 9e monde, raccords vérifiés.
- [x] Code UE5 import des nouvelles hauteurs ajouté sur branche de travail.
- [ ] Vrais fichiers RAW16 présents dans le checkout Windows.
- [ ] Compilation UE5.8 de cette nouvelle branche.
- [ ] Réels .umap importés, collisions et tests PIE réussis.
- [ ] Répartition 5 000 + 1 750 + 3 250 km² réalisée.
