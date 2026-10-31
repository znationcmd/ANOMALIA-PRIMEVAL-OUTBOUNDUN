r"""SKARVIK first native real-asset pilot, isolated 48km World Partition ONLY.

Creates 3 small, distinct village nuclei from real staged ANOMALIA house meshes.
Does not create full towns, traffic, crowds, roads or placeholder cubes.
Do not execute on production D: or a world other than PRIGIMALIA_SKARVIK_CITY_v1.
"""
import json
import math
import os
import traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
MAP="/Game/Maps/PRIGIMALIA_SKARVIK_CITY_v1"
SPEC=Path(os.environ.get("SKARVIK_LAYOUT_JSON",""))
OUT=Path(os.environ.get("SKARVIK_NATIVE_PILOT_REPORT",str(ROOT/"Saved/SkarvikCity/pilot-villages.json")))
PILOTS=("firvale","birch","southwood")
TAG="ANOMALIA_SKARVIK_REAL_VILLAGE_PILOT_V1"
MODELS={
    "wood":"/Game/Anomalia/InteractiveRealismReview_v1/wood_house_enterable/SM_wood_house_enterable",
    "coastal":"/Game/Anomalia/Buildings/Lot1/SM_coastal_house_v1",
    "garage":"/Game/Anomalia/Buildings/Lot1/SM_garage_v1",
    "townhouse":"/Game/Anomalia/Buildings/Expansion1/SM_townhouse",
    "barn":"/Game/Anomalia/Buildings/Expansion1/SM_farm_barn"
}
# Parcel centres in metres. 45m between building centres; central 12-20m street reserve.
PARCELS=(
    (-90,90,"wood"),(0,90,"coastal"),(90,90,"townhouse"),
    (-90,0,"garage"),(0,0,"wood"),(90,0,"barn"),
    (-90,-90,"coastal"),(0,-90,"townhouse"),(90,-90,"wood")
)
state=dict(state="FAILED",map=MAP,stagedHouses=[],villages=[],actorsSaved=0,
           125SitesComplete=False,roadsBuilt=False,citySampleLevelInstanceIntegrated=False,
           SM5Playtested=False,gamePackaged=False,originalDModified=False)
