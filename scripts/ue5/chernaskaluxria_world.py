"""CHERNASKALUXRIA — original 100 x 100 km independent world source plan.

One continuous 10,000 km2 world, NOT a merger of eight existing maps.
20x20 planning/import tiles of 5 km each. Real Unreal Landscape .umap,
foliage, roads, server and performance testing are separate native tasks.
"""
from __future__ import annotations
import json
import math
from pathlib import Path
from chernaskaluxria_archipelago import carve_archipelago, apply_satellite_islands, satellite_island_plans, interisland_voyages, crossing_plans
from chernaskaluxria_geography_targets import plan as new_geography_target_plan

MAP_ID = "chernaskaluxria-v1"
DISPLAY_NAME = "CHERNASKALUXRIA"
UNREAL_PACKAGE = "/Game/Maps/PRIGIMALIA_CHERNASKALUXRIA"
SIDE_METRES = 100_000
TILE_SIDE_METRES = 5_000
TILES_PER_AXIS = SIDE_METRES // TILE_SIDE_METRES
SAMPLES_PER_TILE_SIDE = 1009  # 1008 landscape quads / tile, 4.960317m sample interval.
GRID_RESOLUTION = TILES_PER_AXIS * (SAMPLES_PER_TILE_SIDE - 1) + 1
SAVE_NAMESPACE = MAP_ID

# Coordinates (east, north), in kilometres. Zone descriptors are original.
# These determine regional *identity*, not a seam between separate maps.
REGIONS = (
    ("northern-alpine", -23, 33, 20, "snowy mountain ranges, glaciers, tunnels"),
    ("polar-volcanic", 27, 35, 20, "polar coastal mountains and geothermal anomaly"),
    ("arid-highlands", 32, 8, 22, "arid canyon plateaus and desert outposts"),
    ("central-metropolis", 0, 0, 16, "large urban skyline, suburbs, industry"),
    ("farming-lowlands", -23, 11, 21, "villages, farm fields, forest belts"),
    ("devastated-exclusion", 25, -27, 22, "original ruined colony and exclusion zone"),
    ("tropical-rainforest", -9, -27, 24, "tropical jungle, rivers, waterfalls"),
    ("paradise-islands", -36, -34, 20, "tropical island chain and lagoons"),
    ("coastal-ports", -39, -7, 15, "ports, coastal villages, industrial docks"),
)
NAMES = tuple(x[0] for x in REGIONS)


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _smooth(value: float) -> float:
    t = _clamp(value)
    return t * t * (3.0 - 2.0 * t)


def region_weights(east_m: float, north_m: float) -> dict[str, float]:
    """Continuous biome blending: no teleport or hard boundary between regions."""
    if not -50_000 <= east_m <= 50_000 or not -50_000 <= north_m <= 50_000:
        raise ValueError("Coordinates outside CHERNASKALUXRIA")
    raw = {}
    for name, e, n, spread_km, _ in REGIONS:
        radius2 = ((east_m/1000-e)/spread_km)**2 + ((north_m/1000-n)/spread_km)**2
        raw[name] = math.exp(-2.2 * radius2) + 0.000001
    total = sum(raw.values())
    return {k: v / total for k, v in raw.items()}


def dominant_region(east_m: float, north_m: float) -> str:
    return max(region_weights(east_m, north_m), key=region_weights(east_m, north_m).get)


