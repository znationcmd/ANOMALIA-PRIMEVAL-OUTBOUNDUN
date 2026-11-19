# Vehicle repair and colors — 4 November 2026

Requested: repair existing 3D vehicles, make them drivable, supply multiple colors. Existing original resources and maps must be retained.

Prepared actual-project workflow: 41929128580. It targets D:\ANOMALIA\unreal\AnomaliaPrimeval.uproject, not a substitute project. At preparation time the Windows job was queued without an assigned runner; no fleet repair execution result is yet available.

First executable batch:
- Load each vehicle candidate in the actual project; record failed loads, missing materials, skeletal/physics assets and static collision shapes.
- Inspect existing Blueprint road meshes, animation classes and wheel-bone configuration where exposed.
- Create seven separate material-instance variants only for an explicit paint material with a unique color parameter. Preserve source mesh/material packages; do not recolor glass, tyres or lights.
- Verify saved material parameter values. Actual visual checks and in-game material binding remain required.
- Produce a per-package report, errors and modified material paths. No driving success is asserted by this script.

Palette: black, grey, dark grey, forest green, midnight blue, white and red.

Driving work depends on actual rig inspection. Static decorative art is not a drivable vehicle. Existing source includes a genuine ChaosRoadVehicle implementation with steering, suspension, transmission, wheel bones, engine controls and modular panels; its deployment and each vehicle configuration must be validated in the actual D project. The older floating movement prototype is not acceptable as simulation completion.

Known raw import blockers from run 41851208057:
- Scania mesh failed to reload after FBX import.
- A military backpack mesh also failed to reload (independent from this fleet task).
- 1350 source entries deferred, including disk-reserve cases. This is not a count of 1350 vehicles.
- Existing maps were not saved by raw importer.

No vehicle is declared repaired until acceleration, braking, steering, wheel movement, suspension, collisions, entry/exit and colors have been checked in PIE using the actual model. Motorcycles, snowmobiles, trucks and F1 cars require their own suitable geometry and physics configuration.
