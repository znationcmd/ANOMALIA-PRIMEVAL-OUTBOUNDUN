# BMW E39 — same model, six opening leaves and native driving

## Accepted v5 native baseline — 27 October 2026

Code `e5bcfa65355f4b3aa92fb99aaa2c0f8f9ce845ea`,
[Windows run 40493715250](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40493715250).
Editor and Game compile under UE 5.8.3. All 24 native tests pass (19 clean,
five with warnings). The reference vehicle passes; the original-sedan regression also passes
35 checks, including its driver leaf. The entire Windows workflow succeeds.

The same E39 passes **61 real gameplay checks** and 313 driving samples.
All four doors, bonnet and boot open/close on their authored axes, retain
server lock/aim checks and restore character collision. A real survivor walks
against the closed boot and stops without launching the chassis. The owning
driver operates the driver leaf from the seat; the complete calibrated Chaos
acceleration, steering, gears, braking, lights, fuel and exit sequence passes.
Across 355 panel samples, maximum chassis drift is 0.41774 cm and speed
0.08431 cm/s. This is isolated mechanical acceptance, not a completed vehicle,
photoreal scene, multiplayer, packaged-game or production-installation acceptance.

The successful candidate removes the unproven production pose-mode and
character-force experiments. Only the test character's fixture placement is
isolated, with collision restored and a four-second settling interval before
unchanged physical gates and targeted opening commands. This result supports
the relocation/settling change; it does not uniquely identify an engine-level
root cause. No chassis transform/velocity is reset or clamped.

The boot-open viewport was inspected: the same red E39 remains on the proving
ground, with the actual lid raised. Engine-bay and boot finishes are visibly
incomplete. All six leaves are closed, unobstructed and at zero degrees at the
end of the run. Native artifacts: build `12730321731`, reference `12730577186`,
E39 `12729594152`. Authoritative v5 receipt:
`docs/art/bmw-e39-six-panels-native-validation-20261027.json`.

## v7 cargo-lining correction — native validation pending

Source geometry inspection distinguishes the original `frame` cargo tub from
`mottled` lining on the lid. v6 incorrectly leaves the latter covering the
opening. v7 keeps the tub/frame fixed while restoring lid-envelope felt to the
moving lid. Only body and boot files change; nine accepted parts remain
byte-identical. Original surface area is conserved; no replacement car or
invented cargo box is introduced. v5/v6 namespaces and proofs remain intact.

A new exact mesh audit casts three rear eye-height sightlines at the original
cargo floor, with the lid closed and open. It rejects v6 (first open hit is the
fixed opaque lining) and passes v7 (closed first hit is lid; open first hit is
the original fixed cargo floor). This CPU audit is not native or visual
acceptance. Eleven GLBs have no Khronos errors/warnings and 154 Python tests
pass. Native acceptance and actual viewport inspection remain pending.
Receipt: `docs/art/bmw-e39-cargo-lining-v7-20261027.json`.

## Latest v6 native mechanical acceptance — visual finish incomplete

Code `c05f0963bd596ecdf282e17538e4dc67f2275ca0`,
[Windows run 40498160021](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40498160021),
completed successfully under UE 5.8.3, including Editor/Game compilation,
native tests, reference driving, E39 driving and original-sedan regression.
The same E39 passes 61 gameplay checks, 324 driving samples and 328 panel
samples. Maximum panel-cycle chassis drift is 0.43305 cm; speed is
0.08431 cm/s. All six leaves finish closed and unobstructed. Actual braking
from 80.31 km/h at friction 0.9 takes 30.6551 m; from 80.21 km/h at friction
0.45 takes 57.2985 m. Native E39 artifact: `12731679797`.

The accepted v5 source hashes are pinned in `bmw-e39-accepted-v5-parts.json`
and were compared with the real Windows import report. v6 leaves 2.48663
square metres of original lining and aperture frame on the fixed body.
Only body/lid files change; four wheels, four doors and bonnet are byte-identical.
Original area, closed bounds, source identity and axle positions are preserved.
The real rear-facing painted-lid target passes native aimed interactions.

