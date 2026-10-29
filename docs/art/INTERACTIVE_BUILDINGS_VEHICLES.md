# Functional buildings and vehicles: source and implementation audit

References supplied by the user, 24 October 2026:

- https://community.bistudio.com/wiki/DayZ:Vehicle_Configuration
- https://community.bistudio.com/wiki/DayZ:Doors_on_buildings
- Unreal equivalent: https://dev.epicgames.com/documentation/unreal-engine/how-to-set-up-vehicles-in-unreal-engine
- https://dev.epicgames.com/documentation/unreal-engine/vehicle-art-setup-in-unreal-engine

The DayZ guides describe separate animated selections, hinge axes, interaction
points and collision geometry. Crew positions, wheel hubs, mass, suspension,
torque, gear ratios, steering and braking are functional data, not visual detail.
Those concepts apply to ANOMALIA; RV model.cfg/config.cpp files are not Unreal
assets. No DayZ model, protected implementation or game-specific config is copied.

## Confirmed source defects

- Large-world replacement houses are static scanned **exteriors**. Source hashes,
  material bindings and placement checks do not prove accessible interiors. No
  automatic promotion to an enterable building is allowed.
- `AnomaliaZPrigimaliaVehiclePawn` uses a sphere root and `FloatingPawnMovement` for road
  vehicles. Visual overrides cannot supply real wheels, suspension, differentials
  or transmission. Its current behaviour remains a prototype, not Chaos validation.
- Legacy crew interaction used the actor centre with a 450 cm radius; exit blindly
  teleported 350 cm sideways. There were no dedicated door/seat/exit markers.
- There was no native interactive building-door class. The playable house test
  only verified walking through an already open doorway.

## This implementation

- `AnomaliaZPrigimaliaDoorActor`: separate mobile leaf around a hinge, configurable dimensions
  and signed opening angle, server distance and line-of-sight checks, replicated
  lock/angle/obstruction, collision checked along the moving leaf arc. Server-side
  survivor interaction targets the actual visible door. No arbitrary client target.
- Door collider is independent from the visual mesh. **No default cube is rendered.**
  A licensed separate door leaf must be fitted to a genuine opening. Attaching this
  actor to a sealed exterior scan is not an acceptable integration.
- Vehicle entry now rejects walls between the character and entry. Models may opt
  into explicit driver entry, seat and exit components; the parked survivor follows
  the authored seat. Existing models keep their compatibility entry path.
- Vehicle exit checks a walkable floor, full character capsule, the exit path and
  clearance from the vehicle root before restoring the character. An obstructed
  authored exit is refused, preserving possession and inventory.

## Acceptance before a production claim

Building: correct scale, actual rooms and floor, clear doorway, separated leaf,
hinge and handle points, open/closed collision, lighting, navigation through the
open door, server replication and persisted door state. Door sounds, damage and
persistent open/locked state are not implemented by this change.

Road vehicle: licensed model with accessible cabin and separated moving parts,
correct wheel pivots/bones and sockets, convex chassis collision and centre of
mass, Chaos wheel/suspension setup, engine torque and transmission, steering and
braking curves, authored crew points and door animation. Verify wheel contact,
slopes, collisions, passengers, save/reload and network behaviour in the packaged
game. Other vehicle domains need their own appropriate simulation.

**No existing house is declared newly enterable; no new realistic vehicle physics
or fitted door asset is declared complete.** New native tests exercise the door
and crew collision contracts. Compilation and test evidence must be read from
the fresh workflow; source changes alone are not a successful native test.

The metro, railway station and port remain outstanding map work. This interaction
correction does not claim their geometry was authored or installed.
