# Items — native integration, 22 October 2026

The source catalogue now exposes 262 distinct inventory definitions: the existing catalogue and RP additions, plus three empty drink containers. Existing rows remain present; the two category references to `car_battery` resolve to one inventory definition.

## Implemented in native code

- 21 catalogue consumables (13 foods, seven drinks and a simple sterile-bandage health effect) have server-defined use rules and real inventory buttons. Eight older survival IDs retain compatible use rules.
- Using an item checks the current selected stack count, recovery locks, living/awake state, capacity for returned containers and whether a stat can improve. The server chooses the effects and profile identity.
- A single player-profile write records both the consumed inventory and resulting survival values before either is published in memory. Unrelated profile fields are preserved. Failed writes or unavailable container space preserve the source item.
- The three refillable drinks return their own empty container definitions. Refilling them is still a separate, unfinished interaction.
- Held items can return to the first available compartment slot, including rotated placement. The interface offers **Ranger** for held stacks. If storage is full, the item remains held. This is inventory placement; it does not add a character-held 3D model or weapon functionality.

## Verification

- 93 Python UE5 checks passed locally. Source checks also passed on GitHub.
- Initial native Editor and Game compilation succeeded under Unreal Engine 5.8.3 for `f9b8419`.
- The initial native suite stopped on five assertions in the full-storage consumption fixture: its attempt to shrink default pockets was correctly refused by the production inventory. The fixture now creates an isolated empty one-cell compartment instead of attempting that shrink. Production storage protections remain unchanged.
- The updated native catalogue test checks inventory entry, movement to hands, return to storage and removal for every catalogue ID. Consumption tests cover every one of the 21 configured use rules, persisted effects, stale requests, recovery locks and returned-container capacity. Added storage cases cover full pockets, recovery locks and repeated requests.
- The corrected native compilation/test step and the actual Play In Editor interaction/inventory step passed for commit `76a9c62dad5cc7eb4fa07f6d5323b5e7c3edfc38`, workflow run `39821306529`.
- The packaged gameplay probe now collects food and a second supply from the actual world, invokes the real inventory food-use button, checks the consumed count and restored hunger, then saves and restarts the executable using isolated test data.

The packaged game, explicit profile save, second-process restoration and automatic installation all passed for the same commit. The installed executable repeated the real food-button/count/hunger check successfully. The installer verified the active version and Desktop shortcut and preserved all 11 existing user-data files with isolated validation saves.

Installed executable:

```text
C:\Users\utilisateur\AppData\Local\CMD\ANOMALIA-Windows\versions\76a9c62dad5cc7eb4fa07f6d5323b5e7c3edfc38-5ab5be32\AnomaliaZPrigimalia.exe
```

Desktop launcher: **ANOMALIA - Jouer**. This push updated the existing `e5e5a331` installation automatically. Evidence: [workflow run 39821306529](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/39821306529), artifact `packaged-playable-install-diagnostics` (`12445231682`). That artifact contains the package, restart and installed-copy reports; `ANOMALIA-Windows-Test` (`12445710889`) contains the test build. Native tests verify every configured consumable and every catalogue item's inventory round trip; the packaged UI probe verifies an actual collected food's use, rather than claiming every item's UI or specialized behavior was tested.

## Remaining item work

Catalogue presence is not finished gameplay. Many pickups retain generic labelled geometry. Individual original 3D models, equipping clothes and weapons, firing/reloading, tool actions, crafting, construction placement, advanced medical interactions, refilling, dropping items into a persistent world and related multiplayer tests remain to be completed. No console/mobile item validation is claimed.
