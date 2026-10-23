# World features — 23 October 2026

Eight actual third-party GLBs downloaded and SHA-256 pinned, all individually CC BY 4.0.
Public redistribution: AllenAI Objaverse, ODC-By. Original authors and model license links are retained in `docs/art/world-features-sources.json` and the prepared CREDITS.md.

| Asset | Author | Current role |
| --- | --- | --- |
| Southwark control bunker | artfletch | Interior scan, entrance and terrain cut needed |
| O3/23 concrete bunker | matousekfoto | Exterior scan, ground-patch integration needed |
| Underwater environment | ConradJustin | Local seabed scenery; not an entire ocean floor |
| Copenhagen port scan | Hullken | Brick doorway scan, not dock infrastructure |
| Anchor and winch | Thorus3D | Port detail |
| Full Train Station | ajlakaos | Grey blockout in source preview; not photorealistic production art |
| Modular subway platform | Pablo Campoy | Source units need calibration before world placement |
| Railway station | Dolores | Suspect flat dimensions; quarantine until reviewed |

Source thumbnails were inspected after preparation: the alleged port is a brick doorway; the Full Train Station preview is mostly grey blockout. Neither satisfies the requested photorealistic port/station as supplied. The detailed Dolores station thumbnail does not match its suspect distributed bounds; native verification is required. All models have productionPlacementAllowed=false until reviewed.

The source subway platform is ~11,200 units long, while the train station is ~80 units long. These cannot both be treated as calibrated metres. The station by Dolores has approximately 3.66 × 0.055 × 0.11 source units and is **not approved for placement**. No automatic full-map placement conceals these issues.

Preparation bakes scene transforms into one mesh per source, retains material maps, bottom-centres geometry, and omits one non-surface line primitive in the anchor model. Original files remain unchanged. Preview actors are reduced to at most 30 metres across solely to inspect the models together; this is not physical scale calibration.

## Native import

The dedicated `UE5 licensed world features import` workflow uses the installed engine on the existing Windows runner, shares the native-host concurrency lock, verifies all pinned bytes, imports the prepared models, generates four LODs, preserves existing packages, and saves `/Game/Maps/ANOMALIA_WorldFeaturesReview_v1`.

A fresh receipt with eight models is required. The receipt deliberately declares `IMPORTED_REVIEW_SAVED_SCALE_AND_ACCESS_UNVALIDATED`, and never claims that the large world contains working bunkers, ports or a metro network.

## Full-map state

The published native UE5.8.3 Editor/Game compilation and native tests have passed. Emergency fleet and navigable-water configuration passed. The first populated-world assembly was interrupted by a GPU driver removal; a preserved new-v2 attempt now assembles with NullRHI. Its authored plan contains 4,760 houses and 15,447 foliage/rock placements over 48 × 48 km; actual saved-world completion must be confirmed by its receipt.

Still required before a complete-map claim: successful saved world, visual streaming review, diverse buildings and services on that same world, connected roads/rail, usable metro entrances and tunnels with terrain openings, integrated bunker entrances, functional port berths and navigation, seabed biome materials and decoration across underwater areas, ocean rendering, collision/access tests, vehicle playtests, performance measurements and packaged build. A terrain heightfield alone does not satisfy these criteria.


## Confirmed populated-world save and marine terrain follow-up

Run 39989819736 produced `populated-world.json` with `POPULATED_WORLD_CREATED_NOT_PLAYTESTED`, 4,760 houses, 15,447 vegetation/rock instances, 2,366 streaming clusters and 576 terrain components in `/Game/Maps/ANOMALIA_Inhabited_v2`. The landscape and external actor packages were saved. The overall workflow then failed with a python311.dll access violation **during interpreter shutdown**, after the saved-world receipt was written. This is a confirmed authored save, not a successful clean editor exit or visual playtest. Do not regenerate or delete that map.

