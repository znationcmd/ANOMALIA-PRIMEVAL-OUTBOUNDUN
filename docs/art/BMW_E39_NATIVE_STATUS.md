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

## Real UE 5.8.3 acceptance — 2026-10-26

Code commit: `4a89150609985ae3b03702d834724346f71f2051`.
[Windows workflow 40394672391](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40394672391)
completed successfully. The receipt is
`docs/art/bmw-e39-native-validation-20261026.json`.

| Stage | Actual result |
| --- | --- |
| Local source checks | 126 Python tests; five existing panel-geometry tests pass |
| glTF preparation | Five parts, zero Khronos errors/warnings; repeat preparation preserves identical files |
| UE compilation | Editor and Game targets, UE 5.8.3, exit code 0 |
| Native regression tests | 24 pass: 19 without warnings, five with warnings, zero failures |
| E39 import | Five meshes imported; body/interior 75,564 triangles/46 materials, each wheel 8,370 triangles/four materials |
| E39 gameplay | 26 actual Chaos checks pass, 305 physics samples, real rendered screenshots |
| Existing sedan | Its original driving and seven driver-door acceptance gates pass in the same workflow |
| Packaged release, multiplayer, installation | Not performed |

Measured dry braking: 50.14 km/h to rest in **12.14 m**, 80.27 km/h
in **29.47 m**. Lower friction (0.45) at 80.25 km/h requires **56.10 m**.
These are observations on the controlled proving surface, not a claim that
an E39-specific simulation profile or real-world BMW performance is complete.
The car shares the previously calibrated 1500 kg/320 Nm road prototype profile.

The initial attempt (40392007599) imported the E39 successfully but timed out
without driving measurements: the new map was missing from the native probe's
explicit map/owned-ground allowlist. The corrected build retains standalone,
non-shipping, owned-map and random `chaos-smoke-` server-scope guards. Only the
successful corrected run above is accepted as driving evidence.

## Still unfinished

The E39 is not a completed playable catalogue vehicle. Its doors, hood and trunk
are not yet separated/animated; entry/exit animations and exact seat placement
are unfinished. The existing sedan and its functional driver door remain intact.
The source interior is present, but complete accessibility is not accepted.

Actual screenshots show a recognizable red E39 with its original wheels and
cabin. Photorealism is **not accepted**: source paint is very glossy, glass is
dark, source texture detail is limited, and the image uses a plain engineering
proving surface. No claim of Lumen/Nanite, final PBR presentation or a populated
photoreal world is made. The host is Intel Iris Xe/D3D11; target-PC performance
has not been accepted. Continuous video recording is disabled on this test
host; the retained images are actual Unreal viewport captures.

Manual keyboard/gamepad sessions, multiplayer, mechanical persistence, damage,
part replacement, wipers, packaged Windows acceptance, production-map and Editor
catalogue integration remain incomplete. No installation or save was replaced.

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
