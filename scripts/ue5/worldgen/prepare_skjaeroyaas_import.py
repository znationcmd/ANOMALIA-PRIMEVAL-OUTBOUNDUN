"""Prepare an importable SKJÆRØYÅS UE5 Landscape package from verified RAW16 tiles.

Pure Python, no Unreal runtime and no third-party packages.
- Joins all nine 5 km tiles to one continuous 1513x1513 R16 heightmap
- Verifies source SHA256, tile seams and output size
- Generates coherent roads/settlement/forest location candidates aligned to
  the SAME continuous height function as the heightmap (not a separate seed)
- Writes manifest and CSV for PCG/spline authoring, no actors, .umap or UE edits
- Refuses overwrites and output inside source checkout

Run after generate_skjaeroyaas.py on a fresh external staging folder:
  python scripts/ue5/worldgen/prepare_skjaeroyaas_import.py \
    --tiles /path/to/SKJAEROYAAS_R16_SOURCE --output /path/to/IMPORT_NEW
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import heapq
import json
import math
from pathlib import Path
import struct

import generate_skjaeroyaas as terrain_source

ROOT = Path(__file__).resolve().parents[3]
EXPECTED_WORLD = "skjaeroyaas"
SEA_U16 = 32768
NAMES = (
    ("Skjærnes", "harbour", -4100, -2700),
    ("Bjørnevik", "fishing-village", -4250, 3350),
    ("Åshamn", "harbour", 4100, -3900),
    ("Fjellgård", "mountain-village", -1950, 4750),
    ("Nordvik", "fishing-village", 4850, 3750),
    ("Frostmyra", "forest-village", -2650, -5050),
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _inside(world_x: float, world_y: float) -> bool:
    return -7500 <= world_x <= 7500 and -7500 <= world_y <= 7500


def _slope(x: float, y: float, radius=30.0) -> float:
    h = terrain_source.terrain
    if not _inside(x-radius, y-radius) or not _inside(x+radius, y+radius):
        return float("inf")
    return math.hypot(h(x+radius, y)-h(x-radius, y),
                      h(x, y+radius)-h(x, y-radius)) / (2*radius)


def _land(x: float, y: float, max_slope=0.42) -> bool:
    h = terrain_source.terrain(x, y)
    return 16 < h < 680 and _slope(x, y) < max_slope


def _pick_site(name: str, kind: str, anchor_x: int, anchor_y: int,
               sites: list[dict]) -> dict:
    best = None
    for radius in range(0, 4601, 200):
        for dy in range(-radius, radius+1, 200):
            for dx in range(-radius, radius+1, 200):
                if max(abs(dx), abs(dy)) != radius:
                    continue
                x, y = anchor_x + dx, anchor_y + dy
                if not _inside(x, y) or not _land(x, y, .24):
                    continue
                if any(math.hypot(x - old["xMeters"], y - old["yMeters"]) < 1300
                       for old in sites):
                    continue
                h = terrain_source.terrain(x, y)
                if kind == "mountain-village" and h < 65:
                    continue
                score = math.hypot(dx, dy) + .5*abs(h-(80 if "harbour" in kind else 160))
                if best is None or score < best[0]:
                    best = (score, x, y, h)
        if best and best[0] < radius + 500:
            break
    if best is None:
        raise ValueError(f"No sufficiently flat, separate site for {name}")
    return {"id": f"village-{len(sites)+1:02d}", "name": name, "type": kind,
            "xMeters": best[1], "yMeters": best[2],
            "zMeters": round(best[3], 2), "status": "marker-only-no-buildings"}


def _grid_node(x: int, y: int, steps: int) -> tuple[int, int]:
    cell = 15000 / (steps-1)
    return (max(0, min(steps-1, round((x+7500)/cell))),
            max(0, min(steps-1, round((7500-y)/cell))))


def _node_xy(gx: int, gy: int, steps: int) -> tuple[float, float]:
    cell = 15000 / (steps-1)
    return (-7500 + gx*cell, 7500 - gy*cell)


def _road(a: dict, b: dict, steps: int = 101) -> list[list[int]]:
    start = _grid_node(a["xMeters"], a["yMeters"], steps)
    goal = _grid_node(b["xMeters"], b["yMeters"], steps)
    heights = {}
    def get_h(node: tuple[int, int]) -> float:
        if node not in heights:
            heights[node] = terrain_source.terrain(*_node_xy(*node, steps))
        return heights[node]
    if get_h(start) <= 0 or get_h(goal) <= 0:
        return []
    frontier = [(0.0, 0, start)]
    costs = {start: 0.0}
    parents = {}
    order = 0
    while frontier:
        _, _, cur = heapq.heappop(frontier)
        if cur == goal:
            seq = [cur]
            while seq[-1] != start:
                seq.append(parents[seq[-1]])
            seq.reverse()
            # Dense polyline is data for later spline authoring, not a road mesh.
            return [[round(_node_xy(x,y,steps)[0]), round(_node_xy(x,y,steps)[1]),
                     round(terrain_source.terrain(*_node_xy(x,y,steps)), 2)]
                    for x,y in seq]
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),
                      (1,1),(1,-1),(-1,1),(-1,-1)):
            nx,ny = cur[0]+dx,cur[1]+dy
            if not (1 <= nx < steps-1 and 1 <= ny < steps-1):
                continue
            next_node=(nx,ny)
            height = get_h(next_node)
            if height < 10 or height > 730:
                continue
            climb = abs(height-get_h(cur))
            dist = math.hypot(dx,dy)*15000/(steps-1)
            slope = climb / dist
            if slope > 0.44:
                continue  # cannot propose roads over near-vertical cliff
            step = dist*(1 + min(18, slope*34))
            new_cost = costs[cur]+step
            if new_cost < costs.get(next_node, float("inf")):
                costs[next_node]=new_cost
                parents[next_node]=cur
                order+=1
                heuristic = math.hypot(nx-goal[0],ny-goal[1])*15000/(steps-1)
                heapq.heappush(frontier,(new_cost+heuristic,order,next_node))
    return []


def plan_layout() -> dict:
    sites=[]
    for args in NAMES:
        sites.append(_pick_site(*args,sites))
    edges=[]
    connected=[sites[0]]
    remaining=sites[1:]
    while remaining:
        start,end=min(((a,b) for a in connected for b in remaining),
                      key=lambda t: math.hypot(t[0]["xMeters"]-t[1]["xMeters"],
                                               t[0]["yMeters"]-t[1]["yMeters"]))
        path=_road(start,end)
        edges.append({"from":start["id"],"to":end["id"],"pointsMeters":path,
                      "status":"candidate-route-no-UE-mesh" if path
                      else "not-connected-may-require-ferry-or-bridge"})
        connected.append(end)
        remaining.remove(end)

    # Outdoor tree anchor candidates, deterministic, filtered by terrain and roads.
    forest=[]
    for gy in range(-7200,7201,240):
        for gx in range(-7200,7201,240):
            x = gx + 35*(2*int.from_bytes(hashlib.blake2b(
                f"x|{gx}|{gy}".encode(), digest_size=2).digest(),"big")/65535-1)
            y = gy + 35*(2*int.from_bytes(hashlib.blake2b(
                f"y|{gx}|{gy}".encode(), digest_size=2).digest(),"big")/65535-1)
            key=int.from_bytes(hashlib.blake2b(
                f"tree|{gx}|{gy}".encode(),digest_size=2).digest(),"big")
            if key / 65535 > 0.47 or not _land(x,y,.44):
                continue
            h=terrain_source.terrain(x,y)
            if h > 580 or any(math.hypot(x-s["xMeters"],y-s["yMeters"]) < 380
                              for s in sites):
                continue
            # Prevent forest samples overlapping candidate road centre lines.
            if any(math.hypot(x-p[0],y-p[1]) < 110
                   for e in edges for p in e["pointsMeters"][::2]):
                continue
            forest.append({"xMeters":round(x,2),"yMeters":round(y,2),
                           "zMeters":round(h,2),
                           "biome":"pine-birch-forest" if h < 310 else "subalpine-birch",
                           "status":"PCG-anchor-only"})
    return {"schemaVersion":1, "worldId":EXPECTED_WORLD,"name":"SKJÆRØYÅS",
            "dimensionsKm":[15,15],"coordinateOrigin":"centre of heightmap (0,0,0)",
            "units":"metres; positive X east, positive Y north, Z sea-level=0",
            "landscapeImportOrientation":"verify north/south row flip before spawning",
            "villages":sites,"roadCandidates":edges,"forestAnchors":forest,
            "generatedInUnreal":False,"roadMeshesBuilt":False,
            "buildingMeshesPlaced":False,"forestMeshesPlaced":False}


def _load_source(source: Path) -> tuple[dict, dict[tuple[int,int], bytes], int]:
    manifest=json.loads((source/"terrain-manifest.json").read_text(encoding="utf-8"))
    if manifest.get("worldId") != EXPECTED_WORLD or manifest.get("tileGrid") != [3,3]:
        raise ValueError("Not a SKJÆRØYÅS 3x3 source package")
    n=manifest.get("samplesPerTile")
    if n not in (33, 505, 1009):
        raise ValueError("Unrecognized tile size")
    files={}
    seen=set()
    for tile in manifest["tiles"]:
        x,y=tile["column"],tile["row"]
        if not 0 <= x < 3 or not 0 <= y < 3 or (x,y) in seen:
            raise ValueError("Duplicate or out-of-range tile")
        seen.add((x,y))
        name=f"height_x{x}_y{y}.r16"
        if tile["file"] != name:
            raise ValueError("Unexpected tile filename")
        raw=(source/name).read_bytes()
        if len(raw) != 2*n*n or len(raw) != tile["bytes"] or _sha(raw) != tile["sha256"]:
            raise ValueError("Tile SHA256 or size mismatch: "+name)
        files[(x,y)]=raw
    if len(files) != 9:
        raise ValueError("Expected exactly 9 tiles")
    for y in range(3):
        for x in range(3):
            here=files[x,y]
            if x < 2:
                right=files[x+1,y]
                for row in range(n):
                    if here[2*(row*n+n-1):2*(row*n+n)] != right[2*(row*n):2*(row*n+1)]:
                        raise ValueError("X seam mismatch")
            if y < 2 and here[-n*2:] != files[x,y+1][:n*2]:
                raise ValueError("Y seam mismatch")
    return manifest,files,n


def prepare(source: Path, out: Path) -> dict:
    source=source.expanduser().resolve()
    out=out.expanduser().resolve()
    if out == ROOT or ROOT in out.parents or out == source or source in out.parents:
        raise ValueError("Use a new external output directory, never a source directory")
    if out.exists():
        raise FileExistsError(f"Output already exists: {out}")
    manifest,tiles,n=_load_source(source)
    layout=plan_layout()  # validate proposed locations BEFORE any writing
    out.mkdir(parents=True,exist_ok=False)
    full=3*(n-1)+1
    dest=out/f"SKJAEROYAAS_{full}x{full}.r16"
    digest=hashlib.sha256()
    with dest.open("wb") as f:
        for global_y in range(full):
            ty=min(global_y//(n-1),2)
            local_y=global_y-ty*(n-1)
            row=b"".join(tiles[x,ty][2*(local_y*n):2*(local_y*n+(n-1 if x<2 else n))]
                         for x in range(3))
            if len(row) != full*2:
                raise ValueError("Invalid stitched row size")
            digest.update(row)
            f.write(row)
    layout_file=out/"skjaeroyaas-layout.json"
    layout_file.write_text(json.dumps(layout,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with (out/"villages.csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.writer(f)
        w.writerow(["id","name","type","x_cm","y_cm","z_cm","status"])
        for s in layout["villages"]:
            w.writerow([s["id"],s["name"],s["type"],s["xMeters"]*100,
                        s["yMeters"]*100,round(s["zMeters"]*100),s["status"]])
    with (out/"road-waypoints.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f)
        w.writerow(["from","to","waypoint","x_cm","y_cm","z_cm","status"])
        for edge in layout["roadCandidates"]:
            for idx,p in enumerate(edge["pointsMeters"]):
                w.writerow([edge["from"],edge["to"],idx,p[0]*100,p[1]*100,
                            round(p[2]*100),edge["status"]])
    with (out/"forest-anchors.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f)
        w.writerow(["x_cm","y_cm","z_cm","biome","status"])
        for pt in layout["forestAnchors"]:
            w.writerow([round(pt["xMeters"]*100),round(pt["yMeters"]*100),
                        round(pt["zMeters"]*100),pt["biome"],pt["status"]])
    report={
        "schema":"ANOMALIA-UE5-IMPORT-STAGING-1", "worldId":EXPECTED_WORLD,
        "worldName":"SKJÆRØYÅS","dimensionsKm":[15,15],"areaKm2":225,
        "sourceManifestSHA256":_sha((source/"terrain-manifest.json").read_bytes()),
        "stitchedR16":dest.name,"resolution":[full,full],
        "heightmapBytes":dest.stat().st_size,"heightmapSHA256":digest.hexdigest(),
        "landscape": {
            "sectionsPerComponent":[2,2], "quadsPerSection":63,
            "componentsXY":[(full-1)//126,(full-1)//126],
            "scaleCm":{"x":round(500000/(n-1),8),
                       "y":round(500000/(n-1),8),"z":800},
            "recommendedLocationCm":[-750000,-750000,0],
            "note":"Verify row0 orientation, terrain bounds and level placement in UE",
        },
        "villageMarkers":len(layout["villages"]),
        "forestAnchorCandidates":len(layout["forestAnchors"]),
        "roadCandidates":len(layout["roadCandidates"]),
        "roadsWithLandPaths":sum(bool(r["pointsMeters"]) for r in layout["roadCandidates"]),
        "isNativeUnrealLevel":False,"hasLandscapeActor":False,
        "hasPCGMeshes":False,"hasRoadSplines":False,"hasBuildings":False,
        "files":["skjaeroyaas-layout.json","villages.csv","road-waypoints.csv",
                 "forest-anchors.csv",dest.name],
    }
    (out/"ue5-import-manifest.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report


def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tiles",required=True,type=Path)
    ap.add_argument("--output",required=True,type=Path)
    a=ap.parse_args()
    print(json.dumps(prepare(a.tiles,a.output),ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
