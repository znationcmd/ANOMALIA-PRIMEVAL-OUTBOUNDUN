# BMW E39 — same model, native driving and driver door

Current work: the remaining three doors, bonnet and boot lid are prepared in
`BMWE39Review_v5`, with eleven parts total. The previous driver leaf and all
four wheels are byte-identical. Horizontal/vertical axes and five stable extra
panel components are wired into the native actor.

First all-panel attempt, code `44246f7115d4fce34417c923654dac46ac4094ae`,
[workflow 40404336275](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40404336275),
compiled both targets and passed native tests/reference driving. It imported
all eleven E39 parts, verified the driver/front-passenger doors, then failed
on targeted rear-left opening. That failure is not whole-vehicle acceptance.

Correction `1bdccbdd92c6a2f70e4afadb0eadad15158a4a50` uses real rear-door
surface targets in the test fixture instead of bounding-box centres, which
can lie behind one-sided interior geometry. Gameplay still requires the actual
server ray hit, distance and player validation. New painted panels gain inward
1.2 mm metal skins and edge strips; glass gains 1.5 mm inner skins. Original exterior
area conservation and added shell area/counts are recorded separately. The
source, driver leaf and wheels remain intact. Local validation: 126 Python
checks, nine geometry tests, eleven GLBs with zero Khronos errors/warnings.
The v4 native run
[40407227685](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40407227685)
compiled both targets and passed 24 native tests/reference driving, but its
original-bounds gate rejected an overly thick added mirror-housing skin.
Current correction `ffcf39b5923f3fff0c5addc7c405fafb58b32967` uses 1.2 mm metal;
the composed local envelope matches the original to under 0.000001 cm, while
the unchanged native tolerance remains 1 cm. No production art was overwritten.
The v5 run
[40408724048](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40408724048)
passed compilation, native tests, import and the original-bounds gate. Driver,
front-passenger and rear-left cycles passed. Rear-right opened but its closing
interaction failed; the final viewport shows the chassis had been launched.
That is a failed physical test, not accepted gameplay.

The next correction keeps moving leaves out of the rigid-body solver with
`QueryOnly` collision, retaining character sweeps, visible mesh interaction
rays and obstruction queries. They are kinematic animated leaves; neither
mass nor impulses should be coupled back into the chassis. Native review now
requires the same policy for all six leaves, capsule-sweep blocking when closed,
a clear swept aperture when open, and chassis drift/speed bounds during every
extra-panel cycle. Run
[40410289425](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40410289425),
code `2e9d90ac2766739c5dda93fca0c0dc3f4bf746bc`, compiled Editor/Game and
passed native tests/reference driving. Its stronger gate failed at front-right:
5.76 cm chassis drift and 121.40 cm/s speed. Query-only leaf collision therefore
does not establish that the stationary instability is fixed.

Next validation configures native asynchronous physics at 120 Hz, independent
of rendering/readback stalls, and adds a twenty-second unoccupied stationary
observation before any panel interaction on every review vehicle. It records
idle samples and the actual loaded physics settings; all previous contact,
driving, opening, capsule-collision and stability gates remain required.
This latest physics configuration and extended idle gate are not yet compiled
or accepted; do not report the E39 as completed. The verified v2 results below do not validate these changes
or the five new panels.

**Keep this E39.** The same Black Snow source, body, interior and four wheels
are retained. v2 derives a driver leaf from that model; it does not substitute
a different car. v1 and its successful driving evidence remain preserved.

Complete and verify the E39 before extending to the other requested vehicles.
Each later model needs a detailed licensed source, native import, appropriate
physics for its category, interior/crew/interactions and actual game acceptance.
Reuse compatible components; catalogue names alone do not count as delivery.

## Latest real UE 5.8.3 acceptance — 2026-10-26

Code: `87f6a0d24372ff013f642f7d480cddf7eea43a05`.
[Windows workflow 40399566771](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40399566771)
completed successfully. Machine-readable evidence:
`docs/art/bmw-e39-driver-door-native-validation-20261026.json`.

| Stage | Verified result |
| --- | --- |
| Local checks | 126 Python tests and seven geometry tests pass |
| Prepared parts | Six GLB files, zero Khronos errors/warnings; repeat preparation preserves identical files |
| UE compilation | Editor and Game, UE 5.8.3, both exit code 0 |
| Native tests | 24 pass: 19 without warnings, five with warnings, zero failures |
| Real import | Body/interior, real driver leaf and four original wheels in a separate v2 namespace |
| Actual E39 gameplay | 33 checks pass, including seven driver-door checks, 318 physics samples |
| Visual inspection | Real viewport capture inspected: same red E39, driver leaf open on the correct side, cabin opening and original rims visible |
| Existing vehicles | Reference driving and the Graphite driving/driver-door requirements pass in the same workflow |
| Complete vehicle, multiplayer, package, installation | Not accepted/not performed |

