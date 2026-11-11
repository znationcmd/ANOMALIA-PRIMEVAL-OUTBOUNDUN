"""Genuine UE5.8 rendered preview: real SKARVIK city, E39 v7, Survivor, GSD.

No AI/synthetic imagery and NO source maps saved. Capture actual engine
viewport pixels during single-player PIE. If gameplay/render fails, fail and
report honestly, never substitute unrelated images or claim a successful MP4.
"""
from __future__ import annotations
import hashlib
import json
import math
import os
import time
import traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
OUTPUT=Path(os.environ["ANOMALIA_AUTHENTIC_GAMEPLAY_FRAMES"]).resolve()
LEVEL="/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1"
CITY_PREFIXES=("SKARVIK_FINAL_CITYSAMPLE_3D_SOURCE_",
               "SKARVIK_FINAL_REAL_CITYSAMPLE_DISTRICT_")
ENGINE_CAPTURE_FRAMES=36
MAX_SECONDS=650
R={"state":"FAILED","source":"UE5.8_RENDERED_PIXELS_NOT_AI", "map":LEVEL,
   "actualPIEStarted":False,"realCityMeshActorsSelected":0,
   "originalBMWBodyLoaded":False,"realSurvivorMeshLoaded":False,
   "realGermanShepherdMeshLoaded":False,"totalFramesCaptured":0,
   "frames":[],"originalSourceMapsSaved":False,"actualMP4Produced":False,
   "BMWPhysicallyDriven":False,"realGameplayInputVerified":False,
   "BMWInteractiveGameplayVerified":False,"realTime24FPSVerified":False,
   "photorealismVisuallyReviewed":False}
S={"started":time.monotonic(),"busy":False,"phase":"INIT","index":0,"task":None,"done":False}
REPORT=OUTPUT/"ue5-frame-capture-receipt.json"

