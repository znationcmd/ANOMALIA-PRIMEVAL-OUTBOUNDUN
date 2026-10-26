# BMW E39 — native candidate validation

The E39 is a separate review variant. The previously validated Graphite sedan,
its opening driver door, the production map, installation and saves are preserved.

Source: **BMW E39 Free**, Black Snow,
https://sketchfab.com/3d-models/bmw-e39-free-531a5a93da5d493d9918eb36f011c20d

License: CC BY 4.0, https://creativecommons.org/licenses/by/4.0/.
The source file embeds the same creator, license and source URL. Attribution
remains in each derived GLB and CREDITS.md and is attached to imported meshes.
The registered anonymous redistribution is pinned in
`docs/vehicles/named-assets-sources.json`, commit
`0a56de377f02f2574d781f6920fed08d6423ec2f` of `pedrosoandre/carros`.
Source SHA256: `984a9daab49b5a31c45bbc284c657fa5898a010f2201c003358cb6b6f411751d`.

## Implemented locally

- Anonymous verified source download, preserving any existing different file.
- Original body/interior and four separate authored wheel assemblies; brake
  calipers remain on the chassis. This does not create a proprietary BMW rig.
- Deep copies of shared wheel geometry before baking each node transform.
- +X forward/+Y right/+Z up after Unreal import, metre-to-centimetre checks,
  real tire centres, ground-origin correction and hash-guarded asset namespace.
- 109,044 source-instance triangles retained across five parts. Structural
  Khronos validation: five parts, zero errors and zero warnings.
- Reuse the native Chaos road vehicle, its fuel, lights, gears, braking and exit
  code on `/Game/Maps/ANOMALIA_E39DriveReview_v1`.
- Dedicated E39 import/driving evidence in the existing Windows validation
  workflow; all original sedan driving and driver-door requirements remain.

## Acceptance pending

UE import, compilation and real gameplay acceptance are pending the Windows run.
A prepared GLB is not proof of any of these.

The E39 has not been declared a completed playable catalogue vehicle. Its doors,
hood and trunk are not yet separated/animated; entry/exit animations and exact
seat placement are unfinished. Interior geometry exists but its visual quality
must be inspected in actual Unreal captures. Materials are source materials,
not a claim of photoreal approval. Multiplayer, mechanical persistence, packaged
Windows acceptance and production-map integration remain incomplete.

## Reproduce

1. `python scripts/ue5/prepare-bmw-e39.py`
2. `npm ci --prefix scripts/vehicle-assets --no-audit --no-fund`
3. `node scripts/vehicle-assets/prepare-bmw-e39.mjs`
4. `node scripts/vehicle-assets/validate.mjs unreal/SourceAssets/BMWE39Review_v1`
5. On the UE Windows host: run `import-native-demo-sedan.py --e39`, then
   `prepare-chaos-template-review.py`, then `run-chaos-road-review.py --e39`,
   each with `--engine-root` and the same fresh `--output` directory.

The E39 variant explicitly reports openingDoorsTested=false until real animated
panels are implemented and verified. It cannot satisfy the original sedan's
seven driver-door acceptance checks by omitting its door mesh.
