# SKARVIK -> City Sample Big City, SM5, sans trafic ni PNJ mobiles

**Demande corrigée (31 octobre 2026) :** SKARVIK doit garder une superficie jouable de **48 × 48 km (2 304 km²)**. Le contenu **complet de la grande ville City Sample (~4 × 4 km)** doit être intégré à l'échelle 1:1 dans une zone de cette carte, sans circulation ni PNJ mobiles. Conserver routes, bâtiments, tunnels, ponts, trottoirs et accessoires statiques. Ne jamais réduire le monde SKARVIK aux seules limites urbaines, ni étirer la ville sur 48 km.

**Statut : PRÉPARATION, aucune importation native effectuée.** Ne pas confondre « cible configurée » et « monde réellement installé ». Sur GitHub, les fichiers binaires Epic City Sample ne sont pas présents. L'ancien SKARVIK, `/Game/Maps/ANOMALIA_Archipelago_v2`, reste actif tant que les vérifications ci-dessous échouent. Conserver les sauvegardes et la possibilité de retour arrière. DRAZOVIA et les quatre autres mondes ne sont pas modifiés.

## Étapes d'exécution dans le PC Windows

1. Vérifier que City Sample est installé comme **projet Unreal local** depuis Epic Games/Fab et contient `Content/Map/Big_City_LLV.umap` (certaines versions emploient `Big_City_LVL`) **avec** ses données `Content/__ExternalActors__`, textures, matériaux, meshes, HLODs et autres dépendances.
2. Exécuter l'audit **en lecture seule** : `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/ue5/audit-skarvik-citysample-sm5.ps1 -ReportPath "$env:TEMP\skarvik-city-audit.json"`. Si la source est à un chemin non standard, passer `-CitySampleProject "D:\...\CitySample.uproject"`. Examiner le rapport avant toute copie.
3. Faire une sauvegarde vérifiée et travailler uniquement sur la **copie isolée du projet**, jamais directement dans `D:\ANOMALIA`. S'assurer qu'aucun Unreal Editor/Build n'est en cours et que l'espace libre est suffisant.
4. Depuis City Sample dans Unreal Editor, utiliser **Asset Actions > Migrate** en incluant toutes les dépendances vers la copie ANOMALIA’Z. La grande ville est World Partition / One File Per Actor : la copie d'un seul `.umap` ne constitue **pas** une migration complète. Vérifier les external actors, Data Layers, HLODs et les plugins requis avant d'ouvrir la carte.
5. Configurer sur la copie une cible **D3D11 / SM5**, désactiver Nanite, Lumen et Virtual Shadow Maps; disposer des véritables **fallback meshes**, éventuellement reconstruire les LODs, adapter les matériaux, simplifier les ombres et les textures. **City Sample s'appuie massivement sur Nanite**, il peut être trop lourd en SM5 ou afficher des meshes de secours de qualité insuffisante.
6. Désactiver à la source le spawning **Mass Traffic** et **Mass Crowd** (acteurs de spawn, Data Layers, Blueprints et chargement de gameplay si concernés); laisser les voitures garées uniquement en décor statique si souhaité. Les curseurs de densité à zéro ne suffisent pas à prouver l'absence durable de spawn. Ne pas retirer les routes et bâtiments.
7. Connecter le GameMode, personnage, collisions, PlayerStart, sauvegardes et déplacements ANOMALIA’Z à la ville. Faire des tests **PIE et build packagé** : présence de la ville entière, streaming World Partition, absence de véhicules mobiles et de PNJ animés, FPS et mémoire, sauvegarde/rechargement.
8. **Préserver les 48 × 48 km de SKARVIK** : intégrer City Sample à son échelle native d'environ 4 × 4 km, à l'intérieur d'un nouveau monde 48 × 48 km, en prévoyant des terres, forêts et zones de survie autour. Le terrain environnant et les raccords routiers doivent être réalisés et testés ; ce n'est pas une simple conversion de dimensions. Conserver le streaming World Partition sur toute la superficie, vérifier les transitions, la navigation et les volumes.
9. **Seulement après réussite**, faire pointer l'entrée publique **SKARVIK / archipelago-v2** vers le nouveau niveau 48 × 48 km validé. **Ne modifier ni `widthKm` ni `heightKm` dans le catalogue**, ni l'identité des sauvegardes. Conserver les fichiers originaux 48 × 48 km séparément pour retour arrière.

## Limitation matérielle

Le PC Intel Iris Xe / 16 Go RAM n'atteint pas les recommandations officielles Epic pour City Sample (64 Go RAM, RTX 2080-class / 8 Go VRAM). Supprimer circulation et foule réduit la simulation, **pas** toute la géométrie statique : une ville complète SM5 fluide sur cette machine **n'est pas garantie**.

Documentation officielle : https://dev.epicgames.com/documentation/unreal-engine/city-sample-project-unreal-engine-demonstration

Ce dossier ne contient que des scripts et des métadonnées. Aucun asset sous licence Epic n'est poussé dans le dépôt public.
