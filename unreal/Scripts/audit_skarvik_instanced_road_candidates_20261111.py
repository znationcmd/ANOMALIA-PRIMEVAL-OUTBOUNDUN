"""Read-only survey of existing SKARVIK road actors by native 128m cells.

Never deletes or modifies existing road assets; does NOT assert that all road
actors can be instanced. Descriptor labels alone cannot verify per-instance
materials, collisions, mobility, data layers or road interaction scripts.
The output is a *geographical upper-bound grouping hypothesis*, not a native
conversion or a cooked build-size forecast.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import json
import math
import os
from pathlib import Path
import traceback

REPORT_PATH=Path(os.environ["SKARVIK_ROAD_INSTANCING_READONLY_REPORT"]).resolve()
ROOT_NAME="ANOMALIAZ_SKARVIK_STAGE_41188816555"
LEVEL="/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1"
CELL_CM=12800
MAX_PIECES_PER_ACTOR=256
PREFIXES=(
 "SKARVIK_FINAL_DRY_OLD_REAL_ASPHALT_",
 "SKARVIK_FINAL_SAFE_TOWN_ACCESS_B1_",
 "SKARVIK_FINAL_SAFE_TOWN_ACCESS_B2_",
 "SKARVIK_FINAL_SAFE_TOWN_ACCESS_B3_",
 "SKARVIK_FINAL_REGIONAL_DRY_NATIVE_PILOT_",
)
report={
 "state":"ERROR","world":"SKARVIK","map":LEVEL,
 "mode":"READ_ONLY_NO_MIGRATION_NO_NATIVE_WRITES",
 "nativeMapSaved":False,"newActorsSpawned":0,"originalActorsDeleted":0,
 "originalActorsEligibleForAutomaticDeletion":False,
 "migrationSafeWithoutMaterialCollisionAudit":False,
 "isRealCookedGameSizeKnown":False,"sourceRouteActorCount":0,
}
try:
    import unreal
    root=Path(unreal.Paths.project_dir()).resolve()
    marker=root/".skarvik-ci-stage-marker"
    if ROOT_NAME not in str(root).upper() or not marker.is_file() or \
       marker.read_text(encoding="utf-8-sig").strip()!="41188816555":
        raise RuntimeError("Not trusted Windows staging project")
    originals=(
       root/"Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap",
       root/"Content/Maps/PRIGIMALIA_SKARVIK_ISLANDS_v1.umap",
       root/"Content/Map/Big_City_LVL.umap",
       Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap"),
    )
    before={str(x):(x.stat().st_size,x.stat().st_mtime_ns) for x in originals}
    level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level.load_level(LEVEL):
        raise RuntimeError("Cannot load original native SKARVIK level")
    desc=unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or []
    if len(desc)<9000:
        raise RuntimeError("Native partition descriptors unexpectedly missing")
    source=Counter()
    cell_count=Counter()
    invalid_bounds=[]
    for actor in desc:
        label=str(actor.label)
        prefix=next((p for p in PREFIXES if label.startswith(p)),None)
        if prefix is None:continue
        source[prefix]+=1
        bounds=actor.bounds
        center=((bounds.min.x+bounds.max.x)/2,(bounds.min.y+bounds.max.y)/2)
        if not all(math.isfinite(float(v)) for v in center):
            invalid_bounds.append(label)
            continue
        key=(prefix,math.floor(center[0]/CELL_CM),math.floor(center[1]/CELL_CM))
        cell_count[key]+=1
    if invalid_bounds:raise RuntimeError("Non-finite actor positions: "+str(invalid_bounds[:3]))
    total=sum(source.values())
    if total<9000:raise RuntimeError(f"Too few saved 3D road actors ({total})")
    estimate=sum(math.ceil(n/MAX_PIECES_PER_ACTOR) for n in cell_count.values())
    # Same mesh and material overrides have NOT been validated for each actor.
    # Grouping by historical prefix and spatial cell is a plausible upper
    # optimization *opportunity*, not a guaranteed resulting actor count.
    report.update({
      "state":"NATIVE_ROAD_GROUPING_GEOGRAPHIC_AUDIT_ONLY",
      "worldPartitionDescriptors":len(desc),
      "sourceRouteActorCount":total,
      "sourceRoadsByLabelPrefix":dict(source),
      "streamingCellSizeMeters":CELL_CM/100.,
      "hypotheticalClustersIfCompatible":estimate,
      "potentialActorCountReductionIfCompatible":total-estimate,
      "potentialActorReductionPercentIfCompatible":round(100*(1-estimate/total),2),
      "distinctCellAndPrefixGroups":len(cell_count),
      "materialAndCollisionCompatibilityVerified":False,
      "renderingAndDrivingPIEValidated":False,
      "originalAssetsChanged":False,
      "sourceLevelMetadataUnchanged":True,
    })
    after={str(x):(x.stat().st_size,x.stat().st_mtime_ns) for x in originals}
    if after!=before:raise RuntimeError("Unexpected native source level change")
except Exception:
    report["error"]=traceback.format_exc()[-3500:]
finally:
    REPORT_PATH.parent.mkdir(parents=True,exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",
                           encoding="utf-8")
    try:
        import unreal
        unreal.log("SKARVIK_ROAD_INSTANCING_AUDIT="+report["state"])
    except Exception:
        pass
