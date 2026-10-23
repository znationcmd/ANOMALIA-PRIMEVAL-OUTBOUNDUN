# ANOMALIA — verified work status, 21 October 2026

## Vehicles and buildings

The complete register retains 210 grouped requests: 86 military-category entries, the separate M1025/Humvee alias and 123 civilian entries. The additional metro and earlier generic requests remain in scope. A grouped request can include several variants. No exact requested vehicle has passed all acceptance criteria yet.

Native run 39618230923 on commit c8782f0f3b8df228cbd074267cd1b43dde15644e passed Editor/Game compilation, native tests (including three metro coaches following a curved spline), real world PIE checks, 33 prototype imports and GPU captures, eight original asset imports/captures/collision checks, and import/GPU capture of the metro lead and coach. The independent urban scene contains 28 buildings. The installed editor project was reopened successfully; 41 existing server files were preserved. This is an editor project, not a packaged Windows game or a complete multiplayer test.

Subsequent run 39620112291 exposed real blockers: intermittent GPU process teardown failure, Windows sharp colour-space failure, setup-python blocked by the host's script policy, and an EditDefaultsOnly property being set on an actor instance. No newer project version was activated on that failed run. Fixes now use a checksum-pinned project-local embeddable Python, Pillow texture conversion in an isolated process, and the authoritative tuning method. The corrected metro track is created in a new v2 review map, preserving the earlier failed map.

Ten licensed historic military reference sources (seven initial, then Humvee, LCAC and Seawolf) and 36 credited car artist variants are prepared for separate review imports. They do not prove final manufacturer scale, identity, rigging, driving, seating, damage or multiplayer. Source references and the complete remaining list are in docs/vehicles/FULL_VEHICLE_WORKLIST.md. Current fixes require fresh native validation.

## PR #6

The branch contains 232 loot catalogue items, 142 species entries, 104 variant entries, 13 Moro-inspired entries and 57 kibble references. Most additions are JSON configuration or legacy JavaScript UI. There is no verified native loot/radiation/creature/crafting/admin/workshop implementation attached to these new catalogues. The three menu entries in JavaScript do not establish an Unreal Tools/Editor/Workshop environment.

The P0 correction rejects non-finite time multipliers, clamps large numeric server fields before integer conversion, gives each temporary save a unique name, and rejects drive/protocol/encoded/control-character mapping paths. Existing configurations and unknown JSON keys remain preserved. Focused JavaScript tests and 11 Unreal source-contract checks passed; a native persistence regression was added and still requires the engine test run.

## Outstanding mission

Real loot actors and persistence; radiation events/protection/rewards; creature assets, AI, taming/riding/breeding; complete recipes and crafting; authoritative admin UI/creative mode/admin tool; native menus and solo/non-dedicated settings; Editor mappings; actual mod package signing/download/mount/update; dedicated server builds, multiplayer privilege tests, CMD Hosting end-to-end integration, installer and full performance/visual review remain unfinished. No 15-server deployment or packaged game is claimed.
