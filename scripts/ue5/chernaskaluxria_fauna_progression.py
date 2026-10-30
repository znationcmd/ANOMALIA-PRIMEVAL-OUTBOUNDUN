"""CHERNASKALUXRIA-only original fauna/ecology progression and spawn contracts.

This is data-driven SOURCE PLANNING, not functioning UE creature/AI spawning.
No species asset, AI class, animation, taming/mount, water creature locomotion,
or naval collision is certified installed. Server must validate all of those
before activating encounters. Other eight maps are not modified.

Future native integration: authoritative wildlife subsystem reads biome and
terrain/water queries from UE World Partition; applies route/safe-zone spatial
registries; validates actual creature pawn/AI classes; streams/deduplicates
encounters with hard population budgets, despawn, persistence and anti-grief.
"""
from __future__ import annotations

import hashlib
from collections import Counter
from typing import Optional

from chernaskaluxria_geography_targets import SATELLITE_TARGETS, WORLD_ID, WORLD_PACKAGE

MAX_ACTIVE_AI_PER_PLAYER=10
MAX_ACTIVE_AI_PER_CELL=5
MAX_ACTIVE_AI_PER_SERVER=150
MAX_ACTIVE_WATER_PREDATORS_PER_REGION=2
STARTER_SAFE_RADIUS_M=1600
MIN_TREX_DISTANCE_FROM_STARTER_M=3500
MIN_TREX_DISTANCE_FROM_SETTLEMENT_M=2500
NEARBY_LOAD_RADIUS_M=700
ROUTE_SAFE_BUFFER_M=550
ISLAND_CLASS_COUNTS={200:3,100:6,50:11}
ZONE_TYPES=("metropolis","rural","wilderness","desert","ruined","jungle","snow",
            "coast","channel","deep_sea","small_island")
SEA_THREAT_THRESHOLDS={
    "megalodon":{"minDepthMetres":16,"minShoreDistanceMetres":450,
                 "minDistanceFromSafeRouteMetres":ROUTE_SAFE_BUFFER_M,
                 "maxGroup":1,"tier":3},
    "mosasaur":{"minDepthMetres":55,"minShoreDistanceMetres":1300,
                "minDistanceFromSafeRouteMetres":1500,
                "maxGroup":1,"tier":5},
}
CREATURES={
    "zombie":{"type":"mutated_infected","mobility":"ground","tier":1,"reward":"basic_medical_and_scrap"},
    "raptor":{"type":"raptor","mobility":"ground","tier":2,"reward":"hide_claws"},
    "carnotaurus":{"type":"carnotaurus","mobility":"ground","tier":3,"reward":"rare_predator_resources"},
    "trex":{"type":"tyrannosaurus","mobility":"ground","tier":5,"reward":"boss_predator_trophy"},
    "megalodon":{"type":"megalodon","mobility":"water","tier":3,"reward":"marine_salvage"},
    "mosasaur":{"type":"mosasaurus","mobility":"water","tier":5,"reward":"deep_sea_rare_materials"},
    "pteranodon":{"type":"pteranodon","mobility":"flying","tier":2,"reward":"nest_materials"},
    "genetic_anomaly":{"type":"original_genetic_anomaly","mobility":"ground","tier":5,"reward":"research_unlock"},
}
# Each planned island has a point of interest, but not every island spawns a
# flyer or endgame creature. Travel and progression have distinctive rewards.
ISLAND_FAUNA={
    "elyndra":("raptor",),
    "karvex":("genetic_anomaly","carnotaurus"),
    "vorak":("carnotaurus",),
    "skelvar":("raptor",),
    "horvak":("genetic_anomaly",),
    "telyra":("raptor","carnotaurus"),
    "draem":("raptor",),
    "senvra":("zombie",),
    "calmora":("zombie",),
    "vasdun":("carnotaurus",),
    "marona":("zombie",),
    "frosh":("pteranodon",),
    "nelyn":("pteranodon",),
    "velk":("pteranodon",),
    "naxor":("genetic_anomaly",),
    "dolran":("raptor",),
    "zarvik":("pteranodon",),
    "orven":("zombie",),
    "rask":("genetic_anomaly",),
    "lumira":("pteranodon","genetic_anomaly"),
}
ISLANDS={name:{"sizeKm2":km2,"biome":biome,"exploration":hook,"fauna":ISLAND_FAUNA[name]}
         for name,km2,biome,hook in SATELLITE_TARGETS}
# Conceptual safe routes, NOT real surveyed geometries or navigable splines.
SAFE_MARINE_ROUTE_RULES={
    "startingFerriesRequireSafeHarbours":True,
    "passageMustHaveAnAssetBackedRouteSpline":True,
    "suppressionBufferMetres":ROUTE_SAFE_BUFFER_M,
    "noUnderwaterAIPatrolNearPlayerStartingHarbours":True,
    "protectedPassageMayBeDisabledAfterWorldEvent":False,
    "surveyedRoutesExist":False,
}

