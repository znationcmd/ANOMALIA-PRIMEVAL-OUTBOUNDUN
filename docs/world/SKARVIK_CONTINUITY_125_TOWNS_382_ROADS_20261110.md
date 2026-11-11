# SKARVIK — continuité réelle du monde 48 × 48 km (10 novembre 2026)

**Ce travail continue la carte existante** `/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1` de la branche `feature/skarvik-citysample-sm5-20261031`, sans refaire un second SKARVIK. Les niveaux UE5 et City Sample sont protégés, les 7 îles existantes sont conservées. Aucun nouveau .umap n'a été écrit par ces scripts.

## Dernier audit de données natives / conception
Sources : `public/config/skarvik-world-layout-48km.json` et `public/config/skarvik-final-coastal-migration-125-sites.json`.

- **125 implantations** à préserver (ville City Sample, agglomérations, villes, villages).
- **67 centres** proposés au déplacement de leurs coordonnées initiales en raison du nouveau littoral. **Ces déplacements ne sont pas approuvés ni appliqués automatiquement**.
- **382 liaisons routières régionales** au registre.
- **137 liaisons** n'ont pas de polylignes sources : elles ne peuvent pas être créées physiquement en se contentant de joindre deux noms.
- Sur **245 polylignes** présentes, **236 possèdent au moins une extrémité éloignée de plus de 250 m du centre côtier cible**. Ce sont des besoins de vérification/raccordement sur la géométrie finale, pas une preuve que 236 routes déjà construites sont cassées.
- Le contrôle par rectangles **signale des chevauchements potentiels entre emprises** pour des localités. Il ne remplace pas l'audit de collisions de vrais bâtiments natifs.

Les données existantes situent la ville City Sample **4 × 4 km**, centre `[2, -8]` dans SKARVIK **48 × 48 km**. Le système original SKARVIK exprime Unreal en centimètres : `UE X = eastKm × 100000`, `UE Y = -northKm × 100000` (**différent du kit RACCONIA**). Préserver la source `/Game/Map/Big_City_LVL`, ses dépendances et les autres plans .umap.

## Première série prioritaire : 8 sites à examiner dans UE5

La sélection automatique conservative retient seulement les propositions terrestres sans chevauchement rectangulaire évident et avec marge côtière de 300 m ou plus. Elle propose à **valider visuellement** :

1. BRUMEPIERRE
2. MERIVALS
3. ARBELIN
4. ROCHESECHE
5. ERGUED
6. NORDFJELL
7. MALPHARE
8. LAUZEVEIL

**Les 8 restent non approuvés** : terrain, constructions d'origine, collisions, végétation, littoral et réseau routier doivent être vérifiés avant d'implanter les vraies maisons. Les **59 autres propositions** nécessitent un traitement de conflit, relief ou côte et ne doivent pas être effacées ni déplacées automatiquement.

## Nouvelle vérification automatique

Le script de lecture seule `scripts/plan_skarvik_continuity_next_batch.py` vérifie les deux sources originelles avant toute sortie et refuse de remplacer un dossier existant. Exécution depuis la racine de la branche SKARVIK :

```powershell
python scripts/plan_skarvik_continuity_next_batch.py --output "C:\STAGING\SKARVIK_48KM_CONTINUITE_NOUVELLE"
```

Le générateur fournit :
- `skarvik-next-native-survey.json` — audit complet des 125 localités, des 382 liaisons, des avertissements et empreintes SHA256 des sources ;
- `skarvik-relocations-review.csv` — **67** centres source/cible, coordonnées natives UE5 cm et alertes ;
- `skarvik-road-endpoint-gaps.csv` — **382** liaisons, risques de raccordement, routes sans tracé.

Le workflow `SKARVIK 48km - coastal road and town continuity QA` génère ces fichiers en artefact GitHub pour l'examen manuel.

## Construction native qu'il reste à effectuer

1. Vérifier le monde final **déjà existant** et les sauvegardes/acteurs World Partition (sans cloner SKARVIK).
2. Inspecter en vue aérienne les huit implantations prioritaires, leurs rectangles d'emprise et leur altitude finale. Rejeter les intersections ou zones immergées.
3. Préserver tous les vrais bâtiments, routes et 7 îles déjà installés. Réutiliser leurs meshes, ne pas créer de maisons provisoires en double.
4. Recalculer les raccords des **245** polylignes sur le littoral final ; inventorier les ponts et traversées maritimes ; dessiner les **137** liaisons sans géométrie en fonction du vrai relief.
5. Vérifier collisions terrain/arbres/réseau, LOD/HLOD, World Partition, City Sample sans PNJ et sans trafic, SM5, conduite Chaos, tests PIE et paquet Windows.

**Le bilan reste un audit de sources GitHub, pas une validation de la carte finale native sur le PC.**
