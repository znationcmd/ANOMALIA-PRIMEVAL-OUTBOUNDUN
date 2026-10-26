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

Run 40310935421 extends these existing physical checks with refusal
to exit at speed, actual fuel depletion, full accelerator input with an empty
tank, invalid refuel rejection, and resumed physical acceleration after server
refueling. All twelve checks passed on both reference and original sedan under
UE 5.8.3, commit 862e7167e075a3121fe328b005affcbf15fad665.
Only the isolated review fixture adjusts fuel; no existing installation or save
is changed. Refueling here exercises the trusted server API; it does not claim
an inventory-backed fuel-can interaction or a complete mechanical starter system.

## Explicit road engine ignition

The Chaos road pawn now starts with its engine off. The possessed driver's R
action (gamepad top face button) sends a reliable server request; the server
validates the current player controller, possession, road rig and available fuel.
Engine state is replicated and exposes a Blueprint event for later sound/UI art.
An off engine supplies no throttle and consumes no driving fuel. Fuel exhaustion
stalls it; refueling alone cannot restart it. Driverless road vehicles shut down.
This change leaves the other vehicle simulation types' existing power rules intact.

The extended native probe must prove accelerator input with ignition off, driver
start, actual depletion/stall, refusal to restart empty, refueling without automatic
restart, explicit driver restart and acceleration, and explicit shutdown. The new
ignition code compiled in Editor and Game with UE 5.8.3 and passed actual game
execution in run 40311556355, commit 68dcaeb5391d1efb83a74437b76d25f8cde24d3e.
All sixteen checks passed with both reference and original sedan. All measured
visible tire axles remained aligned (152 reference samples, 150 sedan samples).
The driver APIs are exercised in game; a manual keyboard/gamepad session and
multiplayer session have not been verified. This is a functional power/input
gate, not finished starter animation/audio, battery or engine damage.

Evidence retained in that successful run:
- `native-interaction-proof`, artifact 12645436324: native compilation/automation.
- `native-demo-physics-evidence`, artifact 12644688689: reference driving report
  and genuine Unreal viewport captures.
- `native-sedan-drive-evidence`, artifact 12645695973: original sedan driving
  report and genuine Unreal viewport captures.

154 local Python tests passed as supplementary source/tool checks. The new engine
and fuel work has not been packaged or installed. It does not complete production
roads, doors/entry animations, fuel-can inventory transactions, network gameplay,
mechanical damage or persistent vehicle saves.

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
prediction, multiplayer, manual clutch, entry/exit animations, moving portières,
mechanical repairs or vehicle persistence. No claim of full DayZ parity is made.

Snow, desert storms, foliage wind/audio, buildings and non-road vehicle physics are
separate work; this change does not label them complete.

## Driver controls and unrestricted moving exit (native validation passed)

The road pawn now allows exit at any speed, per the current requested gameplay.
The existing floor, capsule-clearance and obstacle checks still choose the exit
position. The existing survivor receives the chassis' actual linear velocity;
the unattended car coasts instead of receiving an immediate full brake at speed.
Earlier reports of refusing a moving exit describe the previous version only.

Commands, validated against the current driver and replicated by the server:
- Page Up / Page Down: select real Chaos gears; M: automatic/manual mode.
  Manual W/Z accelerates in the selected gear; S brakes. Selection includes
  neutral and reverse, within the actual configured gear count. No clutch yet.
- Space: hold the rear-wheel handbrake (release to disengage).
- L: real front spot lights. Comma/Period: left/right signals; H: hazards.
  Four actual amber light components blink against server time. Dedicated lens
  emissive materials and night-time visual acceptance remain incomplete.

The native probe requires actual first/second gear driving, a stop using the
handbrake without service brake, real light activation/blinking, then an exit
above 2200 cm/s (79.2 km/h), restoring the same survivor with inherited movement.
There is no gameplay speed limit on exit; the threshold is a proving-ground test.
Editor and Game compiled with UE 5.8.3. Run 40315639102 passed all 21 actual game
checks on both reference and original sedan, source commit
`a4aba5fa312c972e15b0f29755b9d3ea441e580a`. The initial test exceeded the old
500 m proving surface; the owned engineering surface is now 1000 m wide. No
production terrain is changed. The test retains physical wheel-contact and
free-exit checks. The character movement update records inherited speed before
later ground friction slows it, without injecting character movement in the probe.

Measured exit speeds: reference 3154.34 cm/s (113.56 km/h), character 3163.45 cm/s;
original sedan 3825.01 cm/s (137.70 km/h), character 3833.59 cm/s. There is no
runtime speed cap. Reports and real viewport captures are retained in that run:
reference artifact 12646652894, sedan artifact 12646703734, native build/tests
artifact 12646917478. Local source/tool tests: 154 passed.

These results cover standalone proving-ground driving and driver APIs. They do
not verify a manual keyboard/gamepad session, night-time optics, network play,
animations, impact injury, production-road driving or a new packaged installation.

Additional requested work, not declared implemented: animated wipers (source
does contain separate arms/blades), replaceable wheels/doors/hood/trunk with item
transactions and persistence, dirt/washing materials, collision deformation,
panel/glass/tire damage and appropriate sounds/animations. Door, hood and trunk
seams in the current source are not separated opening body panels. These require
actual mesh work and runtime validation, not only configuration flags.

## Measured road-simulation calibration (pending native validation)

The initial validation tune used 500 Nm, AWD and a 2x tire friction multiplier.
The new unbranded road-sedan target uses 1500 kg, 320 Nm and rear-wheel drive,
with actual front engine torque disabled and rear torque enabled. Tire friction
multiplier is 1.0. Service brake torque is 1800 Nm front / 1000 Nm rear, handbrake
2200 Nm rear. Springs are 45000 N/m with 12 cm raise / 10 cm drop, damping 0.6.
Drag coefficient 0.30 and chassis section 182 x 145 cm feed actual aerodynamic
drag; no downforce is added for road-sedan grip. These are original tuning targets,
not certified measurements or manufacturer specifications for a named real car.

An explicit standalone probe, only in owned proving maps and isolated save scopes,
assigns per-component transient physical materials with friction 0.9 / 0.45. Shared
engine assets, production terrain and existing installations remain untouched.
The test requires observed rear-only engine torque, actual stops from 50 and
80 km/h on the higher-grip surface, then an 80 km/h stop on lower grip. It measures
actual chassis path/time and equivalent mean deceleration, not a programmed stop.
Lower grip must lengthen stopping distance by at least 30%; the faster dry stop
must exceed the slower dry stop by at least 50%. Broad road-sedan acceptance range
is 0.25–1.2g mean deceleration. These checks detect implausible results; they do not
certify a complete professional tire model or reproduce every real-world condition.

Samples add longitudinal/lateral acceleration, actual contact friction, slip/skid
and spring loads. Acceleration-to-target times are reported alongside each stop.
The longer sequence needs a 2 km wide engineering surface and a larger total
watchdog; individual driving/braking deadlines and the unrestricted-speed exit
rule remain. Fuel consumption is restored after the isolated depletion test.

This revision is not yet compiled/tested in Unreal. Previous 21-check results do
not validate the new calibration. Wet-weather visuals, loose terrain, bumps,
different loads/tires, high-speed cornering, steering-wheel feel and multiplayer
still require dedicated driving validation.