def write():
    OUTPUT.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(R,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def require(flag,why):
    if not flag:raise RuntimeError(why)

def screenshot_position(i):
    # Orbit/track around genuine City Sample architecture and the
    # REAL original BMW mesh, Survivor and German Shepherd.
    t=i/max(1,ENGINE_CAPTURE_FRAMES-1)
    angle=math.radians(-95+135*t)
    radius=1100+180*math.sin(2*math.pi*t)
    eye=unreal.Vector(S["center"].x+math.cos(angle)*radius,
                      S["center"].y+math.sin(angle)*radius,
                      S["center"].z+200+110*math.sin(2*math.pi*t))
    target=unreal.Vector(S["center"].x,S["center"].y,S["center"].z+120)
    direction=unreal.MathLibrary.find_look_at_rotation(eye,target)
    return eye,direction

def restore_and_quit(err=None):
    if S["done"]:return
    S["done"]=True
    if err:
        R["error"]=str(err)
        R["traceback"]=traceback.format_exc()[-6500:]
    else:
        R["state"]="REAL_UE5_IN_ENGINE_PIE_VIEWPORT_FRAMES_CAPTURED_NOT_DIRECT_24FPS_GAMEPLAY"
    write()
    if "handler" in S:
        try:unreal.unregister_slate_post_tick_callback(S.pop("handler"))
        except Exception:pass
    try:
        S["editor"].editor_request_end_play()
    except Exception:
        pass
    try:
        unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    except Exception:
        pass
    try:unreal.SystemLibrary.quit_editor()
    except Exception:pass

def tick(delta):
    if S["busy"] or S["done"]:return
    try:
        require(time.monotonic()-S["started"]<MAX_SECONDS,"UE5 capture timed out")
        if S["phase"]=="WAIT_PIE":
            editor=S["editor"]
            if not editor.is_in_play_in_editor():return
            game=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
            if not game:return
            require("UEDPIE_" in game.get_path_name(),"No actual Unreal PIE world")
            R["actualPIEStarted"]=True
            S["gameWorld"]=game
            camera=S["camera"]
            # In PIE a world duplicate may exist; look up its tagged camera
            matching=unreal.GameplayStatics.get_all_actors_of_class(game,unreal.CineCameraActor)
            found=next((a for a in matching if unreal.Name("AUTHENTIC_ANOMALIA_VIDEO_CAMERA") in a.tags),None)
            require(found is not None,"Transient capture camera not copied to game world")
            controller=unreal.GameplayStatics.get_player_controller(game,0)
            require(controller is not None,"Player controller not started in PIE")
            # UE5 Python exposes APlayerController::SetViewTargetWithBlend,
            # not every engine wrapper exposes the non-Blueprint SetViewTarget.
            if hasattr(controller,"set_view_target_with_blend"):
                controller.set_view_target_with_blend(found,0.0)
                R["nativeCameraAttachedToPlayerController"]=True
            else:
                R["nativeCameraAttachedToPlayerController"]=False
                unreal.log_warning("Native camera blend method unavailable; using actual UE editor PIE viewport")
            S["cameraPIE"]=found
            S["phase"]="CAPTURE"
            S["next"]=time.monotonic()+8
            write()
            return
        if S["phase"]!="CAPTURE" or time.monotonic()<S["next"]:return
        if S["task"] is None:
            eye,rot=screenshot_position(S["index"])
            # Drive both real runtime cinema camera and editor's visible
            # PIE viewport to the same world-space position.
            S["cameraPIE"].set_actor_location_and_rotation(eye,rot,False,True)
            engine=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
            engine.set_level_viewport_camera_info(eye,rot)
            name=f"ue5_real_{S['index']:04d}.png"
            S["busy"]=True
            task=unreal.AutomationLibrary.take_high_res_screenshot(960,540,
                    str(OUTPUT/name),delay=.35,force_game_view=True)
            require(task is not None and task.is_valid_task(),"Unreal screenshot task rejected")
            S["task"]=task
            S["busy"]=False
            return
        if not S["task"].is_task_done():return
        file=OUTPUT/f"ue5_real_{S['index']:04d}.png"
        require(file.is_file() and file.stat().st_size>6000,
                "Real Unreal render missing; cannot fabricate a movie")
        R["frames"].append({"file":file.name,"bytes":file.stat().st_size,
                            "sha256":hashlib.sha256(file.read_bytes()).hexdigest()})
        R["totalFramesCaptured"]=len(R["frames"])
        if S["index"]%6==0:write()
        S["index"]+=1
        S["task"]=None
        if S["index"]>=ENGINE_CAPTURE_FRAMES:
            restore_and_quit()
            return
        S["next"]=time.monotonic()+.2
    except Exception as exc:
        S["busy"]=False
        unreal.log_error("ANOMALIA_REAL_GAMEPLAY_CAPTURE_ERROR="+traceback.format_exc())
        restore_and_quit(exc)

try:
    require(ROOT.as_posix().lower()=="c:/anomaliaz_skarvik_stage_41188816555/unreal",
            "Unexpected Unreal project: never modify originals")
    require((ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()=="41188816555",
            "Isolated stage marker absent")
    original_files=[
        ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap",
        ROOT/"Content/Map/Big_City_LVL.umap",
        Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap"),
    ]
    R["originalSourceHashesBefore"]={str(p):hashlib.sha256(p.read_bytes()).hexdigest()
                                      for p in original_files}
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    editor=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    S["editor"]=editor
    require(editor.load_level(LEVEL),"Actual SKARVIK map cannot open")
    desc=unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or []
    city=[d for d in desc if str(d.label).startswith(CITY_PREFIXES)]
    require(len(city)>=40,"Original real City Sample world partition actor count insufficient")
    origin=unreal.Vector(200000.,800000.,0.)
    city=sorted(city,key=lambda d:(d.bounds.min.x+d.bounds.max.x-origin.x*2)**2+
                                   (d.bounds.min.y+d.bounds.max.y-origin.y*2)**2)
    selection=city[:100]
    unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in selection])
    R["realCityMeshActorsSelected"]=len(selection)
    center=unreal.Vector(200000.,800000.,0.)
    near=selection[0].bounds
    center.x=(near.min.x+near.max.x)/2
    center.y=(near.min.y+near.max.y)/2
    center.z=near.min.z+100.
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    carmesh=unreal.EditorAssetLibrary.load_asset("/Game/Anomalia/BMWE39Review_v7/body/SM_body")
    humanmesh=unreal.EditorAssetLibrary.load_asset("/Game/Survival_Character/Meshes/SK_Survival_Character")
    dogmesh=unreal.EditorAssetLibrary.load_asset("/Game/German_Shepherd_3D_Model/Models/SK_GermanShepherd_01")
    require(isinstance(carmesh,unreal.StaticMesh),"Authentic BMW E39 v7 body missing")
    require(isinstance(humanmesh,unreal.SkeletalMesh),"Authentic survivor skeletal mesh missing")
    require(isinstance(dogmesh,unreal.SkeletalMesh),"Authentic German shepherd skeletal mesh missing")
    R.update(originalBMWBodyLoaded=True,realSurvivorMeshLoaded=True,realGermanShepherdMeshLoaded=True)
    car=actors.spawn_actor_from_class(unreal.StaticMeshActor,center)
    require(car is not None,"Could not place authentic BMW body")
    require(car.get_component_by_class(unreal.StaticMeshComponent).set_static_mesh(carmesh),
            "Authentic BMW StaticMesh assignment failed")
    car.set_actor_label("ANOMALIA_VIDEO_REAL_BMW_E39_V7")
    car.tags=[unreal.Name("AUTHENTIC_ANOMALIA_VIDEO_BMW")]
    survivor=actors.spawn_actor_from_class(unreal.AnomaliaZPrigimaliaSurvivor,
                                            center+unreal.Vector(400.,-240.,100.))
    require(survivor is not None,"Cannot spawn real playable native survivor")
    survivor.get_editor_property("mesh").set_editor_property("skeletal_mesh_asset",humanmesh)
    survivor.tags=[unreal.Name("AUTHENTIC_ANOMALIA_VIDEO_SURVIVOR")]
    dog=actors.spawn_actor_from_class(unreal.AnomaliaZPrigimaliaDogCompanion,
                                       center+unreal.Vector(600.,-300.,100.))
    require(dog is not None,"Cannot spawn genuine dog companion class")
    dog.get_editor_property("mesh").set_editor_property("skeletal_mesh_asset",dogmesh)
    dog.tags=[unreal.Name("AUTHENTIC_ANOMALIA_VIDEO_DOG")]
    dog.set_editor_property("auto_assign_nearest_survivor",True)
    # A movable camera is an actual game Actor, duplicated into PIE.
    camera=actors.spawn_actor_from_class(unreal.CineCameraActor,
                                          center+unreal.Vector(-1100.,-450.,300.))
    require(camera is not None,"Cannot create real in-game CineCamera")
    camera.tags=[unreal.Name("AUTHENTIC_ANOMALIA_VIDEO_CAMERA")]
    S["camera"]=camera
    S["center"]=center
    R["sourceLocationCm"]=[center.x,center.y,center.z]
    R["realOriginalActorsSpawnedTransiently"]=3
    if R["originalSourceHashesBefore"]!={str(p):hashlib.sha256(p.read_bytes()).hexdigest()
                                          for p in original_files}:
        raise RuntimeError("Original map changed; refuse to claim safety")
    write()
    editor.editor_request_begin_play()
    S["phase"]="WAIT_PIE"
    S["handler"]=unreal.register_slate_post_tick_callback(tick)
except Exception as exc:
    restore_and_quit(exc)
