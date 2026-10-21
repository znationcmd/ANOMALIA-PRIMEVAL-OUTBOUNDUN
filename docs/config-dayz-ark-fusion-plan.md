# ANOMALIA — fusion des configurations DayZ / ARK (sans perte)

## Objectif
Un réglage canonique par domaine, avec lecture des anciens fichiers comme **alias d'import**, sans supprimer, renommer ou écraser les configurations et sauvegardes existantes. Les fichiers DayZ/ARK sont des formats de référence, pas des moteurs exécutés par Unreal.

## Fichiers canoniques
- `config.json` : identité du serveur, joueurs, ports, PVE/PVP/RP.
- `GameUserSettings.ini` : options générales, difficulté, faim, soif, stamina, multiplicateurs.
- `Game.ini` : dinosaures, apprivoisement, élevage, hybrides, construction, crafting.
- `types.xml` : objets, loot, tiers, quantités, réapparition.
- `events.xml` : crashs, zones radioactives, événements temporaires.
- `vehicles.xml` : tous les véhicules, pièces, carburant et spawns (le fichier existant est actuellement centré sur les navires : ne pas supposer qu'il gère déjà tous les véhicules).
- `admin_config.json` : rôles et permissions.
- `mods.json` : contenus additionnels.

## Références conservées
- `cfggameplay.json` : paramètres de gameplay DayZ-like et stamina, à migrer vers un schéma canonique avec compatibilité de lecture.
- `cfglootspawn.xml`, `cfgspawnabletypes.xml`, `loot_tiers.json`, `loot_items_catalog.json` : détail du loot ; ne pas perdre les points de spawn, cargaisons et définitions.
- `cfgeventspawns.xml`, `radiation_zones.json` : positions et paramètres détaillés des événements.
- `cfgeconomycore.xml`, `globals.xml`, `economy.xml` : économie.
- `creatures.json`, `ai.xml`, `dinosaurs/*.json`, `dino_*_catalog.json` : données volumineuses des créatures, variantes, recettes et comportements.
- `serverDZ.cfg` : alias d'import ; `GameUserSettings.ini` et `Game.ini` sont des fichiers ANOMALIA personnalisés.

## Règles de fusion à implémenter
1. Faire un inventaire des lecteurs et des écritures des configurations avant de déplacer un fichier.
2. Valider les schémas XML, JSON et INI ; sauvegarder l'original avant migration.
3. Définir des priorités explicites : paramètres du serveur > import des anciens alias > valeurs par défaut ; signaler les conflits.
4. Migrer un domaine à la fois et tester les valeurs effectivement appliquées dans le serveur Unreal dédié.
5. Conserver les chemins historiques en lecture tant que des consommateurs les utilisent. Aucun effacement ni fusion aveugle.
6. Tester la stamina sous charge, le loot par tier, les recettes de croquettes, les véhicules et les événements radioactifs en multijoueur.

**État actuel : plan d'architecture uniquement.** La fusion effective des lecteurs Unreal, la suppression des doublons et les tests de bout en bout restent à réaliser. Ne pas déclarer le projet migré.