try:
    if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper() or ROOT.drive.upper()!="C:":
        raise RuntimeError("Not isolated C: SKARVIK stage; refusing to modify any world")
    if (ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
        raise RuntimeError("Stage marker mismatch")
    if not (ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_CITY_v1.umap").is_file():
        raise RuntimeError("SKARVIK target map package missing")
    if not SPEC.is_file():
        raise RuntimeError("No checked-out SKARVIK 125-locality layout JSON")
    plan=json.loads(SPEC.read_text(encoding="utf-8"))
    by_id={s["id"]:s for s in plan["settlements"]}
    if len(by_id)!=125 or set(PILOTS)-set(by_id):
        raise RuntimeError("Expected exactly 125 named sites including 3 original pilot villages")
    if any(s["settlementClass"]!="village" for s in [by_id[k] for k in PILOTS]):
        raise RuntimeError("Pilot ids were changed from original villages")
    for denied in ("Crowd","Vehicle"):
        if (ROOT/"Content"/denied).exists():
            raise RuntimeError("Forbidden City Sample "+denied+" folder detected")
    if not hasattr(unreal,"AnomaliaZPrigimaliaWorldImportLibrary"):
        raise RuntimeError("Native SKARVIK terrain height function unavailable")
    terrain=unreal.AnomaliaZPrigimaliaWorldImportLibrary
    height=getattr(terrain,"skarvik_city_height",None)
    if not callable(height):
        raise RuntimeError("Missing native skarvik_city_height method")
    meshes={}
    bounds={}
    for key,package in MODELS.items():
        mesh=unreal.EditorAssetLibrary.load_asset(package)
        if not isinstance(mesh,unreal.StaticMesh):
            raise RuntimeError("Cannot load genuine StaticMesh: "+package)
        b=mesh.get_bounds()
        dimensions=[2*b.box_extent.x/100,2*b.box_extent.y/100,2*b.box_extent.z/100]
        if min(dimensions)<=2 or max(dimensions)>50:
            raise RuntimeError("Invalid native model scale: "+key+" "+str(dimensions))
        meshes[key]=mesh
        bounds[key]=b
        state["stagedHouses"].append(dict(name=key,package=package,dimensionsMeters=dimensions))
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels.load_level(MAP):
        raise RuntimeError("Could not open 48km isolated SKARVIK map in editor")
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not world or world.get_path_name().split(".")[0]!=MAP:
        raise RuntimeError("Wrong opened world; stop before spawning")
    existing={a.get_actor_label() for a in actors.get_all_level_actors()}
    # Full upfront validation before touching the level. Keep all buildings in the
    # original reserved flat pads, but independently validate with native height.
    locations=[]
    for sid in PILOTS:
        village=by_id[sid]
        ce,cn=village["eastKm"]*1000.0,village["northKm"]*1000.0
        width,height_km=village["footprintKm"]
        for index,(de,dn,key) in enumerate(PARCELS):
            if abs(de)>width*500-20 or abs(dn)>height_km*500-20:
                raise RuntimeError("Parcel outside village footprint for "+sid)
            e,n=ce+de,cn+dn
            b=bounds[key]
            half_w=b.box_extent.x/100.0
            half_d=b.box_extent.y/100.0
            # Source landscapes are sampled at 15.87m, so checking four bounds
            # cannot prove collisions; this gate prevents obvious burying/hovering.
            samples=[float(height(e+dx,n+dy)) for dx,dy in
                     ((0,0),(-half_w,-half_d),(-half_w,half_d),(half_w,-half_d),(half_w,half_d))]
            if not all(math.isfinite(v) for v in samples):
                raise RuntimeError("Nonfinite terrain at "+sid)
            relief=max(samples)-min(samples)
            if relief>1.5:
                raise RuntimeError("Ground slope too steep for "+sid+" parcel "+str(index)+" (m): "+str(relief))
            label="ANOMALIA_SKARVIK_"+sid.upper()+"_REAL3D_"+str(index+1).zfill(2)
            if label in existing:
                raise RuntimeError("Existing actor must not be replaced or duplicated: "+label)
            locations.append(dict(site=sid,label=label,key=key,eastM=e,northM=n,
                                  terrainM=max(samples),reliefM=relief))
    # 27 real native StaticMeshActors, after validation only.
    for item in locations:
        key=item["key"]
        b=bounds[key]
        # Unreal cm: X=east, Y=-north; use static mesh bounds to place bottom at ground.
        xyz=unreal.Vector(item["eastM"]*100-b.origin.x,
                          -item["northM"]*100-b.origin.y,
                          item["terrainM"]*100-(b.origin.z-b.box_extent.z)+5)
        actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,xyz)
        if not actor:
            raise RuntimeError("Unreal failed to spawn StaticMeshActor "+item["label"])
        comp=actor.get_component_by_class(unreal.StaticMeshComponent)
        if not comp or not comp.set_static_mesh(meshes[key]):
            raise RuntimeError("Genuine StaticMesh did not attach to "+item["label"])
        comp.set_collision_profile_name("BlockAll")
        actor.set_actor_label(item["label"])
        actor.tags=[unreal.Name(TAG),unreal.Name("SKARVIK_"+item["site"].upper())]
        state["actorsSaved"]+=1
    if state["actorsSaved"]!=27:
        raise RuntimeError("27 house static mesh actors expected")
    if not levels.save_all_dirty_levels():
        raise RuntimeError("Could not save isolated SKARVIK World Partition level")
    if not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
        raise RuntimeError("Could not save isolated World Partition actor packages")
    state["villages"]=[dict(id=s,name=by_id[s]["name"],
                            realMeshActorCount=sum(1 for p in locations if p["site"]==s),
                            eastKm=by_id[s]["eastKm"],northKm=by_id[s]["northKm"],
                            onlyStarterNucleus=True,notFullVillage=True) for s in PILOTS]
    state["state"]="THREE_GENUINE_3D_VILLAGE_NUCLEI_SAVED_NOT_SM5_PLAYTESTED"
    unreal.log("SKARVIK_PILOT_VILLAGE_REAL_MESH_ACTORS_SAVED=27")
except Exception as exc:
    state["error"]=str(exc)
    state["traceback"]=traceback.format_exc()
    unreal.log_error("SKARVIK_PILOT_VILLAGE_ERROR="+str(exc))
finally:
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(state,indent=2)+"\n",encoding="utf-8")
    unreal.log("SKARVIK_PILOT_VILLAGE_REPORT="+str(OUT))
