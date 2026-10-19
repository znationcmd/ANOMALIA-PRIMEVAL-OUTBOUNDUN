# ANOMALIA PRIMEVAL OUTBOUNDUN — configuration 0.4

This is a solo, offline prototype running on Three.js and Electron. It is not a DayZ or ARK server and cannot install their Workshop mods or load their proprietary assets/saves.

## Controls

- F2 / ADMIN: local solo administration; item catalog, vehicles, creatures, NPCs, teleport, healing, invulnerability, configuration.
- F3 / GROUPE: adopt/feed a pet, follow/stay/guard orders, recruited survivor orders.
- F5 / VUE: first/third person on foot; cockpit/chase camera when driving.
- E: interact, enter/exit a vehicle, recruit a friendly survivor, collect nearby dropped loot, access the ATM.
- ZQSD/WASD: walk or throttle/steer a vehicle. X: vehicle brake. Space / Ctrl: aircraft ascend / descend. Land before exiting.
- ATM at X 52 / Z 180. All money is fictional game credits. Deposits and withdrawals preserve the balance.

## Editable files

The Windows app copies bundled configuration files into its user-data `config` directory on first launch, without overwriting files that already exist. The exact directory appears under F2 → Fichiers / événements. Close the app before editing these files, then restart. Configuration can also be imported/exported in this menu; imported overrides are retained in the local game save and take priority over disk files.

| File | Implemented fields / behavior |
|---|---|
| types.xml | type name, nominal, min, lifetime (seconds), restock (seconds), quantity, category. Item IDs must exist in the ANOMALIA catalog. Nominal is capped per type and globally for performance. |
| events.xml | HelicopterCrash, TrainCrash, ShipCrash; active, nominal, lifetime, restock. |
| cfgeventspawns.xml | Named event positions: x, z, a (degrees). |
| cfgspawnabletypes.xml | Event cargo item names and counts. |
| cfgeconomycore.xml | Defaults LootEnabled / EventsEnabled toggle the economy systems. The CE registration list is a reference for the bundled files; arbitrary external includes are not loaded. |
| economy.xml | dynamic/events init and respawn flags. load/save flags are documented but currently persistence is automatic in the local game save. |
| globals.xml | LootEnabled, LootMultiplier, VehicleFuelConsumption, CompanionFollowDistance, CompanionTeleportDistance. |
| ai.xml | NPC id, name, friendly/hostile faction, x, z, recruitCost. NPCs patrol, follow when recruited, and engage enemies if line of sight is clear. |
| Game.ini | ANOMALIA section: LootMultiplier, CompanionFollowDistance, TamingSpeedMultiplier, AiDamageMultiplier. |
| GameUserSettings.ini | ServerThirdPersonPlayer, PlayerCharacterFoodDrainMultiplier, PlayerCharacterWaterDrainMultiplier; sg.ResolutionQuality (50–200%), sg.ShadowQuality (0 disables shadows). These are a supported subset, not an ARK configuration interpreter. |
| serverDZ.cfg | hostname is descriptive; disable3rdPerson=1 prevents third-person view on foot. This file does not start or configure a DayZ dedicated server. |
| world-settings.json | schemaVersion=1, playerSpawn x/z, startingItems. Starting equipment applies only to a new game. |
| creatures.json | schemaVersion=1, preferredKibble map and fixed spawns with id/type/x/z/level. Four implemented species: raptor, stegosaur, triceratops, bront. Level is metadata; current creature stats do not scale by level. |

Six ranked croquettes are implemented: basic, simple, regular, superior, exceptional and extraordinary. Equal or higher tiers satisfy the configured preference. Existing herbivore/carnivore recipes remain available for save compatibility. Recipes are ANOMALIA recipes, not exact ARK recipe imports. Rare ingredients can be foraged in jungle zones.

## Unsupported native formats

| Formats | Status in this project |
|---|---|
| init.c / .c | DayZ Enforce Script is not executed. The actual ANOMALIA bootstrap is src/main.js. |
| .pbo | DayZ/Arma package archives are not loaded. |
| .paa / .edds | Engine-specific textures are not imported. |
| .ark / .arkprofile / .arktribe | ARK world, survivor and tribe saves are not imported. ANOMALIA uses its own JSON game state. |
| .uasset / .umap | Unreal assets and maps are not loaded by Three.js. |
| .rpt / .adm | F2 exports ANOMALIA diagnostic/admin text logs with these extensions; these are not DayZ server logs. |

## Current limits

The administration panel is intentionally local and available to the solo player; it is not a multiplayer permission system. Vehicles have arcade movement, fuel, collision checks, simple original models and cockpit instruments. Character, animal and vehicle artwork remains prototype quality, not photorealistic and not equivalent to DayZ/ARK. There are no borrowed game assets, native mod loader, dedicated multiplayer server, high-fidelity flight simulation, or guaranteed 16K runtime performance.
