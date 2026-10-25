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
results. Native compilation and physics driving are still pending validation at this commit.

Not yet approved: production fleet replacement, packaged Windows installation, network
prediction, multiplayer, manual clutch/gears, entry/exit animations, moving portières,
mechanical repairs or vehicle persistence. No claim of full DayZ parity is made.

Snow, desert storms, foliage wind/audio, buildings and non-road vehicle physics are
separate work; this change does not label them complete.
