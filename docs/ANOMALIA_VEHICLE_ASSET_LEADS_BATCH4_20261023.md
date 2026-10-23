# ANOMALIA vehicle sourcing — batch 4 (23 Oct 2026)

**Status: candidate sources only. No downloads, Unreal imports, playable builds, or FPS validation performed.**

| Category | Asset listing | License shown | Notes |
|---|---|---|---|
| UH-60M Black Hawk with cockpit/interior | https://sketchfab.com/3d-models/sikorsky-uh-60m-blackhawk-12b4e525676a49678ac3006b360c8750 | CC BY | ~46.5k triangles; assess rotor rig, cockpit, materials, origin |
| UH-60 Black Hawk | https://sketchfab.com/3d-models/sikorsky-uh-60-black-hawk-ee81eb66006b4d8980d0cf9ff6304b69 | CC BY | ~47.8k triangles; assess visual quality and source rights |
| UH-60M detailed | https://sketchfab.com/3d-models/uh-60m-blackhawk-697d44254628424283c551b4aba908b4 | CC BY | ~1 million triangles; high optimization cost |
| Agricultural tractor | https://sketchfab.com/3d-models/tractor-e9e844f2f9364044a181ce8f38a83dc3 | CC BY | ~69.1k triangles; textured; NoAI restriction: review compliance |
| Agricultural tractor | https://sketchfab.com/3d-models/farm-tractor-02836025b3994747b420d5b790f9512c | CC BY | ~71.3k triangles; check geometry, materials and author rights |
| Agricultural tractor | https://sketchfab.com/3d-models/tractor-f1f01cf3d68f4630956fd89a3b1989b4 | CC BY | ~2.1 million triangles; optimize extensively before game use |

## Exclusions
- https://sketchfab.com/3d-models/mh-x-silent-hawk-a2e8172a314b4a9595a26cb77301b717 — described by uploader as ripped from Call of Duty; **do not use**.
- Explicitly low-poly or toy-like assets do not meet photorealistic final vehicle standards.

## Integration gate
1. Verify provenance, licensing, creator attribution and redistribution limits.
2. Obtain models legally from source; avoid paid assets and third-party source binaries in public GitHub.
3. Review FBX/glTF/texture formats, scale, pivots, LODs, UVs, PBR materials, cockpit, wheels or rotor parts.
4. Import into UE 5.8 via editor or commandlet on machine with Unreal project; preserve existing vehicles and saves.
5. Configure vehicle-specific movement, collisions, interactions, audio, multiplayer and persistence.
6. Build packaged Windows game and inspect real gameplay captures/FPS.
