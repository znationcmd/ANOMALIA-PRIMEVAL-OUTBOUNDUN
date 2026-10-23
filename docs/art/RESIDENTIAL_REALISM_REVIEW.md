# Residential realism selection — 23 October 2026

The user rejected the Innerscene detached house shown in the actual Unreal capture as visually too simple. It and the four related Innerscene variants are provisional sources, excluded from the final architectural selection. The 4,760 existing world placements have not yet been replaced.

Four replacement candidates were downloaded from the publicly licensed Objaverse distribution after inspecting their creators' source thumbnails and individual CC BY 4.0 metadata. These are independent assets, not extracted DayZ buildings.

| Candidate | Visual role | Limit before placement |
| --- | --- | --- |
| geodezes, country house | Real scanned timber cottage, aged roof, porch and garden | Source scale, reverse side, terrain skirt and interior unvalidated |
| Jerrad Lancaster, Abandoned House | Scanned brick house with annex, ivy and slate roof | Baked vegetation, terrain skirt, interior and physical scale unvalidated |
| MrUnity, Old Building [3D Scan] | Scanned technical building, tiled walls, graffiti, author describes 4K PBR | Industrial use, not a dwelling; closed doors are not interactive |
| Sengchor, Abandoned House | Detailed collapsed timber structure and debris | Ruin only, not an intact house |

Rejected from this batch: the LiDAR cottage with torn roof/window geometry, and Denys's house with visibly weaker facade/window treatment. Preview selection is not proof of final Unreal appearance.

Run `python scripts/world-features/prepare-sources.py --residential`, then `node scripts/vehicle-assets/prepare-world-features.mjs --residential`. The separate native review workflow imports the prepared GLBs with materials, four LODs and static collision in `/Game/Maps/ANOMALIA_ResidentialPhotogrammetryReview_v1`. It does not replace the populated world automatically. Validate scale against doors, facade quality at walking distance, lighting, UVs, holes, collision and performance before any world rollout.

The source registry pins original bytes and SHA-256. Prepared GLBs bake static transforms and bottom-centre geometry without rescaling. Credits record source, author, license and modifications. CC BY attribution must ship with ANOMALIA; retain the distribution attribution as well.
