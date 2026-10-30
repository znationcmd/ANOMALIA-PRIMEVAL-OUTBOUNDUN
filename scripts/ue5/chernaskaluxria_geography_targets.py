"""Canonical CHERNASKALUXRIA geographical area budget, not an authored Unreal map.

The ninth WORLD is a single 100 x 100 km level. The main CONTINENT is 5000 km2.
Twenty distinct offshore islands occupy 1750 km2. Sea is 3250 km2.
These are DESIGN TARGETS. Procedural and native UE measured areas MUST be
compared to these numbers before anyone claims the target is achieved.
"""
from __future__ import annotations

WORLD_ID="chernaskaluxria-v1"
WORLD_PACKAGE="/Game/Maps/PRIGIMALIA_CHERNASKALUXRIA"
WORLD_AREA_KM2=10_000
MAINLAND_TARGET_KM2=5_000
SEA_TARGET_KM2=3_250
SATELLITES_TARGET_KM2=1_750
MAINLAND_COUNT=1
# Distinct names and original narrative hooks; none is an existing DayZ island.
# Offshore centres, coastal collision-free outlines and marine access have
# deliberately NOT been approved / generated for this full list yet.
SATELLITE_TARGETS=(
    # Three major island destinations, each 200 square kilometres.
    ("elyndra",200,"paradise-islands","coral coves, shipwreck caves, tropical research island"),
    ("karvex",200,"devastated-exclusion","collapsed research colony and radioactive quarantine"),
    ("vorak",200,"arid-highlands","desert fortified settlements and canyon reservoirs"),
    # Six medium islands, each 100 square kilometres.
    ("skelvar",100,"northern-alpine","mountain observatory and an abandoned cable route"),
    ("horvak",100,"polar-volcanic","geothermal bunker and ash glacier"),
    ("telyra",100,"tropical-rainforest","forgotten scientific camp and ancient tunnels"),
    ("draem",100,"farming-lowlands","farming communities and a historic fortress"),
    ("senvra",100,"coastal-ports","shipyard, commercial docks and boat repair shops"),
    ("calmora",100,"paradise-islands","island hospital and hidden coastal laboratories"),
    # Eleven smaller islands, each 50 square kilometres.
    ("vasdun",50,"arid-highlands","isolated desert fort and precious salvage"),
    ("marona",50,"coastal-ports","smugglers' docks and repair supplies"),
    ("frosh",50,"northern-alpine","radio station and cold-weather caches"),
    ("nelyn",50,"paradise-islands","underwater reef entrance and hidden camp"),
    ("velk",50,"polar-volcanic","polar emergency shelter"),
    ("naxor",50,"devastated-exclusion","hazardous military crash site"),
    ("dolran",50,"farming-lowlands","fortified rural settlement"),
    ("zarvik",50,"tropical-rainforest","river delta and cave waterfall"),
    ("orven",50,"coastal-ports","coastguard station and refuelling"),
    ("rask",50,"arid-highlands","desert mine and deep aquifer"),
    ("lumira",50,"paradise-islands","remote resort with flooded underground facility"),
)

def plan() -> dict:
    islands=[
        {"id":name,"targetKm2":area,"biome":biome,"explorationHook":hook,
         "status":"PLANNED_NOT_TOPOGRAPHICALLY_VERIFIED",
         "separatedByNavigableWater":False,
         "boatRouteTested":False,"bridgeOrTunnelBuilt":False}
        for name,area,biome,hook in SATELLITE_TARGETS
    ]
    classes={area:sum(item["targetKm2"]==area for item in islands)
             for area in (200,100,50)}
    assert len(islands)==20
    assert classes=={200:3,100:6,50:11}
    assert sum(x["targetKm2"] for x in islands)==SATELLITES_TARGET_KM2
    assert MAINLAND_TARGET_KM2+SATELLITES_TARGET_KM2+SEA_TARGET_KM2==WORLD_AREA_KM2
    assert len({x["id"] for x in islands})==20
    return {
        "schemaVersion":1,"mapId":WORLD_ID,"unrealPackage":WORLD_PACKAGE,
        "worldSizeKm":[100,100],"worldAreaKm2":WORLD_AREA_KM2,
        "mainlandTargetKm2":MAINLAND_TARGET_KM2,"mainlandCount":1,
        "satelliteIslandsTargetKm2":SATELLITES_TARGET_KM2,
        "seaTargetKm2":SEA_TARGET_KM2,
        "landTargetKm2":MAINLAND_TARGET_KM2+SATELLITES_TARGET_KM2,
        "targetAreaPercent":{"mainland":50,"islands":17.5,"sea":32.5},
        "islandCountsByAreaKm2":classes,"islandCount":len(islands),
        "plannedIslands":islands,
        "worldPartitionStillOneMap":True,
        "physicalHeightmapMatchesBudget":False,
        "nativeUmapMatchesBudget":False,
        "seaNavigationPlaytested":False,
        "seaLevelMeters":0,
        "authoringStatus":"TARGET_ONLY_PENDING_REVISED_TERRAIN_GENERATION",
        "notes":"Do not confuse world area (10000), mainland land (5000), all land (6750) or sea (3250)."
    }

if __name__=="__main__":
    import json
    print(json.dumps(plan(),indent=2,ensure_ascii=False))
