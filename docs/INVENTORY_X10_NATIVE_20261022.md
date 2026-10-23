# Inventory x10 implementation checkpoint — 22 October 2026

The latest user design replaces the earlier capacity table. `AnomaliaStorageCatalog`
contains the exact requested totals, including the 30,000-cell carrier and the
eleven dinosaur size/domain presets. Grid area, not both dimensions, is scaled.
Weight limits are unchanged and configured independently.

`AnomaliaVehicleCatalog` resolves explicit model capacities and scales other
original references once. Repeated lookups do not rescale saved values. Existing
equipment cargo suggestions now resolve the same presets. No vehicle is removed.
Unspecified storage variants have design defaults, not user-supplied exact values.

Existing compartments are never automatically reduced to a smaller default.
The preceding layout migration preserves stack IDs and quantities, backs up the
original player profile, and puts unplaceable legacy items in withdrawal-only
recovery storage. A test compilation issue (`TSharedRef::ToSharedRef`) is fixed.

## Verification in this batch

The native `Anomalia.Native.StorageGrids` suite checks exact requested areas,
far-edge placement and persistence for all explicit presets, overlap and rotation,
vehicle capacity lookup stability, and preservation of larger existing storage.
It also fills 512 distinct stacks inside actual 30,000-cell cargo, tests rejection
without mutation beyond that limit, saves/reloads all units, and records elapsed
time. `InventoryLayoutMigration` tests original backups, overflow recovery,
continued consumption and reload without duplicated or lost quantities.

Source tests pass locally. Native compilation, automation and packaged Windows
checks must be read from the workflow for this commit before claiming this batch
is installed or verified in Unreal. The previously validated Windows version is
retained until the package and installed-game checks succeed.

## Outstanding integration

These presets configure real inventory components but do not yet provide complete
player-to-vehicle/tent/dinosaur transfer UI or persistent world-container actors.
Equipment slots are not yet fully connected to worn storage and visible meshes.
Drag/drop, world-container permissions, multiplayer transfer journaling and the
complete DayZ-style UMG layout remain outstanding.

The existing UMG panel now pages stored contents at 32 rows per page, keeping
the held item visible independently. Previous/Next buttons, PageUp/PageDown and
controller shoulder buttons navigate pages without changing inventory contents.
Rectangular objects show their occupied dimensions and a 90-degree rotation
button using the existing authoritative move request, so collisions still reject
invalid placements. The real PIE interaction test exercises rotation and both
page buttons against an isolated 41-stack inventory, then reconnects the original
player inventory and checks the existing close controls.

The current persistence and replication model supports **512 stacks per inventory**.
Cell capacity does not remove that separate bound. Add and split now enforce the
same bound as reload, preventing creation of contents that cannot be restored.
Full use of 5,000–30,000 individual one-cell stacks needs paged storage/persistence
and UI virtualization; it is not completed by increasing the grid dimensions.
The single-grid bounds remain 100,000 cells to keep earlier large saves readable.

314 distinct catalogue IDs and 98 use rules are preserved. This batch does not
claim bespoke meshes, animations or gameplay actions for every catalogue entry.
