"""Deterministic, non-destructive layouts for four *original* PRIGIMALIA worlds.

Pure Python planning only. Elevations come from the project's native C++ height
functions; no assets or saved levels are changed by this module.
Distinct inspiration is limited to general biomes, never DayZ assets/maps.
"""
from __future__ import annotations
import hashlib
import math
from collections import defaultdict

PROFILES = {
 "KARSKOV": dict(side=30000, theme="livonia-rural-woodland", towns=25, lots=8,
                 vegetation_step=160, vegetation_density=.63, rocks=.14,
                 max_altitude=530, grade=.18, residential=("country_house_scan","abandoned_brick_house_scan")),
 "VORGRAD": dict(side=30000, theme="nasdara-takistanplus-arid", towns=23, lots=10,
                 vegetation_step=260, vegetation_density=.13, rocks=.75,
                 max_altitude=600, grade=.19, residential=("abandoned_brick_house_scan","country_house_scan")),
 "NEMORIS": dict(side=20000, theme="lux-tropical-rainforest", towns=15, lots=7,
                 vegetation_step=125, vegetation_density=.84, rocks=.08,
                 max_altitude=240, grade=.16, residential=("country_house_scan","abandoned_brick_house_scan")),
 "DRAKHEIM": dict(side=20000, theme="namalsk-sakhal-polar-volcanic", towns=12, lots=6,
                 vegetation_step=240, vegetation_density=.32, rocks=.69,
                 max_altitude=480, grade=.12, residential=("abandoned_brick_house_scan","country_house_scan")),
}

def chance(key,salt):
    h=hashlib.sha256((str(key)+"|"+salt).encode("utf-8")).digest()
    return int.from_bytes(h[:8],"big")/18446744073709551615

def gradient(height,e,n,baseline=12.):
    h=height(e,n)
    if not math.isfinite(h):raise ValueError("Invalid native terrain elevation")
    return h,math.hypot((height(e+baseline,n)-height(e-baseline,n))/(2*baseline),
                        (height(e,n+baseline)-height(e,n-baseline))/(2*baseline))

def select_sites(name,height):
    cfg=PROFILES[name]
    half=cfg["side"]/2
    gap=cfg["side"]/6
    candidates=[]
    for row in range(1,6):
        for col in range(1,6):
            e=-half+col*gap
            n=-half+row*gap
            key=f"{name}:{row}:{col}"
            e+=(chance(key,"east")-.5)*650
            n+=(chance(key,"north")-.5)*650
            z,g=gradient(height,e,n)
            if z<8 or z>cfg["max_altitude"] or g>cfg["grade"]:continue
            candidates.append(dict(id=f"{name.lower()}_site_{row}_{col}",
                                   east=round(e,2),north=round(n,2),height=round(z,2),
                                   role=("town" if len(candidates)%5==0 else "village"),
                                   zone=cfg["theme"]))
    candidates.sort(key=lambda s: chance(s["id"],"order"))
    return candidates[:cfg["towns"]]

def plan(name,height):
    if name not in PROFILES:raise ValueError("Unknown map name")
    cfg=PROFILES[name];half=cfg["side"]/2
    sites=select_sites(name,height)
    if len(sites)<5:raise RuntimeError("Insufficient native safe settlements for "+name)
    buildings=[];foliage=[];reserved_road_centres=[];rejected=defaultdict(int)
    for town in sites:
        lots=cfg["lots"]
        for iy in range(-lots,lots+1):
            for ix in range(-lots,lots+1):
                # Real corridor reservation: leave 10m wide roads every four lots.
                if ix%4==0 or iy%4==0:continue
                e=town["east"]+ix*42
                n=town["north"]+iy*42
                if abs(e)>half-150 or abs(n)>half-150:continue
                key=town["id"]+f":{ix}:{iy}"
                if chance(key,"occupied") < (.21 if name=="DRAKHEIM" else .12):
                    continue
                h,g=gradient(height,e,n)
                if h<6 or h>cfg["max_altitude"] or g>cfg["grade"]*.65:
                    rejected["unsafe_building"]+=1;continue
                # Sample building corners; no tilted or buried floors.
                corners=[height(e+dx,n+dy) for dx,dy in ((-12,-12),(-12,12),(12,-12),(12,12))]
                if min(corners)<5 or max(corners)-min(corners)>1.75:
                    rejected["foundation_relief"]+=1;continue
                building_kind=cfg["residential"][0 if chance(key,"facade")<(.65 if name=="VORGRAD" else .5) else 1]
                buildings.append(dict(id=key.replace(":","_"),site=town["id"],kind=building_kind,
                                      east=round(e,3),north=round(n,3),height=round(max(corners),3),
                                      yaw=90*(int(chance(key,"yaw")*4)%4),role="residence",
                                      interiorReady=False,gameplayReady=False))
        # Road corridors are planned, not claimed as built or drivable.
        radius=lots*42+42
        for d in range(-lots,lots+1,4):
            if abs(d)>lots:continue
            reserved_road_centres.append(dict(site=town["id"],east=town["east"]+d*42,north=town["north"],length=radius*2,axis="north"))
            reserved_road_centres.append(dict(site=town["id"],east=town["east"],north=town["north"]+d*42,length=radius*2,axis="east"))
    # Deterministic biome-aware candidate density, HISM clustering handled natively.
    step=cfg["vegetation_step"]
    for iy in range(int(-half+step/2),int(half),step):
        for ix in range(int(-half+step/2),int(half),step):
            key=f"{name}:flora:{ix}:{iy}"
            if chance(key,"density")>cfg["vegetation_density"]:continue
            e=ix+(chance(key,"jitter-e")-.5)*step*.65
            n=iy+(chance(key,"jitter-n")-.5)*step*.65
            if any(abs(e-s["east"])<cfg["lots"]*42+95 and
                   abs(n-s["north"])<cfg["lots"]*42+95 for s in sites):
                continue
            h,g=gradient(height,e,n)
            if h<4 or h>cfg["max_altitude"]+250 or g>cfg["grade"]*2:
                rejected["unsafe_foliage"]+=1;continue
            kind="rock_moss_set_01" if chance(key,"rock")<cfg["rocks"] else "island_tree_02"
            foliage.append(dict(id=key,kind=kind,east=round(e,3),north=round(n,3),
                                height=round(h,3),yaw=round(360*chance(key,"yaw"),2),
                                scale=round(.85+.25*chance(key,"scale"),4)))
    return dict(schemaVersion=1,name=name,package="/Game/Maps/PRIGIMALIA_"+name,
                mapWidthMetres=cfg["side"],mapHeightMetres=cfg["side"],
                inspiration=cfg["theme"],sites=sites,buildings=buildings,
                vegetation=foliage,reservedRoads=reserved_road_centres,
                rejectionCounts=dict(rejected),state="PLACEMENT_PLAN_NOT_AUTHORED",
                terrainModified=False,existingActorsModified=False,
                interiorReady=False,intercityRoadsBuilt=False,
                pbrPhotorealismValidated=False,gameplayTested=False)
