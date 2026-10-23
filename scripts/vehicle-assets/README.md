# Credited named vehicle review assets

`npm ci --prefix scripts/vehicle-assets` then `node scripts/vehicle-assets/prepare.mjs` downloads the 36 immutable public mirror GLBs in `docs/vehicles/named-assets-sources.json`. Every byte count and SHA-256 is checked. Original creator and component credits are retained in generated CREDITS.md and the manifest. Meshopt is decoded, transforms baked, one static mesh assembled, PNG textures embedded with a 1024px maximum, and animation excluded from this static review import. No extra mesh simplification is applied.

These are individual artist variants, not all requested body styles or generations. Source names and source units are unverified. Several source scenes include display geometry or implausible bounds; `sourceBoundsNeedReview` flags these. The inferred centimetre/millimetre conversion is not manufacturer scale validation. They remain `reference_vehicle` assets outside the playable catalogue. Do not claim correct scale, orientation, interiors, damage, rigging, collisions or driving until reviewed and tested. Preserve the raw cache and prepare to a new directory when artist output changes.

Native import uses `scripts/ue5/validate-expansion-models.py --group NamedVehicles1` and requires all source hashes, actual imported bounds/materials and fresh GPU screenshots. The review map is separate from the archipelago.