Six original 4096 × 4096 CC0 JPGs from Rob Tuytel / Poly Haven are now downloaded and hash-pinned in `marine-terrain-sources.json`: diffuse, OpenGL normal, roughness for Coast Sand 02 and Coast Sand Rocks 02. Source tile width is 15 metres. The new marine material retains forest above +5m, blends sand between +5m and -5m, and blends deeper rocky ground from -25m to -75m. It applies to all 576 existing terrain components after reopening the saved world, without changing heights or actors. This does not provide full seabed decoration, ocean rendering, corals or underwater gameplay.

`run-editor-task.py` releases per-task Python/UObject globals before interpreter shutdown. This is a mitigation to test for the observed shutdown crash, not a confirmed engine fix.

`place-exterior-bunkers.py` proposes one exterior bunker scan per settlement corner, checks native mesh metre bounds, uses the actual quantized landscape height envelope, rejects slopes/water and house overlap, and preserves existing actors. An offline check against the compiled native geography found **23 dry level clear sites out of 27**. Native placement remains unconfirmed until the fresh report says `EXTERIOR_BUNKERS_SAVED_NOT_PLAYTESTED`. This is placement for world review, not final production approval; the source's productionPlacementAllowed=false remains in force. The interior Southwark scan is not buried without a usable terrain opening.

Remaining rendering risk: the existing native terrain resource helper documents that NullRHI imports can save collision relief while visual height resources still need a real GPU layer refresh. The new inhabited world has not yet passed that visual check. Source thumbnails and material graph construction do not validate its in-game terrain appearance.


## Local 3D street authoring

`settlement_roads.py` generates original town street geometry: 8m asphalt carriageways, discrete intersections, dashed paint and 13cm concrete curbs. `build-settlement-roads.py` uses the already verified imported asphalt/PBR and marking materials, generates one static mesh per settlement, assigns structural collision, and saves actors in the existing inhabited world. No house or terrain sample is removed or moved. Water, uneven terrain and house/feature footprint conflicts are rejected. Source geometry is SHA-tagged; existing artist assets are preserved.

An offline execution against the compiled native terrain validated 27 towns, 10,123 accepted 50m centreline segments (506,150m local street centreline), valid finite vertex data and indices, and 25,525,892 bytes of complete generated GLBs. These are **authoring checks, not evidence of native import, saved street actors or driving tests**. Roads do not yet connect towns over the archipelago. Bunker review placements shift to settlement offsets (+365m,+365m), preserving the outer street intersection at (+350m,+350m); all 23 dry level sites remain viable. Existing owned bunker actors may be moved to these offsets; artist-owned objects are preserved.

## Native results and detailed-geometry verification

Run 39992696522 completed successfully: all eight credited world feature meshes were imported with materials and four LODs into the isolated review map. Run 39996311526 then successfully reopened and saved the inhabited map with **23 detailed exterior bunker scans and local 3D street meshes in all 27 towns, totalling 506,150m of street centreline**. These are confirmed authored saves, still not driving or visual-quality approvals. No houses were removed. The Python-global cleanup wrapper completed these native stages without the previous shutdown crash.

The same run failed the marine material guard because reopening a World Partition map did not load all landscape proxies. The corrected marine script now enumerates saved landscape descriptors and explicitly loads only the terrain actors before verifying all 576 components and assigning the new material. It still preserves unknown artist materials and never substitutes a primitive terrain mesh.

`audit-detailed-world.py` reads saved World Partition descriptors and loads all house, vegetation, road and bunker actors in batches of 64. It checks source identity tags, real triangle counts, material bindings, all 4,760 house descriptors, and rejects `/Engine/BasicShapes` meshes or default materials. It saves no packages. This verifies the geometry used by the authored world, not its lighting, appearance, vehicle physics or performance.

`run-visual-review.py` launches the existing native detailed-art review with a real D3D11 renderer at 1280×720, an isolated temporary server identity, and a five-minute timeout. It requests eight day/night views and the existing walk/vehicle checks. This small review scene is intentionally separate from full-world rendering; its outcome must be read from the fresh receipt and actual screenshots.

The current GameDefaultMap remains the older `ANOMALIA_Playable_v1`; a default launch is not evidence that the inhabited map was opened. The populated world is `/Game/Maps/ANOMALIA_Inhabited_v2`. No default-map promotion is made before its rendering and streaming behavior are verified.
