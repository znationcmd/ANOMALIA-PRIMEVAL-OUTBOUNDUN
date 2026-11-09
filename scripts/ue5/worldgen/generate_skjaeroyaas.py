"""SKJÆRØYÅS — deterministic ORIGINAL 15 x 15 km Norwegian fjord heightfield.

Produces 9 seamless 5 km RAW16 source tiles (little-endian) + a true-colour
topographic PNG and manifest. Input is a new fictional landscape: no copied
Norwegian terrain, existing UE maps, licensed assets, roads, or .umap files.
The output is a *Landscape import source*, not an installed/packaged UE5 map.

Requirements: Python 3.10+ standard library. A new, NONEXISTENT folder
OUTSIDE this repository is mandatory; files are never overwritten.
  python scripts/ue5/worldgen/generate_skjaeroyaas.py --output /tmp/skjaeroyaas-stage

Resolution 505: 504 quads per tile, 3 x 3 tiles with shared 1-sample edges;
set Landscape X/Y scale = (500000 / 504) cm (= 992.063492 cm).
For UE Landscape 16-bit storage, Z scale 800 cm provides +/-2048 m range;
at sea level value 32768, zero world Z. Verify these settings in UE 5.8.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import zlib

PROJECT = Path(__file__).resolve().parents[3]
WORLD_ID = "skjaeroyaas"
WORLD_NAME = "SKJÆRØYÅS"
WIDTH_M = 15_000.0
TILE_M = 5_000.0
COUNT = 3
SEA_LEVEL_U16 = 32768
Z_SCALE_CM = 800.0
SEED = "ANOMALIA-2026-SKJAEROYAAS"
VERSION = "fjords-r16-v1"
APPROVED_SAMPLES = (33, 505, 1009)  # 33 for fast tests only (NOT recommended for UE import)


def terrain(x: float, y: float) -> float:
    """A continuous, global-coordinate fictional fjord terrain in metres."""
    a = 1 - ((x + 3450) / 10_500)**2 - ((y - 850) / 9_000)**2
    b = 1 - ((x - 4900) / 5_600)**2 - ((y + 1500) / 8_500)**2
    c = 1 - ((x - 2100) / 2_200)**2 - ((y + 5900) / 2200)**2
    edge = .12 * math.sin(x / 1480 + 1.3 * math.cos(y / 2300))
    edge += .055 * math.sin(x / 435 + y / 640)
    solidity = max(a, b, c) + edge

    # Main deep fjord reaches the south coast and cuts into the mainland.
    fjord_centre = 730 + 1040 * math.sin((y + 2250) / 2350) + 340 * math.sin(y / 590)
    fjord_halfwidth = 410 + 170 * (1 + math.sin(y / 1280))
    main_fjord = -6600 < y < 5800 and abs(x - fjord_centre) < fjord_halfwidth
    # Eastern and western connected branch bays, never a mathematically straight trench.
    west_bay = -4600 < x < 900 and abs(y - (760 + 590 * math.sin(x / 1360))) < 400
    east_bay = 150 < x < 7300 and abs(y - (-1700 + 650 * math.sin(x / 1120))) < 350

    if solidity < .11 or main_fjord or west_bay or east_bay:
        depth = -145 - 55 * math.sin(x / 1800) ** 2 - 32 * math.cos(y / 1200) ** 2
        return depth  # navigable sea bed, below zero

    interior = min(1.0, max(0.0, (solidity - .11) / .44))
    floor = 15 + 170 * interior
    rough = (35 * math.sin(x / 1100) * math.cos(y / 1370) +
             19 * math.sin(x / 335 + y / 480))
    peaks = (
        1290 * math.exp(-(((x + 4200) / 1850)**2 + ((y - 2800) / 2260)**2)) +
        1100 * math.exp(-(((x - 4300) / 1620)**2 + ((y + 1150) / 2150)**2)) +
        870 * math.exp(-(((x + 430) / 1460)**2 + ((y + 5100) / 1550)**2)) +
        760 * math.exp(-(((x - 3100) / 1550)**2 + ((y - 5000) / 1970)**2))
    )
    return min(1860.0, max(2.0, floor + interior * (rough + peaks)))


def encode_height(metres: float) -> int:
    # (u16-32768)/128 * ZScaleCm/100 == physical height in metres.
    value = round(SEA_LEVEL_U16 + metres * 12800.0 / Z_SCALE_CM)
    if not 0 <= value <= 65535:
        raise ValueError(f"Height outside Landscape encoding: {metres} m")
    return value


def colour(metres: float) -> tuple[int, int, int]:
    if metres <= 0:
        return (21, 71, 112)
    if metres < 28:
        return (167, 170, 127)
    if metres < 290:
        return (35, 100, 67)  # pine forests
    if metres < 590:
        return (92, 126, 92)  # treeline / tundra
    if metres < 830:
        return (139, 143, 131)  # fjell cliffs
    return (231, 237, 240)   # snow


def png(rgb: bytes, width: int, height: int) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(
            ">I", zlib.crc32(tag + data) & 0xffffffff
        )
    scan = b"".join(b"\x00" + rgb[y*width*3:(y+1)*width*3] for y in range(height))
    return (b"\x89PNG\r\n\x1a\n" +
            chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(scan, 6)) + chunk(b"IEND", b""))


def generate(output: Path, samples_per_tile: int = 505,
             preview_size: int = 384) -> dict:
    if samples_per_tile not in APPROVED_SAMPLES:
        raise ValueError(f"Samples per tile must be one of {APPROVED_SAMPLES}")
    if not 64 <= preview_size <= 1024:
        raise ValueError("Preview resolution must be between 64 and 1024")
    output = output.expanduser().resolve()
    if output == PROJECT or PROJECT in output.parents:
        raise ValueError("Output must be OUTSIDE GitHub/Unreal source project")
    if output.exists():
        raise FileExistsError("Destination exists: refusing to overwrite terrain")
    output.mkdir(parents=True, exist_ok=False)

    shared_edge = samples_per_tile - 1
    spacing_m = TILE_M / shared_edge
    tiles = []
    for row in range(COUNT):
        for col in range(COUNT):
            filename = f"height_x{col}_y{row}.r16"
            path = output / filename
            digest = hashlib.sha256()
            with path.open("wb") as f:
                for j in range(samples_per_tile):
                    # Row 0 is NORTH; orientation must be checked during UE import.
                    y = 7500 - (row*TILE_M + j*spacing_m)
                    data = bytearray()
                    for i in range(samples_per_tile):
                        x = -7500 + col*TILE_M + i*spacing_m
                        data.extend(struct.pack("<H", encode_height(terrain(x, y))))
                    f.write(data)
                    digest.update(data)
            tiles.append({
                "column": col, "row": row, "file": filename,
                "samples": [samples_per_tile, samples_per_tile],
                "sha256": digest.hexdigest(),
                "bytes": path.stat().st_size,
            })

    # A free-standing map overview; NOT a rendered Unreal world.
    img = bytearray()
    area_land = 0
    for j in range(preview_size):
        y = 7500 - (j + .5) * WIDTH_M / preview_size
        for i in range(preview_size):
            x = -7500 + (i + .5) * WIDTH_M / preview_size
            h = terrain(x, y)
            area_land += h > 0
            img.extend(colour(h))
    (output / "skjaeroyaas-overview.png").write_bytes(png(bytes(img), preview_size, preview_size))

    manifest = {
        "schema": "ANOMALIA-NORDIC-R16-1", "map": WORLD_NAME, "worldId": WORLD_ID,
        "algorithmVersion": VERSION, "seed": SEED,
        "independentLevel": True, "dimensionsKm": [15, 15], "areaKm2": 225,
        "heightEncoding": "unsigned 16-bit little-endian R16, 32768 = sea level",
        "suggestedLandscapeScaleCm": {
            "x": round(TILE_M * 100 / shared_edge, 8),
            "y": round(TILE_M * 100 / shared_edge, 8),
            "z": Z_SCALE_CM,
        },
        "heightRangeMetres": [-2048, 2047.9375],
        "tileGrid": [3, 3], "tileMeters": 5000,
        "samplesPerTile": samples_per_tile, "sampleSpacingMeters": spacing_m,
        "previewLandFraction": round(area_land / (preview_size**2), 5),
        "terrainCreatedInUnreal": False, "nativeLevelPackaged": False,
        "assetsPlaced": False, "noExistingFilesChanged": True,
        "verificationRequired": [
            "Confirm tiled Landscape import orientation and Z scale in UE 5.8",
            "Verify shared edge samples and collision after UE import",
            "Build World Partition level on a staging copy",
            "Add PCG biome graphs, roads, towns, interiors and gameplay",
            "Test playable packaged build on target PC",
        ],
        "tiles": tiles,
    }
    (output / "terrain-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--samples", type=int, default=505)
    p.add_argument("--preview-size", type=int, default=384)
    args = p.parse_args()
    doc = generate(args.output, args.samples, args.preview_size)
    print(json.dumps({
        "world": doc["map"], "sizeKm": doc["dimensionsKm"],
        "tiles": len(doc["tiles"]), "estimatedLandFraction": doc["previewLandFraction"],
        "sourceOnlyNotUnrealLevel": True,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
