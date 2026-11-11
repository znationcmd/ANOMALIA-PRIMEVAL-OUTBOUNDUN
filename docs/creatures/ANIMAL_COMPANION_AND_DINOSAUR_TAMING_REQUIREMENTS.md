# ANOMALIA’Z PRIGIMALIA — Animal companions, wildlife and dinosaur taming

## Product requirement

ANOMALIA must support an ARK-inspired creature gameplay loop while remaining an original implementation. This document is a gameplay requirement, not a claim that the feature is already operational in UE5.

## Creature categories

- **Companions:** eligible animals can be recruited and assigned to a survivor. Initial requested choices include German Shepherd/dog, monkey, lion and wolf, subject to verified assets, animation compatibility and balancing.
- **Multiple companions:** the player can own and travel with more than one companion at the same time; dog + monkey together is an explicit acceptance case. The system must not be hard-coded to one companion slot.
- **Wildlife:** animals also populate appropriate biomes as independent wild actors. A species being companion-capable does not make every wild individual friendly.
- **Dinosaurs:** catalogued dinosaur species and variants can appear as wild creatures and can be tamed, subject to species-specific gameplay and asset readiness.

## Dinosaur taming loop

Support species-configurable taming methods:
1. **Knockout taming:** subdue a creature, manage torpor/unconsciousness, protect it and feed its preferred food or kibble.
2. **Passive taming:** approach carefully and offer the correct food without attacking, for species designed for this method.
3. **Special taming:** bespoke objectives or items for exceptional species and bosses, only where explicitly balanced and enabled.

Expose taming progress, effectiveness, preferred food, hunger, torpor, time remaining and interruption/failure conditions. Food and kibble tiers must map to actual recipes and creature profiles; catalog labels alone are not functional recipes.

## Post-tame gameplay

- Ownership and tribe/server permissions; follow, stay, defend and species-appropriate commands.
- Mounting only for species with verified saddle fit, rider sockets, locomotion, collision and network-safe movement.
- Species-specific abilities, stamina, health, food, inventory/carry limits and progression.
- Breeding, eggs or gestation, baby care, maturation, inherited stats/colours and mutations only after persistence and multiplayer validation.
- Save/load ownership, tame state, inventory, saddle, breeding lineage and growth across server restart/reconnect.

## Technical acceptance criteria

- Server-authoritative taming, ownership, commands, damage and creature state; clients cannot grant taming or alter stats.
- Species data drives mesh, skeleton, animation, AI, habitat, food preferences, tame method, saddle and loot profile.
- Wild AI includes habitat-appropriate idle/roam, flee, hunt/attack, perception and navigation.
- Wildlife and tames use separate behavior/permission states; taming must not silently convert every same-species wild creature.
- Per-map and per-server spawn/taming/breeding overrides; preserve existing catalogs and saves.
- Automated tests cover taming success/failure, food matching, interruption, ownership permissions, multi-companion party (dog + monkey), save/load, replication and server restart.
- UE5 editor/PIE and packaged build validation must confirm real meshes and compatible animations. A catalog entry or asset filename is not proof of a playable creature.

## Existing configuration status

The existing `public/config/dino_species_catalog.json`, `dino_taming_breeding_mounts.json` and `dino_kibbles_catalog.json` are retained. They describe requested species, taming methods, kibble and breeding/mounting settings, but are **configuration only** until connected to Unreal gameplay and validated. Existing hybrid/variant catalogs remain intact. Do not enable a creature with missing or unverified mesh, animation, AI or balancing.

## Asset and licensing safeguards

Use assets already present in the project only after auditing their actual location, skeleton, animations and license. Do not download or redistribute third-party ARK mod assets or reuse proprietary ARK models. Missing creatures require original or properly licensed assets.
