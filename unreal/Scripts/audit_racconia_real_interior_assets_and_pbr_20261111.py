"""Native UE5.8 read-only assessment for 29 RACCONIA architecture sites.

Measurements: physically saved sites, source mesh/materials/triangles for
one sample per location, original existing non-cubic interior candidates,
and readiness for interactive player doors. No viewport screenshots, no
PIE, no source modification. A material slot does not prove photorealism.
"""
from __future__ import annotations
import collections
import hashlib
import json
import os
import re
import traceback
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUTPUT=Path(os.environ["RACCONIA_INTERIOR_PBR_READONLY_REPORT"]).resolve()
WORLD="/Game/Maps/PRIGIMALIA_RACCONIA_VARKOVIA_16KM_v1"
PREFIX="RACCONIA_ARCH_PBR_V2_"
BASENAMES={
  "door":("door","gate","porte"),
  "stairs":("stair","step","escalier"),
  "desk":("desk","counter","reception"),
  "furniture":("chair","table","sofa","bed","shelf","cabinet","locker"),
  "interior":("interior","hall","room","corridor"),
  "light":("light_fixture","lamp","chandelier","ceiling_light")
}
R={"state":"FAILED","readOnly":True,"world":WORLD,"originalLevelsModified":False,
 "sourceActorCount":0,"sourceSiteCount":0,"sampledMeshActors":0,
 "photorealismVisuallyVerified":False,"realTimeRenderingTested":False,
 "interiorsNavigableTested":False,"interactiveDoorsPlaced":False}
try:
    if ROOT.as_posix().lower()!="c:/anomaliaz_skarvik_stage_41188816555/unreal":
        raise RuntimeError("Untrusted UE5 staging project")
    if (ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
        raise RuntimeError("Invalid staging marker")
    paths=[
      ROOT/"Content/Maps/PRIGIMALIA_RACCONIA_VARKOVIA_16KM_v1.umap",
      ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap",
      ROOT/"Content/Map/Big_City_LVL.umap",
      Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap"),
    ]
    before={str(p):[p.stat().st_size,p.stat().st_mtime_ns] for p in paths}
    editor=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not editor.load_level(WORLD):
        raise RuntimeError("Native RACCONIA cannot reopen")
    ds=unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or []
    anchors=[d for d in ds if str(d.label).startswith("RACCONIA_ORIGINAL_SITE_")]
    sources=[d for d in ds if str(d.label).startswith(PREFIX)]
    if len(anchors)!=29 or len(sources)!=367:
        raise RuntimeError("Missing or changed original RACCONIA PBR architecture: "+str((len(anchors),len(sources))))
    bysite=collections.defaultdict(list)
    for d in sources:
        m=re.match(r"RACCONIA_ARCH_PBR_V2_(.+)_([0-9]{3})$",str(d.label))
        if not m:raise RuntimeError("Unrecognized source actor label")
        bysite[m.group(1)].append(d)
    if len(bysite)!=29:raise RuntimeError("29 original PBR venue IDs not preserved")
    R["sourceActorCount"]=len(sources)
    R["sourceSiteCount"]=len(bysite)
    # The cheap native source mesh already has the original 3D assembly.
    selected=[sorted(group,key=lambda d:str(d.label))[0] for _,group in sorted(bysite.items())]
    wp=unreal.WorldPartitionBlueprintLibrary
    wp.load_actors([d.guid for d in selected])
    loaded={a.get_actor_label():a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()}
    inspect=[]
    for d in selected:
        actor=loaded.get(str(d.label))
        if not isinstance(actor,unreal.StaticMeshActor):
            raise RuntimeError("Saved native PBR actor failed to load: "+str(d.label))
        comp=actor.get_component_by_class(unreal.StaticMeshComponent)
        mesh=comp.get_editor_property("static_mesh") if comp else None
        if not isinstance(mesh,unreal.StaticMesh):
            raise RuntimeError("Saved source mesh missing for "+str(d.label))
        matnames=[]
        for i in range(int(comp.get_num_materials())):
            mat=comp.get_material(i)
            matnames.append(mat.get_path_name() if mat else None)
        inspect.append({"sitePrefix":str(d.label).rsplit("_",1)[0],
                        "sourceActor":str(d.label),"mesh":mesh.get_path_name(),
                        "trianglesLOD0":int(mesh.get_num_triangles(0)),
                        "materialSlots":len(matnames),
                        "missingMaterialSlots":sum(x is None for x in matnames),
                        "materials":matnames[:30]})
    wp.unload_actors([d.guid for d in selected])
    R["sampledMeshActors"]=len(inspect);R["sampledPBRMeshMaterials"]=inspect
    # An actor can reference PBR textures yet still look rough; we never
    # equate material slot presence with physically convincing final rendering.
    registry=unreal.AssetRegistryHelpers.get_asset_registry()
    candidate=collections.defaultdict(list)
    for directory in ("/Game/Anomalia","/Game/City","/Game/Props","/Game/Kit","/Game/Environment","/Game/Map"):
        entries=registry.get_assets_by_path(directory,recursive=True)
        for asset in entries:
            n=str(asset.asset_name).lower()
            typ=str(asset.asset_class_path.asset_name).lower() if hasattr(asset,"asset_class_path") else ""
            if typ and "staticmesh" not in typ:continue
            for kind,keys in BASENAMES.items():
                if len(candidate[kind])>=65:continue
                if any(k in n for k in keys):
                    package=str(asset.package_name)
                    if package not in candidate[kind]:candidate[kind].append(package)
    R["availableCandidateMeshesByFunction"]={k:sorted(v) for k,v in candidate.items()}
    R["candidateMeshCountsByFunction"]={k:len(v) for k,v in candidate.items()}
    after={str(p):[p.stat().st_size,p.stat().st_mtime_ns] for p in paths}
    if before!=after:raise RuntimeError("Protected source file changed during native read-only audit")
    R.update(state="RACCONIA_PBR_SOURCES_AND_EXISTING_INTERIOR_ASSETS_READONLY_SURVEY_COMPLETE",
             originalLevelsModified=False)
except Exception as e:
    R["error"]=str(e);R["traceback"]=traceback.format_exc()[-6000:]
finally:
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(R,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    unreal.log("RACCONIA_INTERIOR_MESH_AUDIT="+R["state"])