def _stable_roll(cell_id:str,salt:str) -> float:
    raw=hashlib.sha256(f"{WORLD_ID}|fauna|{cell_id}|{salt}".encode()).digest()
    return int.from_bytes(raw[:8],"big")/(2**64)

def _make_candidate(species:str,count:int,why:str) -> dict:
    kind=CREATURES[species]
    return {
      "speciesId":species,"wildlifeType":kind["type"],"movement":kind["mobility"],
      "count":count,"tier":kind["tier"],"rewardHook":kind["reward"],
      "spawnReason":why,"serverAuthoritativeRequired":True,
      "requiresVerifiedOwnedOrLicensedCreatureAssets":True,
      "requiresNativeAIControllerNavigationAndReplication":True,
      "actualActorSpawningEnabled":False,
      "tamingAndMountRidingVerified":False,
    }

def population_plan(*,cell_id:str,zone:str,biome:str,
                    island_id:Optional[str]=None,
                    geography_verified:bool=False,
                    water_depth_m:Optional[float]=None,
                    shore_distance_m:Optional[float]=None,
                    safe_route_distance_m:Optional[float]=None,
                    distance_from_start_m:float=0,
                    distance_from_settlement_m:float=0,
                    player_distance_m:float=10000,
                    active_ai_near_player:int=0,
                    active_ai_in_cell:int=0,
                    active_ai_on_server:int=0,
                    active_water_predators_in_region:int=0) -> dict:
    """Deterministic ecology candidate for ONE loaded cell.

    All untrusted values are bounded. No gameplay-side spawn or active creature
    claims are made. Water depth/distance and island topology MUST be verified
    from the real collision/water system before the rules become usable.
    """
    if not cell_id or len(cell_id)>128:raise ValueError("Invalid cell identity")
    if zone not in ZONE_TYPES:raise ValueError("Unknown zone")
    if island_id is not None and island_id not in ISLANDS:raise ValueError("Unknown island")
    if island_id and zone!="small_island":raise ValueError("An island must use small_island zone routing")
    if zone=="small_island" and island_id is None:raise ValueError("Island ID required")
    if biome not in {"central-metropolis","farming-lowlands","northern-alpine",
                      "polar-volcanic","arid-highlands","devastated-exclusion",
                      "tropical-rainforest","paradise-islands","coastal-ports"}:
        raise ValueError("Invalid biome")
    distances=[distance_from_start_m,distance_from_settlement_m,player_distance_m]
    if any(not 0<=x<=100000 for x in distances):raise ValueError("Invalid player or settlement distance")
    if any(not 0<=n<=MAX_ACTIVE_AI_PER_SERVER for n in
           (active_ai_near_player,active_ai_in_cell,active_ai_on_server,active_water_predators_in_region)):
        raise ValueError("Invalid AI budget counter")
    ocean=zone in ("channel","deep_sea")
    if ocean:
        if any(v is None or not 0<=v<=100000
               for v in (water_depth_m,shore_distance_m,safe_route_distance_m)):
            raise ValueError("Verified water depth/shore/safe lane distances required")
        if island_id is not None:raise ValueError("Sea encounters do not belong to an island")
    active_radius=player_distance_m<=NEARBY_LOAD_RADIUS_M
    starter_safe=distance_from_start_m<STARTER_SAFE_RADIUS_M
    low_budget=(active_ai_near_player>=MAX_ACTIVE_AI_PER_PLAYER or
                active_ai_in_cell>=MAX_ACTIVE_AI_PER_CELL or
                active_ai_on_server>=MAX_ACTIVE_AI_PER_SERVER)
    candidates=[]
    if geography_verified and active_radius and not starter_safe and not low_budget:
        possible=[]
        if island_id:
            possible=list(ISLANDS[island_id]["fauna"])
            if (biome!=ISLANDS[island_id]["biome"]):
                raise ValueError("Biome must match verified island identity")
        elif ocean:
            if active_water_predators_in_region<MAX_ACTIVE_WATER_PREDATORS_PER_REGION:
                possible=["mosasaur","megalodon"] if zone=="deep_sea" else ["megalodon"]
        elif zone=="metropolis":
            possible=["zombie"]
        elif zone in ("rural","wilderness","jungle"):
            possible=["raptor","carnotaurus"] if zone!="rural" else ["raptor"]
            if zone=="wilderness":possible.append("trex")
        elif zone in ("desert","ruined","snow"):
            possible=["carnotaurus","raptor"] if zone!="snow" else ["raptor"]
            if zone=="ruined":possible.append("genetic_anomaly")
        # Not every region has a required horde. Deterministic sparse selection.
        for species in possible:
            if len(candidates)>=1:break  # one group per cell per tick
            if species=="trex" and (distance_from_start_m<MIN_TREX_DISTANCE_FROM_STARTER_M or
                distance_from_settlement_m<MIN_TREX_DISTANCE_FROM_SETTLEMENT_M):
                continue
            if species in SEA_THREAT_THRESHOLDS:
                condition=SEA_THREAT_THRESHOLDS[species]
                if (water_depth_m<condition["minDepthMetres"] or
                    shore_distance_m<condition["minShoreDistanceMetres"] or
                    safe_route_distance_m<condition["minDistanceFromSafeRouteMetres"]):
                    continue
            if species in ("genetic_anomaly","pteranodon") and island_id is None and zone!="ruined":
                continue
            chance={"zombie":.35,"raptor":.12,"carnotaurus":.05,"trex":.007,
                    "megalodon":.08,"mosasaur":.012,"pteranodon":.07,
                    "genetic_anomaly":.016}[species]
            if _stable_roll(cell_id,species)<chance:
                count=5 if species=="zombie" else 1
                if (active_ai_in_cell+count>MAX_ACTIVE_AI_PER_CELL or
                    active_ai_near_player+count>MAX_ACTIVE_AI_PER_PLAYER or
                    active_ai_on_server+count>MAX_ACTIVE_AI_PER_SERVER):
                    continue
                candidates.append(_make_candidate(species,count,"biome_and_verified_geography"))
    return {
      "mapId":WORLD_ID,"cellId":cell_id,"zone":zone,"biome":biome,
      "islandId":island_id,"geographyVerified":geography_verified,
      "nearActivePlayer":active_radius,"starterProtected":starter_safe,
      "maxActiveAIInCell":MAX_ACTIVE_AI_PER_CELL,
      "maxActiveAINearPlayer":MAX_ACTIVE_AI_PER_PLAYER,
      "maxActiveAIOnServer":MAX_ACTIVE_AI_PER_SERVER,
      "maxActiveWaterPredatorsPerRegion":MAX_ACTIVE_WATER_PREDATORS_PER_REGION,
      "candidateEncounters":candidates,
      "activatedInUnreal":False,
      "assetsAndAIControllersVerified":False,
      "worldPartitionRuntimeValidated":False,
    }

