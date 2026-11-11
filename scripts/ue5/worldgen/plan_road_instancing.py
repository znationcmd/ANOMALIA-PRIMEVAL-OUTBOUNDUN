"""Plan reusable road mesh clusters without touching Unreal levels.

InstancedStaticMesh (ISM) / HierarchicalInstancedStaticMesh (HISM) repeats the
SAME UStaticMesh using per-instance transforms; it does not duplicate geometry.
Plan by 128m streaming cells, exact mesh + material/collision/data layer, and
a cap of 256 instances per actor. Never merge unlike meshes, materials, collision
profiles, or streaming settings.

A planning JSON is ONLY a preview. It cannot prove cooked download size or
verify road seams/physics. Validate in UE 5.8 on a separate staging map before
any original AStaticMeshActors are removed. No deleting anywhere in this tool.

Usage:
 python scripts/ue5/worldgen/plan_road_instancing.py \
   --input existing-road-inventory.json --output new-road-plan.json
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path

CELL_CM = 12800  # 128 m partition: maintain local distance streaming, not one global HISM
MAX_INSTANCES = 256
SUPPORTED = {"StaticMeshActor", "AStaticMeshActor"}


def _finite_num(x):
    return isinstance(x, (int,float)) and not isinstance(x,bool) and math.isfinite(x)


def validate(rec):
    if not isinstance(rec,dict) or rec.get("class") not in SUPPORTED:
        raise ValueError("Only static mesh road actors are eligible for a proposed cluster")
    coords=rec.get("centerCm")
    if not isinstance(coords,list) or len(coords)!=3 or not all(_finite_num(x) for x in coords):
        raise ValueError("Invalid actor position")
    if not isinstance(rec.get("id"),str) or not rec["id"]:
        raise ValueError("Missing unique actor identifier")
    # Source scan may know mesh path but NOT material overrides, collisions,
    # mobility, actor dependencies or Data Layer membership. Do NOT guess.
    for key in ("mesh","materialSignature","collisionProfile","runtimeGrid","dataLayer"):
        if not isinstance(rec.get(key),str) or not rec[key]:
            raise ValueError(f"Unverified cluster compatibility: {key}")
    if rec.get("mobility")!="Static" or rec.get("spatiallyLoaded") is not True:
        raise ValueError("Dynamic or always-loaded actor cannot be batched")
    if rec.get("hasGameplayState") is not False:
        raise ValueError("Cannot batch interactive road actors")
    return True


def plan(records):
    grouped=defaultdict(list)
    ids=set()
    for row in records:
        validate(row)
        if row["id"] in ids:raise ValueError("Duplicate road actor identifier")
        ids.add(row["id"])
        x,y,_=row["centerCm"]
        key=(math.floor(x/CELL_CM),math.floor(y/CELL_CM),
             row["mesh"],row["materialSignature"],row["collisionProfile"],
             row["runtimeGrid"],row["dataLayer"])
        grouped[key].append(row)
    clusters=[]
    for key,group in sorted(grouped.items()):
        group.sort(key=lambda r:r["id"])
        for offset in range(0,len(group),MAX_INSTANCES):
            batch=group[offset:offset+MAX_INSTANCES]
            marker=json.dumps([key,offset//MAX_INSTANCES],separators=(",",":"),ensure_ascii=True)
            identity="ANOMALIA_ROAD_CLUSTER_"+hashlib.sha256(marker.encode()).hexdigest()[:20]
            clusters.append({"clusterId":identity,"gridXY":[key[0],key[1]],
                "mesh":key[2],"materialSignature":key[3],"collisionProfile":key[4],
                "runtimeGrid":key[5],"dataLayer":key[6],
                "instanceCount":len(batch),
                "sourceActorIds":[r["id"] for r in batch]})
    assert sum(g["instanceCount"] for g in clusters)==len(records)
    return {"status":"SOURCE_ONLY_NOT_MIGRATED","sourceActors":len(records),
        "targetClusterActors":len(clusters),
        "potentialActorReduction":len(records)-len(clusters),
        "potentialActorReductionPercent":round(100*(1-len(clusters)/len(records)),2) if records else 0.,
        "cellSizeCm":CELL_CM,"maxInstancesPerCluster":MAX_INSTANCES,
        "sourceMapUnmodified":True,"runtimeStreamingUntested":True,
        "collisionContinuityUntested":True,"cookedPackageSizeNotMeasured":True,
        "canDeleteOriginalRoadActors":False,"clusters":clusters}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    if args.output.exists():raise FileExistsError("Never overwrite previous audit")
    if args.input.resolve()==args.output.resolve():raise ValueError("Cannot write over source")
    doc=json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(doc,list):raise ValueError("Expected JSON array of verified road actors")
    result=plan(doc)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({key:value for key,value in result.items() if key!="clusters"}))


if __name__=="__main__":
    main()
