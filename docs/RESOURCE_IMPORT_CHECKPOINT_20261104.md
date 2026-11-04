# Actual-project resource checkpoint — 4 November 2026

Actual project: D:\ANOMALIA\unreal\AnomaliaPrimeval.uproject (resolves to D:\ANOMALIAZ\01_Projet_Principal\unreal).

## Native resource integration
Run 41846216338 stopped at its 82-minute step limit; it did not finish the complete source manifest.
Receipt artifact 13338703853:
- 113710 package additions recorded; 2359 identical existing entries.
- 5 conflicting existing assets preserved; 398 existing or unowned world-external entries preserved.
- 45734171543 bytes reused through hard links; 219587 privately copied bytes.
- All 127 original map hashes unchanged; zero existing assets overwritten; zero source files written.
Counts describe package operations, not playable vehicles, unique buildings or completed maps.

## Actual D editor registry check
Run 41848085150 succeeded; artifact 13341715561:
- 138252 registered assets.
- 1498 AnimSequence assets, 70 AnimBlueprint assets, 154 Skeleton assets.
- 1970 animation-related assets overall.
- 585 vehicle-name/class candidates; these are not 585 verified vehicles.
- No missing registered skeleton reference in the examined animation tags.
- Zero packages saved; zero gameplay objects loaded. Retargeting, animation playback, vehicle driving and full dependencies have not been accepted by this registry check.

## Continuing work
Raw conversion run 41851208057: source preparation succeeded; actual D editor import running at this checkpoint.
Standalone project discovery run 41855377953: waiting for raw import, then searches attached C:/D: roots for standalone Unreal projects and both Sketchfab directories. Second circuit and motocross terrain remain unconfirmed.
Receipt-aware integration resume implemented in commit 6e7d00af5e9bedf21a584a19fcc1687d34cf2b1f; syntax checked. Workflow commit 13a423fff77f553b3a0f7bce38bf5802a415f002 waits for raw import and both read-only discovery jobs before reusing the prior receipt. No overlapping Unreal/content writer is intentionally started.

## Acceptance limits
No new full-map gameplay, animal AI, complete character retargeting, circuit driving or vehicle simulation acceptance is claimed.
Original files retained. Resources linked into the main project must be detached to private copies before any future edits that would otherwise modify a source hard link.
