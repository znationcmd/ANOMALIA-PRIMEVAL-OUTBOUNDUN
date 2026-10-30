"""CHERNASKALUXRIA: deterministic, budget-limited world population rules.

Only CHERNASKALUXRIA. Plans spatially streamed props, starter mobility and
SERVER-side hazard/AI *intents*. Never claims meshes, zombies, predators,
flying mounts, PCG graphs, or survival damage are already functional in UE5.
The real landscape material/road mask determines surface_type. No magic
asphalt detection by geographic region or extra copies of other maps.
"""
from __future__ import annotations
import hashlib
import math
from collections import Counter
from dataclasses import dataclass
from typing import Callable

from chernaskaluxria_world import terrain_height, dominant_region, region_weights

CELL_SIZE_M=250
RUNTIME_ASSET_REQUIRED=True
DEFAULT_ACTIVE_RADIUS_M=600
MAX_AI_NEAR_PLAYER=10
MAX_AI_PER_CELL=5
WORLD_ID="chernaskaluxria-v1"
WORLD_PACKAGE="/Game/Maps/PRIGIMALIA_CHERNASKALUXRIA"

BIOME_RULES={
  "central-metropolis": {"surfaceDensity":.16,"maxStatic":34,"maxAIGroups":1,
                          "treeAsset":"licensed_city_tree","surface":"asphalt"},
  "farming-lowlands": {"surfaceDensity":.60,"maxStatic":80,"maxAIGroups":0,
                        "treeAsset":"licensed_european_tree","surface":"soil"},
  "northern-alpine": {"surfaceDensity":.25,"maxStatic":40,"maxAIGroups":0,
                       "treeAsset":"licensed_alpine_conifer","surface":"snow"},
  "polar-volcanic": {"surfaceDensity":.10,"maxStatic":20,"maxAIGroups":0,
                      "treeAsset":"licensed_frozen_conifer","surface":"snow"},
  "arid-highlands": {"surfaceDensity":.035,"maxStatic":8,"maxAIGroups":1,
                      "treeAsset":"licensed_dry_bush","surface":"sand"},
  "devastated-exclusion": {"surfaceDensity":.045,"maxStatic":12,"maxAIGroups":1,
                            "treeAsset":"licensed_deadwood","surface":"ash"},
  "tropical-rainforest": {"surfaceDensity":.84,"maxStatic":110,"maxAIGroups":0,
                           "treeAsset":"licensed_jungle_tree","surface":"soil"},
  "paradise-islands": {"surfaceDensity":.54,"maxStatic":75,"maxAIGroups":0,
                       "treeAsset":"licensed_palm","surface":"sand"},
  "coastal-ports": {"surfaceDensity":.22,"maxStatic":28,"maxAIGroups":0,
                     "treeAsset":"licensed_coastal_tree","surface":"soil"},
}
SURFACES=frozenset({"asphalt","soil","snow","sand","ash","rock","water"})
STARTER_VEHICLES={
    "farming-lowlands":"quad",
    "central-metropolis":"dirt_bike",
    "arid-highlands":"buggy",
    "northern-alpine":"snowmobile",
    "polar-volcanic":"snowmobile",
    "tropical-rainforest":"quad",
    "paradise-islands":"quad",
    "devastated-exclusion":"buggy",
    "coastal-ports":"quad",
}
# Only real currently defined vehicle catalog IDs; flying mounts need a separate
# proven creature/piloting system, not a fake 'pteranodon' vehicle entry.
assert set(STARTER_VEHICLES)==set(BIOME_RULES)

def random01(key: str, salt: str) -> float:
    b=hashlib.sha256(f"{WORLD_ID}|{key}|{salt}".encode()).digest()
    return int.from_bytes(b[:8],"big")/2**64

def cell_indices(east_m: float,north_m: float) -> tuple[int,int]:
    if not -50000 <= east_m < 50000 or not -50000 <= north_m < 50000:
        raise ValueError("Location is outside the ninth map")
    return (math.floor((east_m+50000)/CELL_SIZE_M),
            math.floor((north_m+50000)/CELL_SIZE_M))

def height_and_grade(e: float,n: float,height: Callable[[float,float],float]):
    h=height(e,n)
    slope=math.hypot((height(e+8,n)-height(e-8,n))/16,
                     (height(e,n+8)-height(e,n-8))/16)
    return h,slope

