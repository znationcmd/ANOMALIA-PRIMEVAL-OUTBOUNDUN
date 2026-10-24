# Creature Vault: native implementation audit, 24 October 2026

Runtime module: `AnomaliaPrimeval`. Last verified host engine: Unreal 5.8.3.
Scope of this change: durable **legacy terminal metadata**, not the requested
complete dinosaur gameplay. No ARK, SCS or DayZ assets/code are incorporated.

## Existing systems examined

* `AnomaliaCryoSubsystem`: terminal permissions, capture/release metadata and
  in-memory uniqueness. It has no creature actor binding, complete creature
  snapshot, physical terminal, capture tool or inventory container.
* `AnomaliaInventoryComponent`: real replicated inventory and durable player
  transactions. A stack currently has no globally unique creature payload;
  using a stack number alone would not prevent container duplication.
* `AnomaliaNPCRecruitmentSubsystem`: human NPC training/deployment state. This
  is not a dinosaur controller or a substitute for an animated creature.
* Human family data is not dinosaur breeding. It is preserved separately.
* `dino_taming_breeding_mounts.json` explicitly labels its configuration
  `CONFIGURATION_ONLY_NOT_CONNECTED_TO_UNREAL`.
* Branch and open-PR audit found no existing native dinosaur Pawn or rider
  system. No native dinosaur actor class was found in the examined source.
  An exhaustive asset-registry audit on the PC remains necessary before
  declaring that no suitable skeletal assets are installed there.

## Implemented in this slice

The existing subsystem now restores and writes server-scoped versioned JSON at
`Saved/Servers/<server-id>/World/creature-vault-metadata.json`, using the existing
temporary-file replacement path. All metadata mutations are server-only and
return success only after writing. Failed writes roll back memory and do not
populate a release result. Reload reconstructs the cross-terminal uniqueness
index. Invalid saves, unsupported versions and duplicate IDs fail closed without
replacement. A failed load cannot silently redirect a subsequent mutation to
the default server's save.

The file explicitly declares `recordKind: terminal-metadata-only`. Legacy
`ReleaseCreature` still relies on trusted server callers to complete spawning;
its boolean parameter does **not** establish an atomic world/storage handoff.
No client RPC accepts a user-supplied actor ID or administrator role here.

Native regression coverage is added for reload, configuration persistence,
duplicate rejection, durable release, failed writes and rollback, future-version
preservation, and duplicate terminal data. Native compile/test results must be
checked in `UE5 Creature Vault native validation` before merging this branch.
That workflow does not install or claim a playable Creature Vault.

## Still required for the requested gameplay

1. Licensed, verified skeletal species assets, animation blueprints, collision
   and authoritative species profiles with supported locomotion/capabilities.
2. Live creature actors, taming, AI/perception/navigation, attacks and damage.
3. Seat sockets, mount/dismount montages, possession/permissions, safe exits,
   replication and disconnect/death recovery.
4. Complete versioned creature snapshots: statistics, appearance, ownership,
   inventory/equipment, effects, genealogy and growth.
5. A durable operation ledger for capture/release, unique inventory containers
   and crash recovery across the world/storage boundary; metadata uniqueness
   alone does not prove actor/container duplication is impossible.
6. Physical terminal, device, original UI, permissions, server settings and
   breeding/egg/baby/resource rules with bounded offline progression.
7. Real two-client dedicated-server tests, restart/failure recovery and licensed
   asset review. None of these are claimed complete by this change.

## DayZ / Unreal reference review

The user-supplied vehicle and door documentation was examined alongside the
official `DayZ-Samples/Test_Building` configuration/model configuration and
`Test_SmartCar` configuration/script. The building sample couples two opposing
hinges to one double-door action and keeps damage/sound/action points distinct.
The SmartCar sample demonstrates input/engine/gearing coordination, not a
portable Unreal implementation. ADPL-SA restricts those samples to Arma/DayZ;
no sample files are copied into ANOMALIA.

Epic's Opening Doors article demonstrates separate moving meshes and authored
pivots. Chaos Vehicles uses skeletal meshes/physics assets; Chaos Modular
Vehicles uses geometry collections and modular simulation with network
resimulation. The present floating road Pawn is not either vehicle simulation.
The existing hinge/crew foundation does not certify fitted building interiors,
entry animations or a complete DayZ-equivalent vehicle.
