"""Generate seam-matched 16-bit UE Landscape RAW tiles for the 48 km ANOMALIA map.
Requires numpy. Output is an import source, not a .umap and not a playable level.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np

WORLD_METERS = 48_000
TILE_METERS = 4_000
SAMPLES_PER_TILE = 1009  # 4 m spacing; one shared border sample per neighboring tile
STEP = TILE_METERS / (SAMPLES_PER_TILE - 1)
HALF = WORLD_METERS / 2
# centers (east, north), radii (east, north), elevation contribution in meters
ISLANDS = [
    (-10_300, -9_000, 8_800, 7_500, 0),
    (9_400, 9_400, 8_500, 7_200, 0),
    (-2_400, 12_500, 1_700, 1_200, 90),
    (3_000, -13_000, 1_400, 1_000, 60),
    (15_500, -4_000, 1_250, 1_700, 110),
    (-15_000, 3_000, 1_100, 1_500, 80),
]

def height_at(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    land = np.zeros(x.shape, dtype=bool)
    height = np.full(x.shape, -180.0, dtype=np.float32)  # deep navigable-water bed
    for index, (cx, cy, rx, ry, bonus) in enumerate(ISLANDS):
        dx, dy = (x - cx) / rx, (y - cy) / ry
        angle = np.arctan2(dy, dx)
        # Deterministic low-frequency coastline detail; identical at shared tile borders.
        edge = (1.0 + .035 * np.sin(angle * 5 + index) +
                .022 * np.sin(angle * 11 - index * .7) +
                .012 * np.sin(angle * 19 + 1.3))
        radius = np.sqrt(dx * dx + dy * dy)
        island = radius <= edge
        land |= island
        coast = np.clip((edge - radius) / .11, 0, 1)
        plateau = 28 + 75 * np.clip(1 - radius / edge, 0, 1) ** .45
        mountain = 240 * np.exp(-(((x - cx * .96) / (rx * .3)) ** 2 + ((y - cy * 1.03) / (ry * .31)) ** 2))
        ridges = 15 * np.sin(x / 610 + index) * np.cos(y / 780 - index * .3)
        candidate = -180 + coast * (180 + plateau + mountain + bonus + ridges)
        height = np.where(island, np.maximum(height, candidate), height)
    return height, land

def encode_height(height: np.ndarray) -> np.ndarray:
    # Maps -512..+512 m to unsigned 16-bit centered at Unreal sea level (32768).
    normalized = np.clip((height + 512.0) / 1024.0, 0.0, 1.0)
    return np.rint(normalized * 65535).astype("<u2")

def generate(output: Path, measure_only: bool = False) -> dict:
    # Independently verify dry land at 25 m resolution before producing tiles.
    axis = np.arange(-HALF + 12.5, HALF, 25, dtype=np.float32)
    xx, yy = np.meshgrid(axis, axis)
    heights, _ = height_at(xx, yy)
    # Emergent land is strictly above the authored sea surface (0 m).
    area_km2 = float(np.count_nonzero(heights > 0.0) * .025 * .025)
    result = {"worldWidthKm": 48, "worldDepthKm": 48, "totalAreaKm2": 2304,
              "dryLandKm2SampledAt25m": round(area_km2, 3),
              "sampleSpacingMeters": STEP, "tileMeters": TILE_METERS,
              "heightmapResolution": SAMPLES_PER_TILE,
              "heightEncoding": "unsigned little-endian 16-bit RAW; -512m..+512m; sea level 0m",
              "suggestedLandscapeScaleCm": {"x": 396.8254, "y": 396.8254, "z": 200},
              "islands": [{"centerMeters": [i[0], i[1]], "radiiMeters": [i[2], i[3]]} for i in ISLANDS]}
    if area_km2 <= 300:
        raise ValueError(f"Dry land target failed: {area_km2:.2f} km2 <= 300 km2")
    if measure_only:
        return result
    output.mkdir(parents=True, exist_ok=True)
    coordinates = np.arange(SAMPLES_PER_TILE, dtype=np.float32) * STEP
    for row in range(WORLD_METERS // TILE_METERS):
        north = HALF - row * TILE_METERS - coordinates
        for col in range(WORLD_METERS // TILE_METERS):
            east = -HALF + col * TILE_METERS + coordinates
            tx, ty = np.meshgrid(east, north)
            tile_height, _ = height_at(tx, ty)
            filename = output / f"height_x{col}_y{row}.r16"
            encode_height(tile_height).tofile(filename)
    (output / "terrain-manifest.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, nargs="?", default=Path("unreal/TerrainSource"))
    parser.add_argument("--measure-only", action="store_true")
    args = parser.parse_args()
    print(json.dumps(generate(args.output, args.measure_only), indent=2))
