"""Read-only UE5 native SKARVIK final 48km actor/terrain readiness audit.

Requires UnrealEditor-Cmd.exe on trusted isolated C staging project. Enumerates
World Partition descriptors, does NOT spawn, move, delete, save or overwrite
actors/levels. Produces a report for determining exactly which work remains.
"""
from __future__ import annotations
import collections
import json
import os
from pathlib import Path
import traceback

OUT=Path(os.environ["SKARVIK_NATIVE_FINAL_READINESS_REPORT"]).resolve()
REPORT={"state":"FAILED","readonly":True,
        "finalLevel":"/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1",
        "originalLevelOverwritten":False,"actorsSpawned":0,"actorsDeleted":0,
        "nativePIEPlayed":False,"nativeWindowsPackagedBuildTested":False,
        "all382RegionalRoadsVehicleValidated":False,
        "sourceCitySampleFull4kmLoaded":False,"all125SettlementsGameplayValidated":False}
try:
    import unreal
    project=Path(unreal.Paths.project_dir()).resolve()
    marker=project/".skarvik-ci-stage-marker"
    if ("ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(project).upper() or
        not marker.is_file() or marker.read_text(encoding="utf-8-sig").strip()!="41188816555"):
        raise RuntimeError("Not the original verified isolated UE5 staging")
    paths={
        "nativeFinalLevel":project/"Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap",
        "gradedOriginal":project/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap",
        "sevenOriginalIslands":project/"Content/Maps/PRIGIMALIA_SKARVIK_ISLANDS_v1.umap",
        "originalCitySample":project/"Content/Map/Big_City_LVL.umap",
        "protectedDOriginal":Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap"),
    }
    for name,path in paths.items():
        if not path.is_file():
            raise RuntimeError("Protected native map unavailable: "+name)
    original_meta={k:{"bytes":v.stat().st_size,"mtimeNs":v.stat().st_mtime_ns}
                   for k,v in paths.items()}
    subsystem=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not subsystem.load_level(REPORT["finalLevel"]):
        raise RuntimeError("Unreal cannot load the true final WP world")
    wp=unreal.WorldPartitionBlueprintLibrary
    desc=wp.get_actor_descs() or []
    if len(desc)<1000:
        raise RuntimeError("Final World Partition actor descriptors missing")
    labels=[str(d.label) for d in desc]
    prefixes=(
        "SKARVIK_FINAL_DRY_OLD_REAL_ASPHALT_",
        "SKARVIK_FINAL_SAFE_TOWN_ACCESS_B1_",
        "SKARVIK_FINAL_SAFE_TOWN_ACCESS_B2_",
        "SKARVIK_FINAL_SAFE_TOWN_ACCESS_B3_",
        "SKARVIK_FINAL_NATIVE_GRADED_ORIGINAL_MESH_",
        "SKARVIK_FINAL_NATIVE_ISLAND_ORIGINAL_MESH_",
        "SKARVIK_FINAL_CITYSAMPLE_3D_SOURCE_",
        "SKARVIK_FINAL_REGIONAL_DRY_NATIVE_PILOT_",
    )
    REPORT["nativePartitionDescriptors"]=len(desc)
    REPORT["verifiedPrefixes"]={p:sum(label.startswith(p) for label in labels)
                                 for p in prefixes}
    REPORT["landscapeDescriptors"]=sum(
        "Landscape" in str(getattr(d,"native_class","")) for d in desc)
    REPORT["playerStartDescriptors"]=sum(
        "PlayerStart" in str(getattr(d,"native_class","")) for d in desc)
    REPORT["knownSavedRoadMeshActors"]=sum(
        REPORT["verifiedPrefixes"].get(p,0) for p in prefixes[:4])+\
        REPORT["verifiedPrefixes"].get(prefixes[-1],0)
    REPORT["knownSavedBuildingMeshActors"]=sum(
        REPORT["verifiedPrefixes"].get(p,0) for p in prefixes[4:7])
    native=unreal.AnomaliaZPrigimaliaWorldImportLibrary
    if not hasattr(native,"skarvik_final_coastal_height"):
        raise RuntimeError("Compiled true final coastal height source missing")
    for east,north in ((2000.,-8000.),(14000.,15000.),(0.,0.)):
        h=float(native.skarvik_final_coastal_height(east,north))
        REPORT.setdefault("heightSamples",[]).append({
            "eastMeters":east,"northMeters":north,"heightMeters":round(h,2)})
    after={k:{"bytes":v.stat().st_size,"mtimeNs":v.stat().st_mtime_ns}
           for k,v in paths.items()}
    if after!=original_meta:
        raise RuntimeError("Protected source level metadata changed unexpectedly")
    REPORT["readOnlyProtectedMapMetadataUnchanged"]=True
    REPORT["state"]="ACTUAL_UE5_NATIVE_FINAL_WORLD_DESCRIPTOR_AUDIT_NO_SAVE"
except Exception:
    REPORT["error"]=traceback.format_exc()[-3000:]
finally:
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(REPORT,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    try:
        import unreal
        unreal.log("SKARVIK_READONLY_FINAL_WORLD_REPORT_STATE="+REPORT["state"])
    except Exception:
        pass
