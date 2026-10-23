# ANOMALIA — Realistic 3D vehicle asset sourcing (2026-10-23)

Status: SOURCES IDENTIFIED ONLY — no models downloaded, imported, rigged, compiled or validated. Do not represent this document as completed vehicle integration.

## Confirmed candidate listings

| Target | Source | Cost/license as listed | Geometry/notes | Integration status |
|---|---|---|---|---|
| BMW E39 | https://sketchfab.com/3d-models/bmw-5-series-e39-mk4-1995-2003-a6a2a783c59b47e1b9d56e08bebcdfc9 | Free download, CC BY (attribution required) | ~1.2M triangles, needs optimization, interior/rig/texture validation | Not imported |
| BMW E39 | https://sketchfab.com/3d-models/bmw-e39-free-531a5a93da5d493d9918eb36f011c20d | Free download, CC BY (attribution required) | ~286.7k triangles; validate materials and source provenance | Not imported |
| BMW M5 E39 | https://sketchfab.com/3d-models/bmw-m5-e39-d3d3e96a4fbf4990af173c5f51b93bd6 | Free download, CC BY listed | ~146.5k triangles; description says sourced from SketchUp 3D Warehouse, verify redistribution rights before use | Not imported |
| Generic sports/hatchback/pickup/SUV/box truck | https://www.fab.com/listings/dc1ada50-2523-44b1-b0e2-a72d14076fb4 | Permanently free Fab listing; accept/check specific EULA | Vehicle Variety Pack, 5 drivable vehicles with interiors, Unreal Engine format | Not imported |
| Automotive PBR materials | https://www.unrealengine.com/news/get-over-280-production-ready-automotive-substrate-materials-for-ue-5-7-free-on-fab | Free as announced by Epic; check version | Materials only; test UE 5.8 compatibility | Not imported |

## Mandatory asset intake checklist

1. Verify legal use in a distributed game, creator provenance, attribution, trademarks and license compatibility. Never redistribute downloaded source assets publicly in GitHub unless license explicitly allows it; use appropriate private asset storage/LFS if permitted.
2. Download only from original authorized source, with necessary user login/EULA acceptance.
3. Inspect FBX/glTF/uasset content, materials, UVs, wheels, interiors, LODs, normals and textures. Optimize triangle count and draw calls for real-time gameplay.
4. Import to Unreal Engine 5.8 project on a non-destructive working branch, retaining existing vehicle behavior and save data.
5. Rig wheels, collision, suspension, camera, seat positions, door animations and Chaos Vehicle controls; connect existing fuel, damage, inventory, replication and persistence.
6. Build/test in UE Editor and packaged Windows executable; measure FPS and capture in-game before/after.
7. Mark each model sourced/imported/rigged/playable/verified separately; no unverified claims of completion.

## Scope still to source

Motorcycles, motocross, quad bikes, buggies, snowmobiles, karts, F1, monster trucks, trucks/trailers, agricultural, emergency, military/armored/air-defense, boats/yachts/submarines, aircraft and helicopters. Named variants require individual rights/quality/compatibility checks.
