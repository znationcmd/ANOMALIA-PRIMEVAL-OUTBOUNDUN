/** Original 200 m playable terrain. glTF X maps to UE X, glTF Z to UE -Y. */
const smooth = value => { const t = Math.max(0, Math.min(1, value)); return t*t*(3-2*t); };
export function playableHeight(x, z) {
  // Preserve all authored houses, loot, save positions and the full driving lane.
  // Relief begins outside their reserved parcels, with a smooth transition.
  const parcelClearance = Math.max(Math.abs(x)-68, Math.abs(z)-57);
  const roadClearance = Math.abs(z-15)-6;
  const mask = smooth(parcelClearance/16)*smooth(roadClearance/10);
  return mask * (1.8 + 1.4*Math.sin(x*.055)*Math.cos(z*.043));
}
export function playableNormal(x,z) {
  const dx=(playableHeight(x+.01,z)-playableHeight(x-.01,z))/.02;
  const dz=(playableHeight(x,z+.01)-playableHeight(x,z-.01))/.02;
  const length=Math.hypot(dx,1,dz);return [-dx/length,1/length,-dz/length];
}