def terrain_height(east_m: float, north_m: float) -> float:
    """Original deterministic height in metres; placeholder for approved terrain art."""
    if not math.isfinite(east_m) or not math.isfinite(north_m):
        raise ValueError("Invalid coordinate")
    if not -50_000 <= east_m <= 50_000 or not -50_000 <= north_m <= 50_000:
        return -250.0
    x, y = east_m, north_m
    w = region_weights(x, y)
    wave = (22 * math.sin(x/4300. + .35*math.sin(y/4900.))
            + 17 * math.cos(y/3600. - x/8800.)
            + 8 * math.sin(x/810. + y/1200.))
    alpine = w["northern-alpine"]*(530 + 410*(.5+.5*math.sin(x/2800.)*math.cos(y/3800.)))
    polar = w["polar-volcanic"]*(340 + 340*(.5+.5*math.cos(x/2100.)))
    desert = w["arid-highlands"]*(180 + 160*(.5+.5*math.sin(y/2400.)))
    rainforest = w["tropical-rainforest"]*110
    disaster = w["devastated-exclusion"]*(140*math.sin((x+y)/3300.)**2)
    city = w["central-metropolis"]
    base = 70 + wave + alpine + polar + desert + rainforest + disaster
    base = base*(1-.88*city) + city*56*.88  # Broad, gently graded city basin.
    # True island waters, not a completely dry square.
    paradise = w["paradise-islands"]
    island = max(
        1.2-math.hypot((x+38000)/5600., (y+33700)/4600.),
        1.2-math.hypot((x+32000)/3100., (y+40500)/3300.),
        1.2-math.hypot((x+43000)/2400., (y+27000)/2600.),
    )
    base = (1-paradise)*base + paradise*(island*115 + 14*wave)
    # Coastal shelf along western edge of the world.
    if x < -45_000:
        coast = _smooth((x+50_000)/5_000)
        base = -70*(1-coast) + base*coast
    return float(apply_satellite_islands(carve_archipelago(base,x,y),x,y))


def world_tiles() -> list[dict]:
    """No map assets are written. 400 independently addressable source tiles."""
    tiles = []
    for row in range(TILES_PER_AXIS):
        for col in range(TILES_PER_AXIS):
            west = -SIDE_METRES//2 + col*TILE_SIDE_METRES
            north = SIDE_METRES//2 - row*TILE_SIDE_METRES
            east = west + TILE_SIDE_METRES
            south = north - TILE_SIDE_METRES
            region = dominant_region((west+east)/2, (north+south)/2)
            tiles.append({
                "tileId": f"CHERNASKALUXRIA_x{col:02d}_y{row:02d}",
                "col": col, "row": row,
                "boundsMetres": {"west": west, "east": east,
                                 "north": north, "south": south},
                "samplesPerAxis": SAMPLES_PER_TILE_SIDE,
                "dominantBiome": region,
                "nativeLandscapeImported": False,
                "buildingPopulationAuthored": False
            })
    return tiles


def world_manifest() -> dict:
    tiles = world_tiles()
    return {
        "schemaVersion": 1,
        "mapId": MAP_ID,
        "displayName": DISPLAY_NAME,
        "unrealPackage": UNREAL_PACKAGE,
        "saveNamespace": SAVE_NAMESPACE,
        "widthKm": 100,
        "heightKm": 100,
        "totalKm2": 10000,
        "landWaterStatus": "PROCEDURAL_ISLAND_DESIGN_NOT_NATIVE_VALIDATED",
        "targetGeography": new_geography_target_plan(),
        "currentTerrainUsesOnlyEightDraftSatellites": True,
        "revisedTwentyIslandHeightfieldGenerated": False,
        "seaLevelMeters": 0,
        "islandGeography": "continuous terrain with meandering marine straits and six planned crossings",
        "bridgesAndTunnelsBuilt": False,
        "satelliteIslands": satellite_island_plans(),
        "plannedMarineVoyages": interisland_voyages(),
        "plannedCrossings": crossing_plans(terrain_height),
        "tileGrid": [TILES_PER_AXIS, TILES_PER_AXIS],
        "tileSideKm": 5,
        "tileSamplesPerAxis": SAMPLES_PER_TILE_SIDE,
        "globalHeightSamplesPerAxis": GRID_RESOLUTION,
        "sampleSpacingMetres": TILE_SIDE_METRES/(SAMPLES_PER_TILE_SIDE-1),
        "tileCount": len(tiles),
        "regions": [{"id": id, "centreKm": [x, y], "radiusKm": radius,
                     "description": description} for id,x,y,radius,description in REGIONS],
        "tiles": tiles,
        "state": "SOURCE_PLAN_ONLY_NOT_A_NATIVE_UMAP",
        "gameplayValidated": False,
        "serverSelectable": False,
        "existingMapsModified": False,
        "notes": "World Partition/tiled Landscape import and PCG population require native UE5 verification."
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(world_manifest(), indent=2, ensure_ascii=False) + "\n"
    if args.output:
        if args.output.exists():
            raise FileExistsError("Refusing to overwrite world design manifest")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as out:
            out.write(result)
    else:
        print(result)
