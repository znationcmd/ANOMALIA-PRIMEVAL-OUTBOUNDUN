"""Generate REAL shared-edge 16-bit UE Landscape input tiles for CHERNASKALUXRIA.

The 100 x 100 km world is a 20 x 20 grid of 5 km regions. Each tile uses
253 x 253 samples (252 quads) with exactly identical shared-edge samples.
More detailed authored city/road/building meshes will be independent layers.
This tool produces source .r16, never pretends to create an Unreal .umap.
"""
from __future__ import annotations

import argparse
from array import array
import hashlib
import json
from pathlib import Path
import sys

from chernaskaluxria_world import (
    DISPLAY_NAME, GRID_RESOLUTION, MAP_ID, SIDE_METRES,
    SAMPLES_PER_TILE_SIDE, TILES_PER_AXIS, TILE_SIDE_METRES,
    SAVE_NAMESPACE, terrain_height,
)

# The 1009-sample high-resolution design is intentionally retained for
# optional LOD/detail datasets; 253 is the initial, memory-safe UE Landscape base.
BASE_SAMPLES = 253
BASE_QUADS = BASE_SAMPLES - 1
METRES_PER_SAMPLE = TILE_SIDE_METRES / BASE_QUADS
ENCODING = "uint16_little_endian; sample=(32768+height_metres*16), Zscale=800cm"
EXPECTED_BYTES = BASE_SAMPLES * BASE_SAMPLES * 2


def encode(height: float) -> int:
    return max(0, min(65535, round(32768.0 + 16.0 * height)))


def tile_filename(col: int, row: int) -> str:
    if not 0 <= col < TILES_PER_AXIS or not 0 <= row < TILES_PER_AXIS:
        raise ValueError("Tile index outside 20x20 grid")
    return f"CHERNASKALUXRIA_x{col:02}_y{row:02}.r16"


def make_tile(col: int, row: int) -> bytes:
    west = -SIDE_METRES / 2 + TILE_SIDE_METRES * col
    north = SIDE_METRES / 2 - TILE_SIDE_METRES * row
    data = array("H")
    for y in range(BASE_SAMPLES):
        n = north - METRES_PER_SAMPLE * y
        data.extend(encode(terrain_height(west + METRES_PER_SAMPLE * x, n))
                    for x in range(BASE_SAMPLES))
    if sys.byteorder != "little":
        data.byteswap()
    return data.tobytes()


def manifest_header() -> dict:
    return {
        "schemaVersion": 1,
        "mapId": MAP_ID,
        "displayName": DISPLAY_NAME,
        "saveNamespace": SAVE_NAMESPACE,
        "worldWidthMetres": SIDE_METRES,
        "worldHeightMetres": SIDE_METRES,
        "grid": [TILES_PER_AXIS, TILES_PER_AXIS],
        "tileSideMetres": TILE_SIDE_METRES,
        "samplesPerAxis": BASE_SAMPLES,
        "quadsPerAxis": BASE_QUADS,
        "globalVerticesPerAxis": TILES_PER_AXIS * BASE_QUADS + 1,
        "metresPerSample": METRES_PER_SAMPLE,
        "expectedBytesPerTile": EXPECTED_BYTES,
        "heightEncoding": ENCODING,
        "nativeImported": False,
        "gameplayValidated": False,
        "sourceOnly": True,
    }


def generate(out: Path, indices: list[tuple[int, int]]) -> dict:
    if not indices:
        raise ValueError("No tiles requested")
    out.mkdir(parents=True, exist_ok=True)
    tiles = []
    for col, row in indices:
        filename = tile_filename(col, row)
        path = out / filename
        source = make_tile(col, row)
        if len(source) != EXPECTED_BYTES:
            raise RuntimeError("Invalid RAW byte count")
        digest = hashlib.sha256(source).hexdigest()
        if path.is_file():
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise FileExistsError("Existing tile differs, refusing overwrite: " + filename)
        else:
            with path.open("xb") as file:
                file.write(source)
        tiles.append({"col": col, "row": row, "filename": filename,
                      "bytes": EXPECTED_BYTES, "sha256": digest})
    # A run receipt is always uniquely named and never replaces author data.
    info = manifest_header()
    info["tiles"] = tiles
    info["tileCount"] = len(tiles)
    info["state"] = "HEIGHT_SOURCE_TILES_CREATED_NOT_IMPORTED"
    return info


def check_shared_edges(out: Path, col: int, row: int) -> dict:
    """Check exact byte-for-byte edges of adjacent imported height sources."""
    import struct
    left = out / tile_filename(col, row)
    if not left.is_file():
        raise FileNotFoundError(left)
    src = array("H")
    src.frombytes(left.read_bytes())
    if sys.byteorder != "little": src.byteswap()
    if len(src) != BASE_SAMPLES**2:
        raise ValueError("Invalid left tile")
    checked = {}
    if col + 1 < TILES_PER_AXIS:
        right = array("H")
        right.frombytes((out / tile_filename(col+1, row)).read_bytes())
        if sys.byteorder != "little": right.byteswap()
        if len(right) != BASE_SAMPLES**2:
            raise ValueError("Invalid right tile")
        checked["east"] = all(src[y*BASE_SAMPLES+BASE_SAMPLES-1] ==
                              right[y*BASE_SAMPLES] for y in range(BASE_SAMPLES))
    if row + 1 < TILES_PER_AXIS:
        bottom = array("H")
        bottom.frombytes((out / tile_filename(col, row+1)).read_bytes())
        if sys.byteorder != "little": bottom.byteswap()
        if len(bottom) != BASE_SAMPLES**2:
            raise ValueError("Invalid bottom tile")
        checked["south"] = all(src[(BASE_SAMPLES-1)*BASE_SAMPLES+x] == bottom[x]
                               for x in range(BASE_SAMPLES))
    if not all(checked.values()):
        raise RuntimeError("A shared terrain edge is discontinuous")
    return checked


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--col", type=int, default=10)
    parser.add_argument("--row", type=int, default=10)
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    if args.all:
        requested = [(col, row) for row in range(TILES_PER_AXIS)
                     for col in range(TILES_PER_AXIS)]
    else:
        start = args.row*TILES_PER_AXIS + args.col
        if not 0 <= start < 400 or not 1 <= args.count <= 400-start:
            parser.error("Invalid tile range")
        requested = [(i % TILES_PER_AXIS, i // TILES_PER_AXIS)
                     for i in range(start, start+args.count)]
    result = generate(args.output, requested)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.report.open("x", encoding="utf-8") as out:
            json.dump(result, out, indent=2)
    print(json.dumps({"state": result["state"], "tileCount": len(requested),
                      "firstTile": result["tiles"][0]["filename"],
                      "sampleSpacingMeters": METRES_PER_SAMPLE}))


if __name__ == "__main__":
    main()
