# Manny/Quinn modular appearance — preparation (not asset import)

The playable AAnomaliaSurvivor now owns seven optional cosmetic skeletal components: Jacket, Pants, Boots, Gloves, Headgear, Backpack, Vest. Their animation pose follows the existing character mesh; collisions are disabled on cosmetic layers. SetClothingMesh rejects mismatched skeletons. This is a local cosmetic API, **not yet a replicated server-authoritative equipment system**.

## Asset acquisition (manual Epic entitlement)

Epic's official free Mannequins Asset Pack: https://www.fab.com/listings/ad542ee6-34d0-4828-a56c-13846cd649d0 . Acquire through an authorized Epic/Fab account and add to the UE5.8 project with Epic Games Launcher / Fab. Alternatively use the Third Person template's Manny/Quinn assets. Do not commit Epic licensed .uasset files to the public GitHub repository.

## Test plan

1. Assign Manny as the survivor body skeletal mesh and a compatible animation Blueprint (e.g. ABP_Manny) in an ANOMALIA character Blueprint; verify visible locomotion and crouch.
2. Import licensed garments skinned to the same skeleton, set each clothing slot in Blueprint, verify pose following and no extra collisions.
3. Verify removing a garment with null mesh, camera visibility, clipping, dedicated-server replication design, multiplayer appearance and equipment authority.

**Status:** Code committed for validation. No Manny binary downloaded/imported. No real garments bundled. Native UE compile, in-game and network tests still required.