The actual `actual-panel-trunk-open.png` viewport was inspected. The painted
lid rises without carrying the entire lining, but a broad opaque inner surface
still obscures the cargo opening. Detailed usable cargo-volume finish is **not
accepted**. This is a mechanical refinement, not a completed boot interior.
Eleven GLBs have zero Khronos errors/warnings and 154 Python tests pass.
Receipt: `docs/art/bmw-e39-compartment-candidate-20261027.json`.
Detailed engine bay, human animations, multiplayer and packaged/installed
acceptance remain unfinished. No production map or installed game was changed.
The v5 acceptance above remains the historical baseline, with its own exact
measurements and artifacts; do not attribute those measurements to v6.

## Earlier attempts (not accepted at the time)


Historical preparation: the remaining three doors, bonnet and boot lid were prepared in
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
Revision `32575224b4ba545d1466f5fc25b403625ae7a308`,
[workflow 40412772847](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40412772847),
compiled Editor/Game in UE 5.8.3 and passed 24 native tests (19 clean, five with
warnings). The reference vehicle passed 27 checks, including twenty seconds
stationary: 89 samples, maximum speed 0.02442 cm/s and drift 0.29643 cm,
followed by 322 physical driving samples. The loaded async step is 0.008333333 s.

The run ended with failure at 22:46:08 UTC on 26 October, while GitHub still
reported the preceding original-sedan preparation/import step as in progress.
Attempt 1 has no final job log, and its exact interruption cause remains unknown.
Attempt 2 completed on 27 October at 07:26 UTC on `ANOMALIA-PC`.
It compiled both targets, passed native tests/reference driving and imported
all eleven E39 parts. The E39 passed the twenty-second idle and driver-leaf
checks, then failed the front-right panel stability gate: drift 6.16715 cm,
speed 126.18403 cm/s. Evidence artifact: `12717285107`, job `122061181473`.
The async cadence therefore did not resolve opening-cycle instability.

The next diagnostic correction places kinematic leaves on a dedicated
`VehiclePanel` object channel and explicitly excludes only that channel from
Chaos suspension ray queries. Character blocking and visibility interaction
remain enabled; dynamic road surfaces remain eligible for wheel support.
This is a hypothesis under test, not a confirmed cause. Per-frame panel-phase
position, velocity, delta time, leaf angle and four wheel spring/contact outputs
are retained before the unchanged stability gate, including the failing frame.
Native compilation and acceptance of this correction are still pending.

This latest E39 configuration has therefore not passed six-panel acceptance.
Receipt: `docs/art/bmw-e39-all-panels-validation-20261027.json`.
Do not install or report the E39 as completed.
The verified v2 results below do not validate these changes
or the five new panels.

## Panel-channel native attempt — 27 October 2026

Revision `7a8602c474f05383d83777101a738fdf98f9f1a8`,
[run 40469835323](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40469835323),
compiled Editor/Game and passed 24 native tests (19 clean, five with warnings),
source checks and reference driving. All eleven parts imported. The driver
leaf, three additional doors and bonnet completed opening/closing checks.
This does not prove the filter alone solved the earlier nondeterministic issue.

The boot lid failed at 6.09 degrees: in one sampled frame the chassis moved
725.77 cm and reached 28508.43 cm/s. Previous bonnet closure samples had balanced
spring forces and zero/near-zero chassis speed. Evidence artifact `12718547212`
retains 292 panel samples, four accepted additional panel IDs and real captures.
No complete E39 or six-panel acceptance is claimed.

The next hypothesis is CharacterMovement's automatic push/repulsion coupling.
The survivor now uses blocking capsule movement with automatic physics pushing
disabled. This applies to walking against simulated bodies generally; explicit
gameplay interactions are retained. The chassis is not frozen, velocity-clamped
or repositioned by the acceptance gate. Every existing stability limit remains.
An additional acceptance sequence uses actual walking input against the closed
boot lid: the survivor must move at least 25 cm, stop before the trunk aperture,
and leave chassis drift/speed under the existing limits. Panel telemetry also
records survivor velocity, location and movement base. This correction still
requires native compilation and gameplay acceptance.

## Character-push native attempt — 27 October 2026

Revision `93f05797062a108ef4431f9771a06a3d47454086`, run `40472920370`,
compiled Editor/Game, passed native tests and reference driving, and imported
the E39. Its idle observation passed. It failed at the first closed-driver-leaf
aperture check, before the commanded opening, so it did not test the boot or
walking-contact acceptance. Artifact `12720450349` retains the actual report
and viewport. The viewport shows the driver leaf already open. This is not
proof of a missing closed-leaf collider or a successful push-force correction.
Whether stored fixture state or live keyboard input caused the open leaf is
not yet determined.

