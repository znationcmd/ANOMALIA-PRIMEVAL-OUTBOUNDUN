# Issue 68 — original container key and lock pack
Source: https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/issues/68

The exact user-supplied Drive archive was retrieved and verified: 109379 bytes, SHA256 d5ff88601c149ceddbda1495da7c139468de297611ccde256a0f5659e428350b. Original ZIP retained verbatim in SourceAssets/ContainerSecurity68/Original.zip. Its README describes original geometry, not extracted DayZ assets.

Verified locally: twelve valid GLB models, six keys and six locks, also supplied as OBJ. Every GLB contains twelve static pieces. Keys encode their colors as uniform per-part vertex colors; locks have explicit PBR materials. The preparer combines the static primitives into one mesh per model without changing binary geometry and converts key colors into explicit uniquely named materials. Transformed or animated sources are rejected instead of silently flattened.

Validation: two local unit tests passed. These cover all twelve geometry buffers, index and attribute preservation, per-part color/material equality, cross-model material-name uniqueness, and rejection of transformed sources. Python syntax and workflow YAML checked.

The supplied attachment script is visual placement only; it does not implement inventory access or a functioning lock. It is deliberately not executed against arbitrary containers.

The queued Windows job preserves the running all-category extraction, retains the original pack in the real D project, imports only into a dedicated asset namespace without replacing assets or saving maps, records dimensions/material slots/checksums, and verifies saved packages in a second editor process. Existing container asset candidates and native runtime classes are inventoried alongside receipts.

Not yet accepted: Windows import results, actual moving-door attachment, six inventory IDs and quickslots binding, server key validation, door animation/persistence, PIE, multiplayer and packaging. No map, door or lock interaction is claimed complete by this change. The Windows workflow reports runtimeIntegrationAccepted=false even after successful mesh import.
