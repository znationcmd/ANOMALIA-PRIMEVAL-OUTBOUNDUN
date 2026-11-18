"""Regression tests: deterministic authored-intent world plans, no fake completion claims."""
import json,math,runpy
from pathlib import Path
p=runpy.run_path(str(Path(__file__).resolve().parents[1]/"scripts/world_auto_construct/plan_all_30.py"))
catalog=json.loads((Path(__file__).resolve().parents[1]/"public/config/anomalia-map-catalog.json").read_text(encoding="utf-8"))
a=p["build_catalog_plan"](catalog)
b=p["build_catalog_plan"](catalog)
assert a==b
assert a["levelCount"]==30 and len(a["maps"])==30
assert len({m["id"] for m in a["maps"]})==30
assert len({m["worldPackage"] for m in a["maps"]})==30
assert all(m["worldPackage"].startswith("/Game/Maps/") for m in a["maps"])
assert a["savedRoadActors"]==0 and a["savedBuildingActors"]==0
assert a["plannedLocalitiesTotal"]>=1000
for m in a["maps"]:
    w,h=m["worldSizeMeters"]
    assert 7000<=w<=105000 and 7000<=h<=105000,(m["id"],w,h)
    assert m["proposedLocalities"]==len(m["sites"])
    ids={s["id"] for s in m["sites"]}
    assert len(ids)==len(m["sites"])
    assert not m["authoredInUnreal"] and not m["terrainCollisionVerified"]
    for s in m["sites"]:
        assert abs(s["eastMeters"])<w*.47 and abs(s["northMeters"])<h*.47
        assert s["buildingTarget"]>=2 and not s["physicallyPlaced"]
        assert 1<=len(s["meshPalette"])<=12
        assert set(s["meshPalette"])<=set(a["reusesOriginalMeshes"])
    for r in m["regionalRoadGraph"]:
        assert r["from"] in ids and r["to"] in ids
        assert not r["asphaltPhysicallyBuilt"] and not r["navigableInVehicle"]
        assert r["distanceStraightMetres"]>=0
    if len(ids)>=2: assert len(m["regionalRoadGraph"])>=len(ids)-1
assert next(m for m in a["maps"] if m["id"]=="chernaskaluxria-v1")["requestedLocalities"]==475
assert next(m for m in a["maps"] if m["id"]=="archipelago-v2")["requestedLocalities"]==125
assert next(m for m in a["maps"] if m["id"]=="deadroot-v1")["requestedLocalities"]==0
assert next(m for m in a["maps"] if m["id"]=="falc-v1")["worldSizeMeters"]==[32000.,22000.]
assert next(m for m in a["maps"] if m["id"]=="nasdaras-v1")["worldSizeMeters"]==[18000.,26000.]
maps_by_id = {world["id"]: world for world in a["maps"]}
expected_regional_palettes = {
    "moscovie-v1": "urban",
    "corsivia-v1": "mediterranean",
    "mokupunawai-v1": "tropical",
    "kiryumori-v1": "temperate",
    "aranyapura-v1": "tropical",
    "nasdaras-v1": "arid",
    "yudinavia-v1": "nordic",
}
for world_id, expected_palette in expected_regional_palettes.items():
    world = maps_by_id[world_id]
    assert world["biomeConstructionPalette"] == expected_palette, world_id
    assert not world["architectureThemeVerified"], world_id
print("ANOMALIA_30_AUTO_BUILDER_MASTER_PLAN_TESTS_PASS localities={} links={}".format(
    a["plannedLocalitiesTotal"],a["plannedRegionalLinksTotal"]))
