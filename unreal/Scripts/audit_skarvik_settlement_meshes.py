"""Read-only audit of real building static meshes available for 125 SKARVIK localities.
Does not spawn placeholder actors or alter levels. Output contains asset paths only.
"""
import json, os, re, traceback
from pathlib import Path
import unreal
root=Path(unreal.Paths.project_dir()).resolve()
out=Path(os.environ.get("SKARVIK_BUILDING_CATALOG_REPORT",str(root/"Saved/SkarvikCity/building-catalog.json")))
state={"state":"FAILED","catalogue":[],"totalStaticMeshesByFolder":{},"originalDModified":False}
try:
    if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(root).upper():
        raise RuntimeError("Untrusted project root")
    if (root/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
        raise RuntimeError("Missing correct stage marker")
    registry=unreal.AssetRegistryHelpers.get_asset_registry()
    groups=[
        ("/Game/Building","building"),
        ("/Game/City","city"),
        ("/Game/Environment","environment"),
        ("/Game/Prop","prop"),
        ("/Game/Road","road"),
        ("/Game/Anomalia","anomalia")
    ]
    rx=re.compile("(?i)(house|home|cabin|hut|villa|residen|apart|bldg|building|shop|store|farm|barn|hospital|police|station|church|town|roof|door|bridge|road|cottage|hotel|market|warehouse|shelter|garage|wall)")
    for folder,group in groups:
        count=0
        interesting=[]
        for asset in registry.get_assets_by_path(unreal.Name(folder),recursive=True):
            typ=str(asset.asset_class_path.asset_name)
            if typ!="StaticMesh":continue
            count+=1
            name=str(asset.asset_name)
            if rx.search(name):
                interesting.append({"name":name,"objectPath":str(asset.get_soft_object_path()),"package":str(asset.package_name)})
        state["totalStaticMeshesByFolder"][folder]=count
        interesting=sorted(interesting,key=lambda z:z["name"].lower())
        state["catalogue"].extend([dict(group=group,**e) for e in interesting[:150]])
        unreal.log("SKARVIK_BUILDING_MESH_GROUP={} total={} interesting={}".format(folder,count,len(interesting)))
    state["totalBuildingCandidates"]=len(state["catalogue"])
    state["state"]="READ_ONLY_STATIC_MESH_CATALOG_READY"
    unreal.log("SKARVIK_BUILDING_CATALOGUE_READY=true")
except Exception as e:
    state["error"]=str(e)
    state["traceback"]=traceback.format_exc()
    unreal.log_error("SKARVIK_BUILDING_CATALOGUE_ERROR="+str(e))
finally:
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(state,indent=2)+"\n",encoding="utf-8")
