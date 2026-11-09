"""Deterministic, non-destructive procedural PREVIEW for started ANOMALIA'Z worlds.

Generates proposed biomes, candidate vegetation cells, settlement centres and
land-only road graphs in an isolated output folder. Never modifies UE5 maps.
It does NOT create a real Landscape, .umap, World Partition or baked PCG.

Examples:
  python scripts/ue5/worldgen/preview_world.py --world racconia-varkovia
  python scripts/ue5/worldgen/preview_world.py --world unknown-horror-x --write --output /tmp/world-preview
  python scripts/ue5/worldgen/preview_world.py --world skarvik --protected /path/protected-actors.json
"""
from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import math
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROFILES = ROOT / "config" / "worldgen" / "starter-worlds.json"
ALGO = "anomalia-worldgen-preview-v1"
COLORS = {
    "ocean": (35, 87, 129),
    "coast": (204, 188, 132),
    "forest": (56, 113, 68),
    "grassland": (115, 159, 82),
    "wetland": (69, 126, 113),
    "highland": (118, 124, 112),
    "snow": (220, 226, 231),
}


def stable_float(key: str, a: int, b: int) -> float:
    raw = hashlib.blake2b(f"{key}|{a}|{b}".encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(raw, "big") / 2**64


def smooth_noise(key: str, x: float, y: float) -> float:
    i, j = math.floor(x), math.floor(y)
    u, v = x - i, y - j
    u = u * u * (3 - 2 * u)
    v = v * v * (3 - 2 * v)
    a = stable_float(key, i, j)
    b = stable_float(key, i + 1, j)
    c = stable_float(key, i, j + 1)
    d = stable_float(key, i + 1, j + 1)
    return ((a * (1 - u) + b * u) * (1 - v) +
            (c * (1 - u) + d * u) * v)


def load_profiles() -> dict[str, dict]:
    doc = json.loads(PROFILES.read_text(encoding="utf-8"))
    if doc.get("schemaVersion") != 1:
        raise ValueError("Unsupported world profile format")
    profiles = {}
    for p in doc["profiles"]:
        wid = p["worldId"]
        if wid in profiles or not all(p.get(k) for k in ("name", "seed", "widthKm", "heightKm")):
            raise ValueError("Invalid or duplicate world profile")
        if not (0 <= p["density"] <= 1):
            raise ValueError("Density must be between zero and one")
        profiles[wid] = p
    return profiles


def load_protected(path: Path | None) -> list[dict]:
    if path is None:
        return []
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("schemaVersion") != 1 or not isinstance(doc.get("protected"), list):
        raise ValueError("Invalid protected actors manifest")
    protected, seen = [], set()
    for x in doc["protected"]:
        if not isinstance(x, dict) or not isinstance(x.get("id"), str) or not x["id"]:
            raise ValueError("Protected actor missing id")
        if x["id"] in seen:
            raise ValueError("Duplicate protected actor id")
        seen.add(x["id"])
        for k in ("xMeters", "yMeters", "radiusMeters"):
            if isinstance(x.get(k), bool) or not isinstance(x.get(k), (int, float)) or not math.isfinite(x[k]):
                raise ValueError(f"Protected actor {x['id']} missing {k}")
        if x["radiusMeters"] < 0:
            raise ValueError("Negative protected actor radius")
        protected.append(x)
    return protected


def sample_existing_r16(path: Path, grid: int, sea_level_u16: int) -> tuple[set[int], str, int]:
    """Sample land from an ORIGINAL, read-only unsigned little-endian R16 heightmap.

    WARNING: the true sea-level threshold must be supplied by the author; no
    elevation scale or native Landscape import is inferred from this preview.
    """
    safe_grid_bounds(grid)
    if isinstance(sea_level_u16, bool) or not isinstance(sea_level_u16, int) or not 0 <= sea_level_u16 <= 65535:
        raise ValueError("Sea level must be an unsigned R16 value 0..65535")
    raw = path.read_bytes()
    if len(raw) % 2:
        raise ValueError("R16 source must contain whole uint16 samples")
    resolution = math.isqrt(len(raw) // 2)
    if resolution * resolution * 2 != len(raw) or resolution < grid or resolution > 16385:
        raise ValueError("Expected a square R16 source with at least grid samples per axis")
    land = set()
    for y in range(grid):
        sy = min(resolution - 1, int((y + .5) / grid * resolution))
        for x in range(grid):
            sx = min(resolution - 1, int((x + .5) / grid * resolution))
            value = struct.unpack_from("<H", raw, 2 * (sy * resolution + sx))[0]
            if value > sea_level_u16:
                land.add(y * grid + x)
    return land, hashlib.sha256(raw).hexdigest(), resolution


def safe_grid_bounds(grid: int) -> None:
    if not isinstance(grid, int) or not 32 <= grid <= 160:
        raise ValueError("Preview grid size must be 32..160")


def generate_plan(profile: dict, grid: int = 64, protected: list[dict] | None = None,
                  seed_override: str | None = None, source_land_cells: set[int] | None = None,
                  source_sha: str | None = None, source_resolution: int | None = None) -> dict:
    """Generate candidate planning data ONLY; no files and no UE5 mutations."""
    safe_grid_bounds(grid)
    protected = list(protected or [])
    seed = seed_override or profile["seed"]
    if not isinstance(seed, str) or not seed:
        raise ValueError("Empty seed")
    key = f"{ALGO}|{profile['worldId']}|{seed}"
    width_m = profile["widthKm"] * 1000
    height_m = profile["heightKm"] * 1000
    cell_x, cell_y = width_m / grid, height_m / grid

    scores = []
    for y in range(grid):
        for x in range(grid):
            u, v = x / grid, y / grid
            large = smooth_noise(key + "|continental", u * 3.4, v * 3.4)
            medium = smooth_noise(key + "|medium", u * 10, v * 10)
            detail = smooth_noise(key + "|detail", u * 28, v * 28)
            scores.append(0.62 * large + 0.28 * medium + 0.1 * detail)
    # A preview-only land/water split; NOT a survey or existing heightmap.
    target_land = profile.get("landFraction")
    if target_land is None:
        target_land = .60  # illustration, explicitly not the original map land fraction
    land_count = min(len(scores), max(1, round(len(scores) * target_land)))
    land_ids = (set(sorted(range(len(scores)), key=lambda i: (-scores[i], i))[:land_count])
                if source_land_cells is None else set(source_land_cells))
    if any(i < 0 or i >= grid*grid for i in land_ids):
        raise ValueError("Source land mask has out-of-bounds cell indexes")
    def is_land(x: int, y: int) -> bool:
        return 0 <= x < grid and 0 <= y < grid and (y * grid + x) in land_ids

    blocked = set()
    for actor in protected:
        for y in range(grid):
            py = (y + .5) * cell_y - height_m / 2
            for x in range(grid):
                px = (x + .5) * cell_x - width_m / 2
                if math.hypot(px - actor["xMeters"], py - actor["yMeters"]) <= actor["radiusMeters"] + max(cell_x, cell_y):
                    blocked.add(y * grid + x)

    biomes: list[str] = []
    for y in range(grid):
        for x in range(grid):
            i = y * grid + x
            if i not in land_ids:
                biome = "ocean"
            elif any(not is_land(x + dx, y + dy) for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))):
                biome = "coast"
            else:
                moisture = smooth_noise(key + "|moisture", x / 11, y / 11)
                cold = smooth_noise(key + "|temperature", x / 21, y / 21)
                if scores[i] > .66 and cold < .36:
                    biome = "snow"
                elif scores[i] > .66:
                    biome = "highland"
                elif moisture > .66:
                    biome = "wetland"
                elif moisture > .35:
                    biome = "forest"
                else:
                    biome = "grassland"
            biomes.append(biome)

    # Candidate cells: immutable proposed PCG scatter mask, NOT actor placement.
    eligible = [i for i, biome in enumerate(biomes)
                if biome in ("forest", "grassland", "wetland", "highland") and i not in blocked]
    density = profile["density"]
    selected = sorted(eligible, key=lambda i: (stable_float(key + "|scatter", i % grid, i // grid), i))
    scatter = selected[:round(len(eligible) * density)]
    # A handful of candidate settlement centres, marked PROPOSAL ONLY.
    candidates = [i for i, biome in enumerate(biomes)
                  if biome in ("grassland", "forest", "highland") and i not in blocked]
    candidates.sort(key=lambda i: (stable_float(key + "|town", i % grid, i // grid), i))
    centres: list[dict] = []
    desired = max(4, min(12, round(width_m * height_m / 40_000_000)))
    minimum_spacing = max(3, grid // 9)
    for i in candidates:
        x, y = i % grid, i // grid
        if any(math.hypot(x - c["cell"][0], y - c["cell"][1]) < minimum_spacing for c in centres):
            continue
        centres.append({
            "id": f"proposed-settlement-{len(centres)+1:02d}",
            "type": "city-candidate" if len(centres) < 2 else "village-candidate",
            "cell": [x, y],
            "coordinatesMeters": [round((x + .5)*cell_x-width_m/2, 2),
                                   round((y + .5)*cell_y-height_m/2, 2)],
            "status": "proposal-not-placed",
        })
        if len(centres) >= desired:
            break

    def pathfind(a: list[int], b: list[int]) -> list[list[int]]:
        start, goal = tuple(a), tuple(b)
        frontier = [(0., 0, start)]
        costs = {start: 0.}
        previous = {}
        order = 0
        while frontier:
            _, _, current = heapq.heappop(frontier)
            if current == goal:
                route = [current]
                while route[-1] != start:
                    route.append(previous[route[-1]])
                return [list(p) for p in reversed(route)]
            x, y = current
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = (x + dx, y + dy)
                if not is_land(*nxt) or nxt[1] * grid + nxt[0] in blocked:
                    continue
                step = 1 + (0.6 if biomes[nxt[1]*grid+nxt[0]] in ("highland", "wetland") else 0.)
                new_cost = costs[current] + step
                if new_cost < costs.get(nxt, float("inf")):
                    costs[nxt] = new_cost
                    previous[nxt] = current
                    order += 1
                    heuristic = abs(nxt[0]-goal[0]) + abs(nxt[1]-goal[1])
                    heapq.heappush(frontier, (new_cost + heuristic, order, nxt))
        return []

    roads = []
    for i, end in enumerate(centres[1:], 1):
        start = min(centres[:i], key=lambda c: math.dist(c["cell"], end["cell"]))
        cells = pathfind(start["cell"], end["cell"])
        roads.append({
            "id": f"proposed-road-{i:02d}",
            "from": start["id"], "to": end["id"],
            "status": "preview-only-unreal-unverified" if cells else "requires-manual-bridge-or-detour",
            "cells": cells,
        })

    counts = {k: biomes.count(k) for k in COLORS}
    return {
        "format": "AZ-WORLDGEN-PREVIEW-1",
        "generatorVersion": ALGO,
        "name": profile["name"], "worldId": profile["worldId"],
        "dimensionsKm": [profile["widthKm"], profile["heightKm"]],
        "seed": seed, "grid": grid, "biomeCounts": counts,
        "previewLandFraction": round(len(land_ids)/(grid*grid), 6),
        "sourceR16HashSha256": source_sha, "sourceR16Resolution": source_resolution,
        "originalLandFractionKnown": profile.get("landFraction"),
        "density": density, "pcgEligibleCells": len(eligible), "pcgCandidateCells": len(scatter),
        "scatterIndices": scatter, "biomes": biomes, "settlements": centres, "roads": roads,
        "protectedActorIds": [x["id"] for x in protected],
        "protectedCells": sorted(blocked),
        "protectedActorsVerifiedAgainstUE5": False,
        "protectedManifestProvided": bool(protected),
        "terrainPolicy": profile["terrainPolicy"],
        "externalSourcePackage": profile["sourcePackage"],
        "warnings": [
            ("Synthetic BIOME/COAST preview only: not derived from original terrain or user heightmaps."
             if source_land_cells is None else
             "Coastline samples ORIGINAL R16 read-only; biome heights, roads and settlements are still synthetic proposals."),
            "Roads/settlements are proposals only, NOT merged with original roads, cities or protected UE actors.",
            "A native UE5 source audit and authoritative protected-actors manifest are required before any placement.",
        ],
        "nativeUE5MapGenerated": False,
        "nativePCGBaked": False,
        "originalWorldModified": False,
    }


def render_ppm(plan: dict) -> bytes:
    grid = plan["grid"]
    pixels = [COLORS[b] for b in plan["biomes"]]
    for road in plan["roads"]:
        for x, y in road["cells"]:
            pixels[y * grid + x] = (177, 146, 118)
    for centre in plan["settlements"]:
        x, y = centre["cell"]
        pixels[y * grid + x] = (220, 80, 75)
    return f"P6\n{grid} {grid}\n255\n".encode("ascii") + bytes(v for pix in pixels for v in pix)


def render_png(plan: dict, scale: int = 8) -> bytes:
    """Viewable true-color PNG; Python standard library only."""
    if not 1 <= scale <= 24:
        raise ValueError("Invalid PNG preview scale")
    grid = plan["grid"]
    pixels = [COLORS[b] for b in plan["biomes"]]
    for road in plan["roads"]:
        for x, y in road["cells"]:
            pixels[y * grid + x] = (177, 146, 118)
    for centre in plan["settlements"]:
        x, y = centre["cell"]
        pixels[y * grid + x] = (220, 80, 75)
    width = grid * scale
    data = bytearray()
    for y in range(grid):
        scan = b"".join(bytes(pixels[y*grid+x]) * scale for x in range(grid))
        for _ in range(scale):
            data.extend(b"\x00")
            data.extend(scan)

    def chunk(name: bytes, payload: bytes) -> bytes:
        return (struct.pack(">I", len(payload)) + name + payload +
                struct.pack(">I", zlib.crc32(name + payload) & 0xffffffff))

    return (b"\x89PNG\r\n\x1a\n" +
            chunk(b"IHDR", struct.pack(">IIBBBBB", width, width, 8, 2, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(bytes(data), 6)) +
            chunk(b"IEND", b""))


def write_isolated(plan: dict, folder: Path) -> list[str]:
    folder = folder.expanduser().resolve()
    # Refuse any path inside the checked-out source tree.
    if folder == ROOT or ROOT in folder.parents:
        raise ValueError("Output must be OUTSIDE the project source directory")
    if folder.exists():
        raise FileExistsError(f"Output already exists; never overwrite: {folder}")
    folder.mkdir(parents=True, exist_ok=False)
    report = folder / "world-preview.json"
    image_path = folder / "preview.ppm"
    png_path = folder / "preview.png"
    report.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    image_path.write_bytes(render_ppm(plan))
    png_path.write_bytes(render_png(plan, max(1, 512 // plan["grid"])))
    return [str(report), str(image_path), str(png_path)]


def main(argv: list[str] | None = None) -> dict:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--world", choices=sorted(load_profiles()), required=True)
    cli.add_argument("--grid", type=int, default=64)
    cli.add_argument("--seed", default=None)
    cli.add_argument("--protected", type=Path, default=None,
                     help="Optional exported, verified actor circles; never changed")
    cli.add_argument("--source-r16", type=Path, default=None,
                     help="Optional existing square R16 heightmap, read-only")
    cli.add_argument("--sea-level-u16", type=int, default=None,
                     help="Required original RAW16 sea-level threshold when using --source-r16")
    cli.add_argument("--write", action="store_true",
                     help="Write a new, isolated preview folder; default is dry-run")
    cli.add_argument("--output", type=Path, default=None)
    args = cli.parse_args(argv)
    if args.write != (args.output is not None):
        cli.error("--write and --output must be supplied together")
    if (args.source_r16 is None) != (args.sea_level_u16 is None):
        cli.error("--source-r16 and --sea-level-u16 must be supplied together")
    profile = load_profiles()[args.world]
    src_cells, src_sha, src_resolution = None, None, None
    if args.source_r16 is not None:
        src_cells, src_sha, src_resolution = sample_existing_r16(
            args.source_r16, args.grid, args.sea_level_u16)
    plan = generate_plan(profile, args.grid, load_protected(args.protected),
                         args.seed, src_cells, src_sha, src_resolution)
    if args.write:
        paths = write_isolated(plan, args.output)
    else:
        paths = []
    summary = {
        "worldId": args.world, "seed": plan["seed"], "grid": plan["grid"],
        "previewLandFraction": plan["previewLandFraction"],
        "candidateRoads": len(plan["roads"]),
        "candidateSettlements": len(plan["settlements"]),
        "candidatePCGCells": plan["pcgCandidateCells"],
        "protectedManifestProvided": plan["protectedManifestProvided"],
        "written": paths,
        "disclaimer": "Standalone preview only; no UE5 map or actual topography changed.",
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return plan


if __name__ == "__main__":
    main()
