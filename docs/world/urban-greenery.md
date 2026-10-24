# Urban planting v1

Adds the already imported Poly Haven CC0 `island_tree_02` and `grass_medium_01` to clear parcels in `/Game/Maps/ANOMALIA_Inhabited_v2`. It does not alter terrain, buildings, streets or existing forest clusters. This is decorative planting; no new blocking tree collision or gameplay performance certification is claimed.

The planner uses copied saved actor bounds, full yaw-independent crown radii, a one-metre structure margin and the existing 8.5m-wide street corridors. Ground envelopes reject flooded, steep or high parcels. Selection is deterministic for reviewable updates and idempotent validation.

The authoring runner verifies a pre-change world archive, checks the prepared model file hashes and imported asset provenance, creates tagged native HISM clusters, saves only this world's packages, then verifies every saved instance in a fresh Unreal process. Unexpected actors, modified materials and existing partial planting are preserved and stop the run. Ownership and plan hashes are retained in `Saved/UrbanGreenery`.

The map-progress workflow gates the installed Editor update on native compilation/tests, the existing house audit, independent planting verification, real GPU reopening, and validation of the copied project. Graphics captures include a street-height view. This does not mark the full map complete, connect towns, finish building interiors, or package the full map into the playable game.

Source references and attribution are recorded in `docs/art/realism-validation-sources.json`; no third-party game resources are copied.
