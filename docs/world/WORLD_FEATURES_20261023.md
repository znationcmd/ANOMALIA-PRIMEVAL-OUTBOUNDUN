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
