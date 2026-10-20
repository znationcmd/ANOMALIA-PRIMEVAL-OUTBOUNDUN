"""Generate a lighter, seam-matched ANOMALIA 48 x 48 km tiled Landscape SOURCE.

Original 1009-sample heightmaps remain untouched. This opt-in 253-sample draft
uses 576 landscape components, versus 9216 for the original 1009-sample tiles
(63 quads/section, 2x2 sections/component). The files are NOT a playable .umap.
Run with Python 3 and NumPy from the repository root or any directory.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SOURCE_SCRIPT = Path(__file__).with_name("generate-terrain.py")
DEFAULT_OUTPUT = ROOT / "unreal" / "TerrainPreview"
SAMPLES = 253
TILES_PER_SIDE = 12
PREFIX = "ANOMALIA"
MANIFEST = "draft-terrain-manifest.json"
SCALE_XY_CM = 400000.0 / (SAMPLES - 1)

spec = importlib.util.spec_from_file_location("anomalia_original_terrain", SOURCE_SCRIPT)
terrain = importlib.util.module_from_spec(spec)
spec.loader.exec_module(terrain)


def tile_name(col: int, row: int) -> str:
    if not 0 <= col < TILES_PER_SIDE or not 0 <= row < TILES_PER_SIDE:
        raise ValueError("Tile coordinate out of range")
    return f"{PREFIX}_x{col}_y{row}.r16"


def tile_bytes(col: int, row: int) -> bytes:
    # Derive world-grid endpoints in float64 before casting, so adjacent tiles
    # share EXACTLY the same float32 edge coordinates, even with non-integer steps.
    x = np.linspace(-24000 + col * 4000, -24000 + (col + 1) * 4000,
                    SAMPLES, dtype=np.float64).astype(np.float32)
    y = np.linspace(24000 - row * 4000, 24000 - (row + 1) * 4000,
                    SAMPLES, dtype=np.float64).astype(np.float32)
    xx, yy = np.meshgrid(x, y)
    heights, _land = terrain.height_at(xx, yy)
    return terrain.encode_height(heights).tobytes()


def tile_file(output: Path, col: int, row: int) -> Path:
    return output / tile_name(col, row)


def save_tile(output: Path, col: int, row: int) -> bool:
    """True if created, False if untouched; never overwrite an existing tile."""
    dest = tile_file(output, col, row)
    data = tile_bytes(col, row)
    if dest.exists():
        if dest.read_bytes() != data:
            raise ValueError(f"Existing tile differs from current source, NOT replaced: {dest}")
        return False
    output.mkdir(parents=True, exist_ok=True)
    # Temporary file in same directory allows atomic replace on Windows.
    # The destination is checked first; don't run parallel writers here.
    handle, tmp = tempfile.mkstemp(prefix=".anomalia-part-", suffix=".r16", dir=output)
    try:
        with os.fdopen(handle, "wb") as f:
            f.write(data)
        if dest.exists():
            if dest.read_bytes() != data:
                raise ValueError(f"Concurrent tile conflict: {dest}")
            return False
        os.replace(tmp, dest)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return True


def edges(content: bytes) -> tuple[bytes, bytes, bytes, bytes]:
    expected = SAMPLES * SAMPLES * 2
    if len(content) != expected:
        raise ValueError(f"Tile byte count {len(content)} != {expected}")
    stride = SAMPLES * 2
    top, bottom = content[:stride], content[-stride:]
    left = b"".join(content[r * stride:r * stride + 2] for r in range(SAMPLES))
    right = b"".join(content[r * stride + stride - 2:(r + 1) * stride] for r in range(SAMPLES))
    return top, bottom, left, right


def verify_tiles(output: Path, cols: int = 12, rows: int = 12) -> dict:
    samples = {}
    checksums = {}
    missing = []
    for row in range(rows):
        for col in range(cols):
            path = tile_file(output, col, row)
            if not path.is_file():
                missing.append(tile_name(col, row))
                continue
            contents = path.read_bytes()
            samples[(col, row)] = edges(contents)
            checksums[tile_name(col, row)] = hashlib.sha256(contents).hexdigest()
    if missing:
        raise ValueError(f"Missing {len(missing)} tiles: {', '.join(missing[:8])}")
    seams = 0
    for row in range(rows):
        for col in range(cols):
            top, bottom, left, right = samples[(col, row)]
            if col + 1 < cols:
                if right != samples[(col + 1, row)][2]:
                    raise ValueError(f"Vertical seam mismatch: ({col},{row}) / ({col + 1},{row})")
                seams += 1
            if row + 1 < rows:
                if bottom != samples[(col, row + 1)][0]:
                    raise ValueError(f"Horizontal seam mismatch: ({col},{row}) / ({col},{row + 1})")
                seams += 1
    return {"tilesVerified": cols * rows, "seamsVerified": seams,
            "byteCountPerTile": SAMPLES * SAMPLES * 2,
            "tileSHA256": checksums}


def metadata(verification: dict) -> dict:
    return {
        "status": "terrain_sources_verified_not_imported",
        "description": "ANOMALIA World Partition playtest terrain; NOT .umap or final art",
        "sourceGeneratorSHA256": hashlib.sha256(SOURCE_SCRIPT.read_bytes()).hexdigest(),
        "worldMeters": [48000, 48000],
        "tileMeters": 4000,
        "tiles": [12, 12],
        "heightmapResolution": [SAMPLES, SAMPLES],
        "heightmapFormat": "little-endian unsigned 16-bit .r16",
        "filenameExample": tile_name(0, 0),
        "componentQuads": 126,
        "componentsPerTile": [2, 2],
        "totalLandscapeComponents": 576,
        "recommendedImportScaleCm": {
            "x": round(SCALE_XY_CM, 8),
            "y": round(SCALE_XY_CM, 8),
            "z": 200.0,
        },
        "sourceRowsRunNorthToSouth": True,
        "flipYAxisRequiresInEditorVisualVerification": True,
        "seaLevelMeters": 0,
        "expectedHorizontalCoverageMeters": (SAMPLES - 1) * SCALE_XY_CM / 100 * 12,
        **verification,
    }


def generate(output: Path, verify_only: bool = False) -> dict:
    output = output.resolve()
    manifest_path = output / MANIFEST
    source_hash = hashlib.sha256(SOURCE_SCRIPT.read_bytes()).hexdigest()
    if manifest_path.is_file():
        prior = json.loads(manifest_path.read_text(encoding="utf-8"))
        if prior.get("sourceGeneratorSHA256") != source_hash:
            raise ValueError("Source generator changed; refusing to mix existing and new tiles")
    if not verify_only:
        for row in range(TILES_PER_SIDE):
            for col in range(TILES_PER_SIDE):
                save_tile(output, col, row)
    verified = verify_tiles(output, TILES_PER_SIDE, TILES_PER_SIDE)
    result = metadata(verified)
    # Check the full tile hashes against the previous manifest on every run,
    # including --verify-only (detects tampering away from shared edges).
    encoded = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if manifest_path.exists():
        if manifest_path.read_text(encoding="utf-8") != encoded:
            raise ValueError("Existing terrain manifest differs; left unchanged")
    elif not verify_only:
        output.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(encoded, encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--verify-only", action="store_true",
                        help="Only inspect existing tiles; never generate new data")
    args = parser.parse_args()
    print(json.dumps(generate(args.output, args.verify_only), ensure_ascii=False, indent=2))