The source door includes its painted surfaces, glass, mirror and inner lining.
Disconnected authored islands are retained whole; shared window-frame surfaces
are partitioned with interpolated original attributes. The source body surface
area, 79.649182720245 m², is conserved between the leaf (1.911817677998 m²) and
remaining body (77.737365042248 m²). Closed body + hinge-offset leaf recompose
the original native bounds; all four wheel files remain byte-identical to v1.

Hinge: chassis-local `(92.4, -80, 90)` cm, +70° opening. The existing generic
`UAnomaliaVehiclePanelComponent` supplies server-owned angular motion, moving
convex collision, locking, obstruction checks and replicated angle/state.
The E39 review uses the same targeted server interaction as E outside and the
same owning-driver O command inside. No invisible-panel opening substitute.
The six-part importer alone does not count as an opening or gameplay test.

The actual game verifies the installed panel, original closed bounds,
closed/open/restored collision, locked rejection, and operation from the seat,
then repeats real Chaos acceleration, steering, gears, braking, handbrake,
lights, fuel depletion/refuelling and moving exit with the original survivor.

| Measured E39 braking on controlled surface | Distance | Time |
| --- | ---: | ---: |
| 50.30 km/h, friction 0.9 | 12.17 m | 1.70 s |
| 80.07 km/h, friction 0.9 | 29.53 m | 2.64 s |
| 80.15 km/h, friction 0.45 | 55.69 m | 5.03 s |

The same calibrated 1500 kg/320 Nm prototype profile is reused. These results
prove functioning Chaos physics on the proving ground, not complete real-world
BMW calibration. The engineering surface is not the requested photoreal zone.
Continuous recording is disabled on the validation host; screenshots are actual
Unreal captures, not generated imagery. Only `driver_door` is validated:
`openingDoorsTested=true` does not mean that every vehicle panel is complete.

## Source and preservation

**BMW E39 Free**, Black Snow:
https://sketchfab.com/3d-models/bmw-e39-free-531a5a93da5d493d9918eb36f011c20d

CC BY 4.0: https://creativecommons.org/licenses/by/4.0/.
The GLB embeds the creator, license and original URL. Attribution remains in
all derivatives, CREDITS.md and imported asset metadata. Anonymous redistribution
is pinned in `docs/vehicles/named-assets-sources.json`, commit
`0a56de377f02f2574d781f6920fed08d6423ec2f` of `pedrosoandre/carros`.
Source SHA256:
`984a9daab49b5a31c45bbc284c657fa5898a010f2201c003358cb6b6f411751d`.

Original v1 preparation deep-copies shared wheel geometry before transformation,
corrects forward axis and ground origin, preserves the body/cabin and separates
four authored wheel assemblies. Brake calipers remain on the chassis.
Hash, scale and origin guards preserve artist assets. The Graphite sedan and
its door, production map, installation and saves remain intact.

Historical v1 driving: code `4a89150609985ae3b03702d834724346f71f2051`, successful
[workflow 40394672391](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40394672391),
26 driving checks, receipt `docs/art/bmw-e39-native-validation-20261026.json`.
The earlier failed run 40392007599 imported v1 but timed out with the probe
inactive; it is not driving evidence. The corrected probe retains standalone,
non-shipping, explicit owned-map and temporary server-scope guards.

## Still unfinished

The E39 is not yet a completed playable catalogue vehicle. Three other doors,
hood and trunk, exact seat positioning, entry/exit animations and a visible
animated human driver remain unfinished. Entry currently uses the existing
crew possession path; the complete animation/access sequence is not accepted.

Source paint is very glossy, glass is dark and texture detail is limited.
Frame/seam finishing, interior presentation, realistic sounds and final PBR
quality remain to review. Photorealism is not accepted. The host is Intel Iris
Xe/D3D11; no Nanite/Lumen or target-PC performance acceptance is claimed.

Manual keyboard/gamepad sessions, multiplayer, vehicle/panel persistence,
locks/keys, damage, replaceable parts, repairs, dirt, wipers, packaged Windows
acceptance, production-map and Editor-catalogue integration remain incomplete.
No existing installation or save was replaced, no force push or expense.

## Reproduce

1. `python scripts/ue5/prepare-bmw-e39.py`
2. `npm ci --prefix scripts/vehicle-assets --no-audit --no-fund`
3. `node scripts/vehicle-assets/prepare-bmw-e39.mjs`
4. `node --test scripts/vehicle-assets/mesh-islands.test.mjs scripts/vehicle-assets/panel-geometry.test.mjs`
5. `node scripts/vehicle-assets/prepare-bmw-e39-panels.mjs`
6. `node scripts/vehicle-assets/validate.mjs unreal/SourceAssets/BMWE39Review_v2`
7. On the UE Windows host: run `import-native-demo-sedan.py --e39`, then
   `prepare-chaos-template-review.py`, then `run-chaos-road-review.py --e39`,
   each with `--engine-root` and the same fresh `--output` directory.
