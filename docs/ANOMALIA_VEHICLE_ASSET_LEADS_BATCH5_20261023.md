# ANOMALIA vehicle asset leads — batch 5 (2026-10-23)

Status: candidate links discovered, **not downloaded/imported/rigged/compiled**. Listings' displayed CC BY licenses must be verified along with creator provenance before using in a distributed game.

| Category | Source | Listing details | Next steps |
|---|---|---|---|
| F-16 Fighting Falcon | https://sketchfab.com/3d-models/f-16-fighting-falcon-f4a4568d8a624026a675090852fb9546 | Download, CC BY listed, ~192.7k triangles, 4K PBR textures, not rigged | Validate provenance, cockpit, separate control surfaces, rig and flight physics |
| F-16 Block 70 | https://sketchfab.com/3d-models/f-16-block-70-pilot-animations-c5415a75ec5645f5b2c469b84f1555c5 | Download, CC BY listed, ~97.6k triangles, pilot and animations advertised | Check animation export, texture and origin |
| F-16 NATO game-ready | https://sketchfab.com/3d-models/f-16-fighting-falcon-nato-gameready-1d74c97a06384d318b1d09e0e3811055 | Download, CC BY listed, ~114.7k triangles, multiple PBR texture sets | Evaluate visual fidelity and game import |
| Modern motorcycle | https://sketchfab.com/3d-models/motorcycle-2a5922ce4283422d83c34d5bab5f65bf | Download, CC BY listed, ~67.7k triangles | Inspect model parts, tire pivots, textures, steering |
| Motorcycle | https://sketchfab.com/3d-models/motorcycle-135b505f55bb4da0b82b8987a34443b2 | Download, CC BY listed, ~52.7k triangles | Check texture quality and provenance |
| Motorcycle | https://sketchfab.com/3d-models/motorcycle-693e83d86e1e4e5b95e4314dbdd95d40 | Download, CC BY listed, ~69.9k triangles | Check PBR maps, wheel rig and quality |
| Motorcycle off-road style | https://sketchfab.com/3d-models/motorcycle-d2491be97414453ea6c1f2e13b6db4a5 | Download, CC BY listed, ~410k triangles | Optimize, check fit to requested motocross category |
| Historic American fire truck | https://sketchfab.com/3d-models/free-1940s-us-fire-truck-american-lafrance-9548e406e29e49e18a7ea39a4de1111d | Download, CC BY listed, ~137.3k triangles, FBX/Blend and textures | Historic vehicle only; not substitute for modern fire engine |
| Fire truck | https://sketchfab.com/3d-models/fire-truck-4a0d8c5bfca643d2aaa9b113ff752c26 | Download, CC BY listed, ~72.2k triangles | Inspect whether visual quality meets photorealistic target |

## Exclude or do not prioritize
- https://sketchfab.com/3d-models/f-16-fighting-falcon-fighter-jet-free-f0b00989e5634764848ef2c235c64db5 — CC BY-NC-SA, noncommercial; unsuitable for unrestricted distribution.
- https://sketchfab.com/3d-models/custom-motorcycle-89ba3a1f06a04ba0bfbd9daef95607b0 — CC BY-NC.
- https://sketchfab.com/3d-models/fire-truck-e0fadd42bd3b448eaa0eb660764c170a — 474 triangles, too basic for photorealistic target.

## Unreal 5.8 integration checklist
Verify each source and license; legally download through publisher; keep attribution. Do not upload third-party binary assets to public GitHub without permission. Inspect scale, UV, normals, PBR materials, interior, detachable wheels, doors and control surfaces; create optimized LODs. Integrate existing ANOMALIA vehicle systems, collision, sound, movement, fuel, damage, inventory, multiplayer and saves. Test in Unreal Editor and packaged Windows build before claiming integration.
