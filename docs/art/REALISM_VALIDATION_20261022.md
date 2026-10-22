# Native visual replacement — 22 October 2026

The installed playable scene is a prototype. `create_playable_zone.py` currently
loads Lot1 coastal house, villa and garage meshes plus the generic car/SUV/truck
meshes. `PlayableLook_v2` creates foliage crowns, shrubs, rocks and distant hills
from engine spheres; its materials are procedural colour/noise, without scanned
PBR surface maps. Renderer project flags alone do not fix those limitations.

## First concrete replacement batch

A separate map, `/Game/Maps/ANOMALIA_VisualValidation_v1`, uses these pinned sources:

| Asset | Author/source | License | Integration |
|---|---|---|---|
| Detached two-storey house | Innerscene original | CC0 | Detailed shell, openings, windows, roof, structural interior, source material maps |
| Island Tree 02 | Poly Haven | CC0 | Real branch/trunk/leaf geometry and source PBR textures |
| Grass Medium 01 | Poly Haven | CC0 | Detailed ground vegetation |
| Rock Moss Set 01 | Poly Haven | CC0 | Textured rock geometry |
| Forest Ground 04 | Poly Haven | CC0 | Original undulating ANOMALIA terrain, tiled source PBR maps |
| Asphalt 02 | Poly Haven | CC0 | Original ANOMALIA road geometry, tiled source PBR maps |
| Car Concept | Eric Chadwick / Darmstadt Graphics Group GmbH, 2024 | CC BY 4.0 | Detailed static body/interior on existing vehicle pawn; excluded logo texture removed |

Full URLs, source sizes and SHA-256 digests are in `realism-validation-sources.json`.
Prepared data stays outside git; the Windows runner downloads matching sources,
verifies their identity and assembles them. Credits ship with the executable.
The original source files and all earlier game maps remain intact. Entrance leaves
and handles are omitted only in the open-door house review variant. Animated doors,
furnished interiors, final character models, Chaos wheel physics and all-category
vehicle replacements are not completed by this batch.

## Verification and delivery gates

Seven prepared GLBs pass structural glTF validation with zero errors. Foliage and
surface UV warnings still require actual image review. Distant mesh LODs are built
inside Unreal to keep detailed source meshes from rendering at full density afar.

The workflow must import the assets, create/load the separate map, verify its
real Editor game renderer, cook both maps, run existing gameplay/save-restart
regressions, then launch the actual Windows executable on the new map. A dedicated
native probe verifies imported mesh paths without basic-shape fallbacks, character
movement and entry/driving/exit of the detailed car, and writes three fresh GPU
screenshots. The copied installed game repeats that review before its new shortcut
is exposed. All installer tests run with isolated Saved data; existing saves and
previous application versions remain preserved.

The normal gameplay shortcut remains available. `ANOMALIA - Validation visuelle`
opens the new map with its own local save scope, only after successful automated
checks. No whole-world deployment or final photorealism approval is claimed before
the actual screenshots are inspected. The compatibility captures request DX11/SM5;
they are not evidence that Lumen, Nanite or hardware ray tracing are active. DX12
quality/performance, indoor walkability, lighting, texture quality and frame rate
need native visual assessment before promoting this map to the default game.

The status HUD now paints original vector health/blood/food/water/stamina/sleep/
temperature icons in a compact bottom-right strip, using existing native values,
white/yellow/red thresholds and restrained critical pulsing. Bleeding, pain and
illness icons appear only when the existing effects state warrants them. The old
blue frame and permanent percentage text are hidden; diagnostic getters and touch
input remain compatible. Oxygen and consciousness are not fabricated: their
underlying systems still need implementation/integration. The complete requested
main menu, Editor, Tools and Mods overhaul remains separate work; no inactive
button is added to imply those systems are completed.
