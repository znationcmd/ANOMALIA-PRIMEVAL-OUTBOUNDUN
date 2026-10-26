# Native Chaos road vehicle

The new `AAnomaliaChaosRoadVehicle` uses an actual skeletal chassis, Physics Asset,
four Chaos wheels, torque curve, automatic forward/reverse transmission, service brakes
and speed-dependent steering. It reuses ANOMALIA's existing authoritative input, fuel,
character possession and safe exit. The legacy floating road movement is disabled only
for this subclass. Existing road, rail, flight and naval prototypes remain unchanged.

The native road vehicle refuses player entry without a real valid rig, four distinct
wheel bones, Vehicle Animation Instance and active physics state. It does not substitute
primitive art when a model is missing. Wheel animation is explicitly bound to its Chaos
movement component because this class retains the existing ANOMALIA pawn hierarchy.

Validation uses an isolated review map and a unique `chaos-smoke-` save scope. The
installed Epic vehicle template is copied locally without overwriting different existing
artist assets. Engine assets and private engine source are never added to this repository
or uploaded as workflow evidence. The plain test surface is an engineering fixture,
not production map scenery.

The actual game process must prove acceleration, physical translation, rotating wheels
in contact with the ground, heading change under steering, braking, reverse and safe
restoration of the original survivor. JSON records measured samples, not simulated test
results. Early runs compiled but failed driving. Subsequent physical acceptance
is recorded below. Compilation alone does not establish drivable behaviour.

## Real driving acceptance — 26 October 2026

Run 40302457850, commit d62969a67215fad3358953e5a21f77c3e410a8c3:
Editor and Game compiled with UE 5.8.3. The actual Unreal game process passed
all seven checks: real skeletal/four-wheel Chaos configuration, preservation of
the survivor/inventory on entry, physical acceleration with rotating contact
wheels, steering, service-brake stop, reverse and safe exit restoring the same
survivor. The full report and genuine viewport screenshots are retained in the
`native-demo-physics-evidence` artifact, ID 12641187281.

The correction combines a dedicated per-instance chassis Physics Asset, bounded
physics substeps, spherical tire sweeps and ABS. Shared vendor assets remain
unchanged. Continuous recording is opt-in because its GPU readback/PNG overhead
significantly slowed the previous test. Phase screenshots remain enabled.

This verifies a single isolated flat proving ground with the Epic reference
vehicle, not the final original sedan, production roads, multiplayer, animations,
vehicle damage/persistence, photorealistic scene, or packaged game. The overall
workflow failed later during the sedan import: PowerShell did not wait for the
GUI Editor process before reading its report. A blocking Python subprocess driver
now waits for actual process completion and validates the source identity/report.
That import correction subsequently passed in Unreal, in run 40303679561.

## Original sedan and corrected wheel orientation

Run 40304980199 passed the same real driving checks with the source-verified
original CC0 sedan body and four individual wheel meshes. The original static
art is assembled on the locally installed licensed skeletal Chaos rig. It is
not an original fully rigged sedan asset with opening door panels.

Run 40308148891, commit 8811670afa0ea1703a677a02fe4307974c5d928b,
compiled Editor and Game with UE 5.8.3 and passed both reference and original
sedan driving. Visual wheel transforms now use measured tire axle orientation,
authored hub positions and actual Chaos suspension, steer and rotation values.
They do not inherit an arbitrary skeletal bind rotation. The continuous native
guard checks each visible axle against the vehicle's steered lateral direction.
The genuine viewport captures are retained with each driving artifact.

The next native validation extends these existing physical checks with refusal
to exit at speed, actual fuel depletion, full accelerator input with an empty
tank, invalid refuel rejection, and resumed physical acceleration after server
refueling. These additional cases are pending until the new Windows run passes.
Only the isolated review fixture adjusts fuel; no existing installation or save
is changed. Refueling here exercises the trusted server API; it does not claim
an inventory-backed fuel-can interaction or a complete ignition/starter system.

## Account-free original sedan preparation

`docs/art/native-demo-sedan-source.json` pins an original Innerscene CC0 sedan by
URL, exact size and SHA-256. `scripts/ue5/prepare-native-demo-sedan.py` verifies the
source without an account. After installing the already pinned Node dependencies,
`node scripts/vehicle-assets/prepare-native-demo-sedan.mjs` derives a body and four
centred wheel assemblies in a separate generated namespace. The source is retained.
Repeated preparation reproduced all five derivative hashes locally.

The source includes static seats, dashboard and steering wheel, but has no skeleton,
animations or separated opening door panels. Preparation is not Unreal import,
rigging, driving or a final DayZ-style vehicle. The generated manifest records these
limits explicitly. No Sketchfab, Google or Epic sign-in is needed for this source.

Not yet approved: production fleet replacement, packaged Windows installation, network
prediction, multiplayer, manual clutch/gears, entry/exit animations, moving portières,
mechanical repairs or vehicle persistence. No claim of full DayZ parity is made.

Snow, desert storms, foliage wind/audio, buildings and non-road vehicle physics are
separate work; this change does not label them complete.
