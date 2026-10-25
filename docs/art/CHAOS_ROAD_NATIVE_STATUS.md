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
results. Editor and Game compilation passed on Windows with UE 5.8.3 in run
40195507582. The physical driving gate failed; this vehicle is not approved for
production. Compilation does not establish drivable behaviour.

The next correction disables non-root skeletal bodies, including axle and damper
branches outside the wheel subtrees. Only the chassis remains physically active;
Chaos supplies suspension and wheel contact forces. This correction must pass the
same unmodified acceleration, steering, braking, reverse and safe-exit gate.

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
