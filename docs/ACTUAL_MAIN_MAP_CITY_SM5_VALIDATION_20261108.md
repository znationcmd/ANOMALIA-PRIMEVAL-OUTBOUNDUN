# Validate the actual installed main SKARVIK, not a staging/test map
The user's current instruction makes main-map validation mandatory. Existing C-stage evidence does not establish that all City Sample buildings are installed in the main D world.

Repository source has a routing discrepancy to check on Windows: DefaultEngine.ini boots ANOMALIA_Playable_v1, while the native SKARVIK choice and JSON catalogue point to /Game/Maps/ANOMALIA_Archipelago_v2. Historical advanced work was saved as PRIGIMALIA_SKARVIK_FINAL_v1. The job does not silently select this advanced map, copy it over the original, or create another world.

The preflight reads the installed D Config and native browser routing source. A genuine configured SKARVIK boot map takes precedence; otherwise the installed native SKARVIK world choice is used. Unresolved routing or a missing actual map stops the test. Existing final-map presence is recorded without opening that other map. Four local routing tests passed.

The rendered Editor run explicitly requests DX11/SM5, never NullRHI. It opens only the resolved main map, checks the compiled SKARVIK route, inventories City Sample actor descriptors, and loads candidate actors in groups of six. It records meshes, conventional LOD geometry, material slots, collision mode and asset Nanite settings. Session-only Nanite/Lumen/virtual-shadow overrides are recorded; persistent project settings are not silently rewritten.

PIE is attempted only when the installed GameMode source exposes the isolated automation server-profile option. The runtime GameMode server_id must match the unique test profile, and the PIE world package must still be the exact main map. Screenshot presence, actual D3D11 log initialization, shader/material failures, missing package logs, map hashes and pre-existing save hashes are checked. Reported tick timing is editor tick duration, not a fabricated GPU/FPS benchmark.

Pre-existing saves are backed up locally. Unexpected changed saves are retained as evidence before restoration; newly created saves outside the owned test profile are preserved outside the active save root. Backups and player profiles are deliberately excluded from uploaded artifacts. No PostgreSQL reset, original map replacement, map save, scene creation or actor placement is performed by this validation job.

Full City Sample completeness and full-city SM5 acceptance remain false until expected-source coverage is actually established. A package on disk, a LevelInstance reference, a conventional LOD, or one screenshot does not prove the entire Big City is installed, explorable or rendered. The next concrete map corrections must follow the actual main-map report rather than repeating the historical C-stage experiments.

Primary API references: https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-command-line-arguments-reference ; https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/WorldPartitionBlueprintLibrary ; https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/LevelEditorSubsystem ; https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/AutomationLibrary