def biome_progression() -> list[dict]:
    return [
      {"tier":1,"region":"starter_near_city_and_villages",
       "threats":["zombie"],"travel":"foot_then_quad_or_moto",
       "safety":"protected_starter_radius"},
      {"tier":2,"region":"mainland_fields_and_rainforest",
       "threats":["raptor"],"travel":"quad_buggy_vehicle",
       "safety":"open_roads_and_visible_patrols"},
      {"tier":3,"region":"remote_mainland_and_offshore_strata",
       "threats":["carnotaurus","megalodon"],"travel":"reinforced_vehicles_and_real_boats",
       "safety":"surveyed_nearshore_routes"},
      {"tier":4,"region":"selected_50km2_island_nests",
       "threats":["pteranodon"],"travel":"watercraft_plus_later_verified_flying_mount",
       "safety":"nest_visibility_and_return_harbours"},
      {"tier":5,"region":"remote_wilderness_deep_sea_secret_labs",
       "threats":["trex","mosasaur","genetic_anomaly"],
       "travel":"protected_expedition_craft",
       "safety":"advanced_gear_and_teamwork"},
    ]

def review_manifest() -> dict:
    return {
      "schemaVersion":1,"mapId":WORLD_ID,"worldPackage":WORLD_PACKAGE,
      "requiresAuthoritativeServer":True,
      "creatureAssetPathsResolved":False,
      "creatureBlueprintClassesResolved":False,
      "navmeshAndWaterAIApproved":False,
      "gameplayIntegrationEnabled":False,
      "nativePlaytestsPassed":False,
      "stageRules":biome_progression(),
      "smallIslandFauna":ISLAND_FAUNA,
      "islandPlanCounts":dict(Counter(x["sizeKm2"] for x in ISLANDS.values())),
      "protectedMarineRouteRules":SAFE_MARINE_ROUTE_RULES,
      "oceanPredatorDepthThresholds":SEA_THREAT_THRESHOLDS,
      "maxConcurrentAI":{"perCell":MAX_ACTIVE_AI_PER_CELL,
          "nearPlayer":MAX_ACTIVE_AI_PER_PLAYER,
          "perServer":MAX_ACTIVE_AI_PER_SERVER,
          "waterPredatorsPerRegion":MAX_ACTIVE_WATER_PREDATORS_PER_REGION},
      "sourceOnly":True,
    }

if __name__=="__main__":
    import json
    print(json.dumps(review_manifest(),indent=2,ensure_ascii=False))
