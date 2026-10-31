# DRAZOVIA — référence choisie le 30 octobre 2026
La **nouvelle image du joueur (IMG_8278.jpeg, carte iZurvive)** est la référence exclusive de DRAZOVIA pour cette révision. L'ancienne image DRAZOVIA, la carte F.A.L.C et les cartes source d'autres jeux **ne doivent pas être substituées**.

## Valeurs
- Dimensions : 48 × 48 km, surface 2 304 km².
- Terres ≈ 1 604,37 km², eau ≈ 699,63 km², **estimées sur les pixels** et non mesurées sur un vrai terrain.
- Nouvelle RAW16 : `DRAZOVIA_NEW_TOPO_48KM_3025.r16`, 3025², 18 301 250 octets, SHA256 `704222bd547c6ec4a417a20e7b580aaefec1db769d18a4b331adf2ac0d263e9c`.
- Origine graphique : capture plein écran du joueur, recadrée [0,363,709,1091] ; elle comporte l'archipel, le lac de l'est, montagnes et routes.
- Hauteurs **reconstruites/synthétiques** : ce n'est pas le heightmap officiel de la carte ni une altitude mesurée.
- Niveau de vérification : RAW16 générée et intégrité vérifiée **hors Unreal** ; .umap, matériaux, route, 27 villages, collisions, sauvegardes, navigation, météo, gameplay et graphismes en UE5.8 **non validés**.

## Sécurité (indispensable)
- Ne jamais modifier `D:\\ANOMALIA` directement.
- Niveau DRAZOVIA de production protégé : `/Game/Maps/ANOMALIA_Inhabited_v2`.
- Ancienne topographie candidate protégée : `/Game/Maps/ANOMALIA_DrazoviaTopo_Candidate`.
- **Nouvelle version** : `/Game/Maps/ANOMALIA_DrazoviaTopo_NewReference_Candidate` sur une branche isolée.
- F.A.L.C et SKARVIK restent indépendantes et leurs sauvegardes intactes.
- L'ancienne carte possède des villes/infrastructures à adapter ultérieurement ; ne pas les annoncer déjà migrées.

## Procédure native à effectuer sur Windows, PC allumé
1. Vérifier l'état de la PR de migration #48 et la disponibilité de la copie Windows, sans concurrence avec d'autres workflows.
2. Extraire l'archive RAW16 livrée dans la conversation (pas sur GitHub) et copier le seul fichier RAW16 dans `<copie-isolée-UE5>/TerrainSource/DRAZOVIA_NEW_REFERENCE/`.
3. Compiler UE5.8 (classes `AnomaliaZPrigimaliaWorldImportLibrary`), vérifier les erreurs UHT.
4. Exécuter `unreal/Scripts/create_drazovia_izurvive_candidate.py` sur **cette copie uniquement**. Vérifier le SHA256 du fichier source, le .umap candidat et les 576 Landscape Components.
5. Comparer les littoraux côte-à-côte avec la source ; importer réellement matériaux, biomes, eau, routes et bâtiments après validation, sans remplacer les originaux.
6. Tests PIE, cartes sauvegardées, réseau, navigation, 27 implantations et performances avant de fusionner.
7. Garder la nouvelle capture et les assets hors diffusion publique si les droits de reproduction commerciale ne sont pas établis.

## Exécution à distance
On peut committer scripts/tests/doc et fabriquer la RAW16 hors du PC. **L'import UE5 sur un runner auto-hébergé exige que le PC Windows soit allumé et que son runner soit disponible.** Aucune importation ou playtest natif n'est déclaré réussi par ce commit.
