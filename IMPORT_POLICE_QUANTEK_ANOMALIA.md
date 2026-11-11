# ANOMALIA — audit du modèle « Police » (Quantek Studio)

Date : 28 octobre 2026. Source : https://sketchfab.com/3d-models/police-5cf1e9c6e2e844948cf378f0dd8caa0f

## Contrôle réel des deux fichiers transmis

- `police.zip` : glTF binaire original, **1 mesh**, 880 084 sommets, 1 499 986 triangles, 1 matériau, 3 textures, **0 skin / squelette, 0 animation**.
- `police.glb` : glTF converti, **14 meshes nommés Object_0 à Object_13**, qui se chevauchent et ne sont pas des vêtements individuels ; 0 skin / squelette, 0 animation.
- 6 419 composants géométriques connexes détectés dans la source : ils ne correspondent pas à des pièces vestimentaires directement équipables.
- Métadonnées du GLB converti : Quantek Studio ; licence **CC BY 4.0** https://creativecommons.org/licenses/by/4.0/ . Conserver attribution et vérifier les droits sur uniformes/insignes éventuels.
- Un **GLB dérivé local** a été créé en séparant les triangles par coordonnées en 5 zones indicatives : tête/casquette, torse/gilet, manches/gants, pantalon et bottes. Il est **hors dépôt** et comporte potentiellement des coupures, du corps et des accessoires dans chaque zone. Rien n'est automatiquement compatible Manny.

## Suite nécessaire

1. Affiner manuellement les frontières des vêtements dans Blender/outil équivalent ; éviter les corps coupés et fermer les pièces.
2. Retopologie et normal baking, puis ajustement à Manny, rigging et weight painting.
3. Import sous UE 5.8, création de vêtements équipables et tests d'animations/collisions/écrêtage réels.
4. Ne pas remplacer les assets existants ni pousser de modèles tiers sur le GitHub public sans validation des droits.

**Statut actuel : zéro vêtement réellement équipable dans ANOMALIA ; zéro test Unreal Engine de ces vêtements.** Ce document est un audit, pas une preuve d'intégration fonctionnelle.
