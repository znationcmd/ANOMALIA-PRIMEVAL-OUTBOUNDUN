#!/usr/bin/env python3
"""Deterministic, map-specific 30-world settlement / road master planner.

Creates ONLY plans, never edits .umap or claims roads/houses exist.
All coordinates are east/north metres relative to each original Unreal world.
A separate Unreal Editor authoring phase must verify actual Landscape collision,
dry ground, protected actor footprints, road slopes and authentic 3D meshes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from pathlib import Path

VERSION = "ANOMALIA-AUTO30-ORIGINAL-2026-V1"
# Preserve user-authored big-map and local gameplay intentions rather than
# assigning one uniform urban density to all biomes.
LOCALITY_TARGETS = {
    "archipelago-v2":125,"inhabited-v2":70,"chernaskaluxria-v1":475,
    "kolchiem-origins-v1":35,"solynacalyra-v1":20,"nexavarkhos-v1":18,
    "falc-v1":20,"racconia-varkovia-v1":24,
    "yudinavia-v1":12,"moscovie-v1":28,"corsivia-v1":15,
    "bot-sever-v1":50,"kiryumori-v1":19,"aranyapura-v1":22,
    "konigsbruck-v1":38,"skjaeroyas-v1":10,"valhalla-extinction-v1":25,
    "unknown-horror-x-v1":4,
    "deadroot-v1":0, # Preserve deathmatch-only arena: do not replace it with civilian towns.
}
# Native generator dimensions: rectangular maps stay rectangular. UNKNOWN
# HORROR X is provisional in the original native .umap; no invented new size.
DIMENSIONS = {
    "falc-v1":(32000.,22000.),
    "nasdaras-v1":(18000.,26000.),
    "unknown-horror-x-v1":(12000.,12000.),
    "valhalla-extinction-v1":(24000.,24000.),
}
REAL_BUILDING_ASSETS = {
 "wood":"/Game/Anomalia/InteractiveRealismReview_v1/wood_house_enterable/SM_wood_house_enterable",
 "coastal":"/Game/Anomalia/Buildings/Lot1/SM_coastal_house_v1",
 "garage":"/Game/Anomalia/Buildings/Lot1/SM_garage_v1",
 "apartment":"/Game/Anomalia/Buildings/Lot1/SM_hlm_8floors_v1",
 "residence":"/Game/Anomalia/Buildings/Expansion1/SM_residence_4floors",
 "townhouse":"/Game/Anomalia/Buildings/Expansion1/SM_townhouse",
 "hospital":"/Game/Anomalia/Buildings/Expansion1/SM_hospital",
 "police":"/Game/Anomalia/Buildings/Expansion1/SM_police_station",
 "barn":"/Game/Anomalia/Buildings/Expansion1/SM_farm_barn",
 "fire":"/Game/Anomalia/Buildings/Expansion1/SM_fire_station",
}
REAL_ROAD_ASSETS = {
 "main":"/Game/Road/Kit_City_Road/SM_ROAD_19_10_0_0_road",
 "local":"/Game/Road/Kit_City_Road/SM_ROAD_19_5_0_0_road",
}
ARCHETYPES = {
 "city": ("apartment","residence","townhouse","hospital","police","fire","wood"),
 "town": ("residence","townhouse","wood","garage","hospital","police","barn"),
 "village": ("wood","coastal","barn","garage","townhouse"),
}
ARID_TERMS = ("arid","desert","savanna","sahel","dry","sand","dunes")
COLD_TERMS = ("snow","fjord","polar","frozen","scandinavian","nordic","ice","taiga")
TROPICAL_TERMS=("rainforest","tropical","monsoon","bamboo","jungle","coast","island")
def seed_for(s):
    return int.from_bytes(hashlib.sha256((VERSION+"|"+s).encode("utf-8")).digest()[:8],"big")
def dimension(map_spec):
    key=map_spec["id"]
    if key in DIMENSIONS: return DIMENSIONS[key]
    w,h=map_spec.get("widthKm"),map_spec.get("heightKm")
    if w and h and w>0 and h>0: return float(w)*1000,float(h)*1000
    area=map_spec.get("areaKm2")
    if not area or not (10<=float(area)<=20000):
        raise ValueError("No documented map dimensions / area for "+key)
    # Square worlds unless known explicit rectangular dimensions above.
    side=math.sqrt(float(area))*1000.
    return side,side
def density(map_spec):
    key=map_spec["id"]
    if key in LOCALITY_TARGETS: return LOCALITY_TARGETS[key]
    count=map_spec.get("targetLocalities")
    if count is not None: return int(count)
    area=float(map_spec.get("areaKm2") or 150)
    return max(2,min(48,int(math.sqrt(area)*1.15)))
# Regional profiles override broad climate words found in mixed-biome maps.
REGIONAL_PALETTES = {
    "moscovie-v1": "urban",
    "corsivia-v1": "mediterranean",
    "mokupunawai-v1": "tropical",
    "kiryumori-v1": "temperate",
    "aranyapura-v1": "tropical",
}

def biome(map_spec):
    if map_spec["id"] in REGIONAL_PALETTES:
        return REGIONAL_PALETTES[map_spec["id"]]
    s = str(map_spec.get("terrainBiome") or "").lower()
    if any(t in s for t in ARID_TERMS):return "arid"
    if any(t in s for t in COLD_TERMS):return "nordic"
    if any(t in s for t in TROPICAL_TERMS):return "tropical"
    if any(t in s for t in ("ruin","apocalyptic","horror","haunted","outbreak")):return "ruins"
    return "temperate"
def class_sequence(count,kind):
    if count<=0:return []
    city_count = (0 if count<8 else max(1,round(count*.055)))
    town_count = (0 if count<5 else max(1,round(count*.22)))
    if kind=="urban":
        city_count=max(1,round(count*.25))
        town_count=min(count-city_count,max(0,round(count*.55)))
    if kind=="nordic":city_count=min(city_count,max(0,count//18))
    if kind=="arid":town_count=min(town_count,max(1,count//8))
    while city_count+town_count>count:town_count-=1
    return ["city"]*city_count+["town"]*town_count+["village"]*(count-city_count-town_count)
def classify_assets(typ,env):
    choices=list(ARCHETYPES[typ])
    if env=="urban" and typ=="town": choices=["apartment"]+choices
    if env=="mediterranean" and typ=="village": choices=["coastal","townhouse","barn","garage"]
    if env=="nordic": choices=[x for x in choices if x not in ("coastal","apartment")] + ["wood","barn"]
    if env=="arid": choices=[x for x in choices if x!="wood"]+["coastal","townhouse"]
    if env=="ruins":choices=[x for x in choices if x not in ("hospital","fire")]+["garage","townhouse"]
    return choices
def ground_ok(sample,x,y):
    if sample is None:return True
    try:
        z=sample(x,y)
        if z<4. or z>1900. or not math.isfinite(z):return False
        for dx,dy in ((35.,0.),(-35.,0.),(0.,35.),(0.,-35.)):
            zz=sample(x+dx,y+dy)
            if not math.isfinite(zz) or abs(zz-z)>3.:return False
        return True
    except (ValueError,IndexError,OverflowError):return False
def candidates(rng,width,height):
    # Deterministic jittered low-discrepancy-like scatter; no world edges.
    # Keep user towns apart while leaving some nonurban wilderness.
    for idx in range(1,50000):
        x=(rng.random()*.86-.43)*width
        y=(rng.random()*.86-.43)*height
        yield x,y
def site_plan(spec,sampler=None):
    key=spec["id"]
    width,height=dimension(spec)
    count=density(spec)
    environment=biome(spec)
    seed=seed_for(key)
    rng=random.Random(seed)
    classes=class_sequence(count,environment)
    minimum=max(470.,min(3600.,math.sqrt(width*height/max(1,count))*0.35))
    result=[]
    unused=0
    options=candidates(rng,width,height)
    for index,category in enumerate(classes):
        placed=None
        # Large city 8+ km away from next city if practical, else standard spacing.
        spacing=minimum*(1.8 if category=="city" and count>=24 else 1.)
        for _ in range(180):
            x,y=next(options)
            if any((x-p["eastMeters"])**2+(y-p["northMeters"])**2<(spacing if p["kind"]=="city" or category=="city" else minimum)**2
                    for p in result):continue
            if not ground_ok(sampler,x,y):continue
            placed=(round(x,2),round(y,2));break
        if placed is None:
            unused+=1
            continue
        buildings={"city":24,"town":12,"village":5}[category]
        if environment=="nordic":buildings=max(3,round(buildings*.65))
        if environment=="arid":buildings=max(3,round(buildings*.75))
        if environment=="ruins":buildings=max(2,round(buildings*.55))
        result.append({
            "id":f"{key.upper().replace('-','_')}_{category.upper()}_{index+1:04}",
            "kind":category, "eastMeters":placed[0],"northMeters":placed[1],
            "buildingTarget":buildings,"plotSpacingMeters":{"city":65,"town":54,"village":42}[category],
            "meshPalette":classify_assets(category,environment),
            "groundProbedFromNativeHeightmap":sampler is not None,
            "physicallyPlaced":False,"fullInteriorsValidated":False,
        })
    return result,unused,minimum,(width,height),environment,seed
def road_graph(sites):
    # Minimum spanning tree keeps topological route connectivity without claiming
    # paths are drivable. A* / collision validation is required in Unreal later.
    if len(sites)<2:return []
    centers=[(s["eastMeters"],s["northMeters"]) for s in sites]
    in_tree={0};edges=[]
    while len(in_tree)<len(sites):
        best=None
        for i in in_tree:
            a=centers[i]
            for j in range(len(sites)):
                if j in in_tree:continue
                b=centers[j]
                dx,dy=a[0]-b[0],a[1]-b[1]
                dist=dx*dx+dy*dy
                if best is None or dist<best[0]:best=(dist,i,j)
        _,i,j=best
        in_tree.add(j)
        edges.append((i,j))
    seen={tuple(sorted(e)) for e in edges}
    # Add a few redundant links for route alternatives and loops.
    possible=[]
    for i in range(len(sites)):
        lengths=sorted(((math.hypot(centers[i][0]-centers[j][0],centers[i][1]-centers[j][1]),j)
                       for j in range(len(sites)) if i!=j))
        for distance,j in lengths[:3]:
            key=(min(i,j),max(i,j))
            if key not in seen: possible.append((distance,*key))
    for _,i,j in sorted(set(possible))[:min(len(sites)//6,30)]:
        if (i,j) not in seen:edges.append((i,j));seen.add((i,j))
    routes=[]
    for idx,(i,j) in enumerate(edges):
        a,b=sites[i],sites[j]
        routes.append({"id":f"AUTO30_LINK_{idx+1:04}","from":a["id"],"to":b["id"],
            "kind":"regional","distanceStraightMetres":round(math.hypot(a["eastMeters"]-b["eastMeters"],
                                      a["northMeters"]-b["northMeters"]),1),
            "terrainSlopeVerified":False,"asphaltPhysicallyBuilt":False,"navigableInVehicle":False})
    return routes
def make_plan(spec,sampler=None):
    sites,unplaced,spacing,(width,height),environment,seed=site_plan(spec,sampler)
    roads=road_graph(sites)
    return {
        "id":spec["id"],"name":spec["displayName"],
        "worldPackage":spec.get("originalUnrealPackage") or spec.get("plannedUnrealPackage"),
        "worldSizeMeters":[round(width,1),round(height,1)],
        "biomeConstructionPalette":environment,
        "terrainTheme":spec.get("terrainBiome"),
        "architectureThemeVerified":False,
        "seed":seed,"requestedLocalities":density(spec),"proposedLocalities":len(sites),
        "unplacedBecauseNoDryGround":unplaced,"minimumSiteSpacingMeters":round(spacing,1),
        "sites":sites,"regionalRoadGraph":roads,
        "plannedRoadCount":len(roads),"actualStaticMeshBuildingsSaved":0,
        "actualRoadMeshActorsSaved":0,"authoredInUnreal":False,
        "terrainCollisionVerified":False,
        "existingActorCollisionVerified":False,
        "realBuildingInteriorsVerified":False,"fullRoadConnectivityVerified":False,
        "planOnlyNotGameplayComplete":True,
    }
def build_catalog_plan(catalog):
    maps=catalog["maps"]
    if len(maps)!=30 or len({m["id"] for m in maps})!=30:
        raise ValueError("Exactly 30 distinct maps required")
    plans=[make_plan(m) for m in maps]
    if any(not x["worldPackage"] for x in plans):raise ValueError("Unregistered UE map package")
    return {"schemaVersion":1,"generationVersion":VERSION,"seedPolicy":"sha256-per-original-map-id",
        "project":"D:/ANOMALIA/unreal/AnomaliaPrimeval.uproject",
        "levelCount":30,"nativeWorldSourcePreserved":True,
        "reusesOriginalMeshes":REAL_BUILDING_ASSETS,"reusesOriginalRoadMeshes":REAL_ROAD_ASSETS,
        "plannedLocalitiesTotal":sum(x["proposedLocalities"] for x in plans),
        "plannedRegionalLinksTotal":sum(len(x["regionalRoadGraph"]) for x in plans),
        "savedRoadActors":0,"savedBuildingActors":0,
        "rollout":"PLAN_FIRST_SAFE_EDITOR_NATIVE_AUTHORING_AFTER_TERRAIN_COLLISION_CHECK",
        "maps":plans}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--catalog",required=True)
    p.add_argument("--out",required=True)
    args=p.parse_args()
    src=json.loads(Path(args.catalog).read_text(encoding="utf-8-sig"))
    doc=build_catalog_plan(src)
    out=Path(args.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    data=json.dumps(doc,ensure_ascii=False,separators=(",",":"),indent=2)+"\n"
    if out.exists() and out.read_text(encoding="utf-8")!=data:
        raise RuntimeError("Existing map-specific plan differs; refuse overwrite: "+str(out))
    if not out.exists():out.write_text(data,encoding="utf-8")
    print("ANOMALIA_AUTOCONSTRUCT_30_PLAN "+json.dumps({"maps":len(doc["maps"]),"localities":doc["plannedLocalitiesTotal"],
        "roads":doc["plannedRegionalLinksTotal"],"out":str(out),"nativeActorsSaved":0}))
if __name__=="__main__":main()