The next change affects only the explicit standalone proving-ground probe:
initialize its fixture leaves closed before the twenty-second idle observation,
disable live pawn keyboard input during the automated review, and retain final
open/angle/obstruction states in every report. Measured opening/closing still
uses the same targeted server commands; normal production input is unchanged.
No stability/collision threshold is relaxed. Native verification is pending.

## Isolated-input native attempt — 27 October 2026

Revision `098dca60faf8a6fff340ac77bb000fd4d06e6a19`, run `40475542625`,
compiled Editor/Game, passed native tests and reference driving, and imported
all eleven E39 parts. The report confirms closed fixture initialization and
isolated keyboard input. All four doors and the bonnet completed their cycles.
The boot again launched the chassis near six degrees: 766.95 cm drift and
22532.03 cm/s speed. Artifact `12721900245` retains the real report/captures.
The survivor had zero horizontal velocity and no movement base at the boot,
with automatic character physics interaction disabled. That experiment did not
resolve the failure; the unrelated global character setting is now removed.

The next candidate changes only animated leaf pose updates to
`ETeleportType::TeleportPhysics`, retaining the existing angular obstruction
samples, query-only collision and all acceptance limits. This mode updates
collision geometry without deriving physics velocity from pose changes:
https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/Components/USceneComponent/MoveComponent/1
The raw and effective panel body owners and actual WeldParent state are now
recorded on every panel sample to detect hidden native coupling. No chassis
velocity/transform is assigned or clamped. This is an unverified hypothesis;
complete six-panel, walking-contact and driving acceptance is still required.

## Pose-mode native attempt — 27 October 2026

Revision `337a36efad731b1217a22ae4eb4f7404ec408495`, run `40478504861`,
compiled Editor/Game and passed native tests/reference driving. Eleven parts
imported, idle/driver checks passed, then front-right opening failed stability:
24.43 cm drift and 626.67 cm/s speed. Artifact `12722358347` records distinct
raw/effective `RoadPanel1` bodies and `WeldParent=false`. Neither a hidden weld
nor the proposed pose mode is established as the root cause.

The impulses occur within the first two samples after the test character is
relocated across the vehicle. The next candidate isolates this fixture action
before commanding any opening. Only while placing the test character, its
collision is disabled, movement/base reset and its collision recreated at the
destination. It is restored before four seconds of normal simulation; the same
50 cm / 100 cm/s chassis limits must pass before the server opening command.
Those six pre-opening acceptance checks are required by the Python driver.
All real opening, closing, capsule blocking, walking and driving gates remain.
No vehicle transform/velocity is set, and no collision is disabled during a
measured interaction. Production character movement is unchanged. The unproven
production panel-pose change is removed. This remains a hypothesis under test;
no complete E39 or six-panel acceptance is claimed.

## Fixture candidate compilation — 27 October 2026

Revision `f5ff521494793ac31bd3e24cf12eab231bcfe694`, run `40492726919`,
failed Editor compilation with C2668 at `SetBase(nullptr)`. UE 5.8 provides
both `UPrimitiveComponent*` and `FMovementBaseInterfaceData*` overloads.
The call now uses an explicit `UPrimitiveComponent*` null pointer. Artifact
`12729545899` retains the actual compiler error. No native gameplay test ran
for that failed revision; the relocation hypothesis is still unverified.

**Keep this E39.** The same Black Snow source, body, interior and four wheels
are retained. v2 derives a driver leaf from that model; it does not substitute
a different car. v1 and its successful driving evidence remain preserved.

Complete and verify the E39 before extending to the other requested vehicles.
Each later model needs a detailed licensed source, native import, appropriate
physics for its category, interior/crew/interactions and actual game acceptance.
Reuse compatible components; catalogue names alone do not count as delivery.

## Historical driver-leaf-only acceptance — 2026-10-26

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
`UAnomaliaZPrigimaliaVehiclePanelComponent` supplies server-owned angular motion, moving
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

The E39 is not yet a completed playable catalogue vehicle. Its four doors,
bonnet and boot now pass isolated native interaction/collision acceptance.
Engine-bay/boot finishing, exact seat positioning, entry/exit animations and a
visible animated human driver remain unfinished. Entry currently uses the
existing crew possession path; the complete animation/access sequence is not accepted.

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