def plan_population_cell(east_m: float,north_m: float,surface_type: str,
                         player_distance_m: float | None=None,
                         actor_assets_verified: bool=False,
                         height: Callable[[float,float],float]=terrain_height) -> dict:
    """One 250m cell per request; never loop through the entire 100km world."""
    if surface_type not in SURFACES:raise ValueError("Surface must come from a material/road mask")
    cx,cy=cell_indices(east_m,north_m)
    e=-50000+(cx+.5)*CELL_SIZE_M
    n=-50000+(cy+.5)*CELL_SIZE_M
    region=dominant_region(e,n)
    profile=BIOME_RULES[region]
    key=f"{cx:03d}-{cy:03d}"
    near=player_distance_m is not None and 0<=player_distance_m<=DEFAULT_ACTIVE_RADIUS_M
    static=[]
    # Licensed actual meshes need to be bound/verified in Editor. Never install
    # placeholder engine blocks pretending to be art.
    for i in range(profile["maxStatic"]):
        if random01(key,f"prob-{i}")>profile["surfaceDensity"]:continue
        offset_x=(random01(key,f"x-{i}")-.5)*(CELL_SIZE_M-24)
        offset_y=(random01(key,f"y-{i}")-.5)*(CELL_SIZE_M-24)
        x,y=e+offset_x,n+offset_y
        z,grade=height_and_grade(x,y,height)
        if z<2 or grade>.47:continue
        if surface_type=="water":continue
        if surface_type=="asphalt":
            # Actual registered road asphalt required, not merely an urban region.
            if region=="central-metropolis":
                kind="licensed_abandoned_vehicle" if i%3==0 else "licensed_street_debris"
            else:continue
        elif region in ("devastated-exclusion","arid-highlands"):
            kind="licensed_ruin_piece" if i%4==0 else profile["treeAsset"]
        else:
            kind=profile["treeAsset"]
        static.append({"id":f"CH-{key}-P{i:03d}","kind":kind,
                       "eastMeters":round(x,2),"northMeters":round(y,2),
                       "groundMeters":round(z,2),"yawDegrees":round(random01(key,f"yaw-{i}")*360,1),
                       "requiresVerifiedLicensedAsset":True,
                       "placeableNow":actor_assets_verified})
    events=[]
    if near and actor_assets_verified and surface_type=="asphalt" and region=="central-metropolis":
        # Exactly five per group, but only a dedicated server with a verified
        # zombie pawn class and its own replication budget may activate it.
        if random01(key,"zombie-group")<.38:
            events.append({"kind":"zombie-group","count":5,
                           "radiusMeters":100,"serverOnly":True,
                           "requiresVerifiedAIClass":True,
                           "activeInUnreal":False})
    if near and region in ("arid-highlands","devastated-exclusion") and surface_type!="water":
        if random01(key,"predator")<.20:
            events.append({"kind":"elite-predator","count":1,
                           "radiusMeters":250,"serverOnly":True,
                           "requiresVerifiedAIClass":True,
                           "activeInUnreal":False})
    radiation=region=="devastated-exclusion" and surface_type!="water"
    return {"worldId":WORLD_ID,"cellId":f"CH-{key}",
            "cellBoundsMeters":[e-125,n-125,e+125,n+125],
            "region":region,"surface":surface_type,
            "staticCandidates":static,"maxStaticPerCell":profile["maxStatic"],
            "hismExpected":surface_type not in ("asphalt","water"),
            "spawnEvents":events,
            "radiationHazardDesign":radiation,
            "radiationDamageActive":False,
            "radiationWarningAndProtectionNeeded":radiation,
            "fullyAuthoredInUE":False,
            "gameplayTested":False}

def starter_mobility_hubs() -> list[dict]:
    """One *candidate* vehicle per regional starter hub, not an actor spawn."""
    from chernaskaluxria_world import REGIONS
    hubs=[]
    for name,e_km,n_km,_,_ in REGIONS:
        e,n=e_km*1000.,n_km*1000.
        selected=None
        for radius in (0,100,250,450,650,900,1200):
            for angle in range(0,360,30):
                x=e+radius*math.cos(math.radians(angle))
                y=n+radius*math.sin(math.radians(angle))
                if not -49000<x<49000 or not -49000<y<49000:continue
                h,g=height_and_grade(x,y,terrain_height)
                if h>6 and g<.12:
                    selected=(x,y,h);break
            if selected:break
        if selected is None:raise RuntimeError("No verified flat hub candidate in "+name)
        x,y,h=selected
        # World coordinate to UE cm; Unreal north axis is negative Y in map import.
        hubs.append({"id":"starter-"+name,"region":name,"vehicleId":STARTER_VEHICLES[name],
                     "locationMeters":[round(x,2),round(y,2),round(h,2)],
                     "unrealCm":[round(x*100,2),round(-y*100,2),round(h*100+150,2)],
                     "maxMetresFromRegionalSpawn":1200,
                     "earlyAccessGoalMinutes":30,
                     "requiresPhysicalRoadAndVerifiedRig":True,
                     "serverSpawnConfirmed":False,
                     "flyingMountConfirmed":False})
    return hubs

def server_vehicle_template() -> dict:
    hubs=starter_mobility_hubs()
    vehicles=[{"id":h["vehicleId"],"x":h["unrealCm"][0],"y":h["unrealCm"][1],
               "z":h["unrealCm"][2],"yaw":90,
               "fuelPercent":70,"fuelConsumptionPerSecond":.045,
               "speedMultiplier":1.} for h in hubs]
    return {"schemaVersion":1,"mapId":WORLD_ID,"source":"review-only; server vehicles.json must be approved and copied per server",
            "vehicles":vehicles,"hubs":hubs,"activatedOnServer":False}

def coverage_summary() -> dict:
    hubs=starter_mobility_hubs()
    return {"mapId":WORLD_ID,"starterHubs":len(hubs),
            "eligibleVehicles":dict(Counter(h["vehicleId"] for h in hubs)),
            "independentWorld":True,
            "aiServerSpawnActive":False,"pcgGraphAuthored":False,
            "vehiclesPlaced":False,"allBiomes":list(BIOME_RULES)}
