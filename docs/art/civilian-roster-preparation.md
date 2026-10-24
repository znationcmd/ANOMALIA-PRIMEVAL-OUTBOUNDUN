# Civilian roster source preparation

Requested roster: seven men, seven women, seven boys and seven girls. Contemporary
human appearance; no anime or futuristic costumes. The player must eventually be
visible in third person, choose a survivor, retain that choice in saves, and see
equipped loot clothing on the same character.

## Source and licensing

The preparation uses Blender 4.5.9 LTS and MPFB 2.0.18, source revision
`b1a2dc98776da9d1eea751b159d42cf61778fe2e`. MPFB's code license is separate
from its CC0 model assets. No generator source code is linked into the game.

- Core model/targets: https://github.com/makehumancommunity/mpfb2
- Core asset pack: https://static.makehumancommunity.org/assets/assetpacks/index.html
- Closed-source game permission: https://static.makehumancommunity.org/mpfb/faq/use_in_closed_source.html
- Asset pack SHA256: `b542127a8e25547c7c29c19f2d1d2adb9a664c80396ecd694095dbc8028a0107`
- Blender archive SHA256: `dcdc3eca6c9825bb35a8033b689c053f3cb5a9b0cd2a61b2eac2a49436b4ad3d`

Only the reviewed CC0 core pack is accepted. Pack metadata licenses are checked
before extracting. Each exported preset records its macro settings, source
garment checksums, output checksums, dimensions and skeleton count. Child
presets use the generator's child-to-young age targets, not scaled adult meshes.
All saved scenes and previews include a shirt, full-length trousers and shoes.

## Reproduction

Install the pinned MPFB extension in Blender's `user_default` extension repository.
Run `scripts/characters/build-civilian-roster.py` in background Blender with
`--asset-pack <reviewed-zip> --output <new-directory>` after Blender's `--`.
Default output is exactly 28 characters. `--limit 1` supports an initial art check.
Run `scripts/characters/verify-civilian-export.py --root <output-directory>`
in background Blender to round-trip all 28 GLBs and one FBX per group, check
textures, dimensions, bones and actual skin deformation.

## Explicit integration boundaries

These are source preparation assets, not production-approved photorealistic
characters. Realistic human proportions alone do not meet the final art target.
FBX and GLB contain separate skinned body, clothing, footwear and face/hair
objects. The supplied casual suit is currently one garment mesh; independent
top/trouser swapping needs authored modular seams and an underlying clothed
fallback. Do not claim DayZ-style per-slot clothing is already implemented.

The exports currently contain no gameplay animation clips. Retargeting, LODs,
collision/capsule sizing for children, native mesh assignment, selector UI,
save persistence, equipped-loot binding and native GPU gameplay verification
remain required. Do not silently replace the invisible native survivor with a
static statue or release a T-pose model as completed gameplay.

The preparation does not change the existing installed game's player mesh or
saved player data. Its validation report records `unrealTested: false`.
