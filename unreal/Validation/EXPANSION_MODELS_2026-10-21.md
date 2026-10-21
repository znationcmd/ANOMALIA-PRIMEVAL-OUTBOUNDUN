# Original prototype expansion — 21 October 2026

This increment generates 33 original GLB meshes with the Python standard library:
26 generic vehicle families from the existing native catalogue, one static semi-trailer,
and six building types. It preserves all existing models and all 210 grouped exact-model
requests. These are original geometry prototypes, not finished realistic vehicles or
manufacturer replicas. No exact BMW, military chassis, DayZ model or other requested
manufacturer model is declared implemented by this change.

## Implemented

- Trucks, tractor, buggy, motorcycles, kart, Formula-style racer, car/SUV/van,
  emergency variants, armored van and monster truck.
- Generic boat, carrier, warship, submarine, locomotive, light airplane, fighter-style
  airplane, attack-style and transport-style helicopters.
- Static semi-trailer (no coupling physics).
- Four-floor residence, townhouse, hospital, police/fire stations and farm barn.
- Original mesh geometry includes tyres, alloy wheel details, seats, steering controls,
  transparent cabin panes, chassis, emergency light bars, railings and building stairs.
- Versioned import destinations, source SHA metadata, preserved unrelated art,
  dimensions checked after native import, catalogue binding probes for all 26 vehicles.
- Separate `/Game/Maps/ANOMALIA_ExpansionReview_v1` review scene, preserving the
  archipelago and player/server saves. Not yet placed in the production world.
- Native DX11 screenshot job for each of the 33 models and checksum validation.

## Local verification

Three tests passed: full generic native catalogue coverage; all 33 generated GLB headers,
buffer lengths, finite vertex data, unit normals, valid triangle indices, bounds and SHA;
deterministic regeneration and preservation of modified art. Python scripts compile.
A temporary mesh overview was inspected; silhouettes are identifiable but visibly
prototype quality. This is not evidence of Unreal rendering or realistic driving.

## Remaining

Native import, model screenshots, collision and walk-through tests must pass and be
reviewed. Ground driving currently uses the existing prototype movement, not a completed
Chaos vehicle rig. Wheel/rotor/propeller animation, texture/UV detail, damage, usable
passenger seats, trailer articulation, specific manufacturer models, city/village layout
on the real terrain and multiplayer scenarios remain outstanding.

The source generator runs on the trusted Windows Unreal host; generated GLBs and
imported assets are included in its evidence/artifacts and installed project copy only
after successful validation. The files generated here are not 33 completed game features.
