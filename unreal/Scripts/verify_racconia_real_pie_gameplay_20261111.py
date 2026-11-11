"""Run an actual transient PIE spawn/movement/door-component smoke test in saved RACCONIA.

No level saving or overwriting. This is *not* a photorealistic visual test;
NullRHI cannot establish image quality or certify all 491 authored rooms.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
MAP_PACKAGE="/Game/Maps/PRIGIMALIA_RACCONIA_VARKOVIA_16KM_v1"
OUT=Path(os.environ["RACCONIA_NATIVE_PIE_TEST_REPORT"]).resolve()
START=time.monotonic()
R={"state":"FAILED","test":"transient_RACCONIA_PIE_player_start_and_door_actor",
   "world":MAP_PACKAGE,"nativePIEStarted":False,"spawnedPlayer":False,
   "playerControllerPossessed":False,"walkingMovementVerified":False,
   "doorComponentInstantiated":False,"serverDoorToggleValidated":False,
   "all491InteriorsComplete":False,"all754InteractionsPassed":False,
   "all187PuzzlesSolved":False,"visualPhotorealismValidated":False,
   "RHI":"NullRHI", "savedWorldModified":False,"sourceDModified":False}
state={"phase":"setup","finished":False,"start":START,"last":START}

def record():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(R,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def require(flag,reason):
    if not flag:raise RuntimeError(reason)

def finish(err=None):
    if state["finished"]:return
    state["finished"]=True
    if err:R["error"]=str(err);R["traceback"]=traceback.format_exc()[-5000:]
    else:R["state"]="RACCONIA_NATIVE_TRANSIENT_PIE_SURVIVOR_AND_WORLD_SMOKE_PASSED_NO_VISUAL_CERTIFICATION"
    record()
    if "tick" in state:
        unreal.unregister_slate_post_tick_callback(state["tick"])
    try:
        state["editor"].editor_request_end_play()
    except Exception:
        pass
    def done(_delta):
        try:
            if not state["editor"].is_in_play_in_editor():
                unreal.unregister_slate_post_tick_callback(state.pop("close"))
                unreal.SystemLibrary.quit_editor()
        except Exception:
            pass
    try:state["close"]=unreal.register_slate_post_tick_callback(done)
    except Exception:pass

def tick(delta):
    if state["finished"]:return
    try:
        now=time.monotonic()
        require(now-START<195,"Timed out attempting real RACCONIA native PIE")
        ed=state["editor"]
        if state["phase"]=="await_pie":
            w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
            if not ed.is_in_play_in_editor() or not w:return
            require("UEDPIE_" in w.get_path_name(),"Not an actual PIE world")
            require("RACCONIA_VARKOVIA_16KM_v1" in w.get_path_name(),"PIE opened another map")
            ctrl=unreal.GameplayStatics.get_player_controller(w,0)
            if not ctrl:return
            actorlist=unreal.GameplayStatics.get_all_actors_of_class(w,state["class"])
            survivor=next((x for x in actorlist if unreal.Name("RACCONIA_PIE_TEMP_SURVIVOR") in x.tags),None)
            if not survivor:return
            ctrl.possess(survivor)
            require(survivor.get_controller()==ctrl,"Actual RACCONIA player possession failed")
            require(bool(survivor.get_editor_property("mesh")),"No native survivor skeletal component")
            R["nativePIEStarted"]=True
            R["spawnedPlayer"]=True
            R["playerControllerPossessed"]=True
            R["runtimeWorldName"]=w.get_path_name()
            R["startPositionCm"]=[survivor.get_actor_location().x,survivor.get_actor_location().y,
                                  survivor.get_actor_location().z]
            state.update(world=w,controller=ctrl,survivor=survivor,
                         beginMoveTime=now,startPos=survivor.get_actor_location(),phase="movement")
            record()
            return
        if state["phase"]=="movement":
            pawn=state["survivor"]
            pawn.add_movement_input(unreal.Vector(1,0,0),1.0,False)
            if now-state["beginMoveTime"]<3:return
            start=state["startPos"];end=pawn.get_actor_location()
            move=((end.x-start.x)**2+(end.y-start.y)**2)**.5
            R["motionDistanceCm"]=round(move,2)
            # A real character can be stopped by collision. Report movement
            # as blocked instead of making up a successful walking test.
            R["walkingMovementVerified"]=move>=80
            R["doorComponentInstantiated"]=bool(state["door"])
            R["state"]="RACCONIA_REAL_PIE_COMPLETE_MOVEMENT_NOT_CONFIRMED" if move<80 else R["state"]
            if move<80:raise RuntimeError("Native RACCONIA player did not traverse 80cm in PIE")
            finish()
    except Exception as exc:
        finish(exc)

try:
    require(ROOT.as_posix().lower()=="c:/anomaliaz_skarvik_stage_41188816555/unreal",
            "Untrusted UE5 project")
    require((ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()=="41188816555",
            "Untrusted marker")
    files=[
      ROOT/"Content/Maps/PRIGIMALIA_RACCONIA_VARKOVIA_16KM_v1.umap",
      ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap",
      Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap"),
    ]
    before={str(p):(p.stat().st_size,p.stat().st_mtime_ns) for p in files}
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    ed=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    require(ed.load_level(MAP_PACKAGE),"Original saved RACCONIA map cannot load")
    desc=unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or []
    anchors=[d for d in desc if str(d.label).startswith("RACCONIA_ORIGINAL_SITE_")]
    meshes=[d for d in desc if str(d.label).startswith("RACCONIA_ARCH_PBR_V2_")]
    require(len(anchors)==29 and len(meshes)==367,"Native 29 PBR sites changed unexpectedly")
    varkov=next((d for d in anchors if "VARKOV" in str(d.label)),None)
    require(varkov is not None,"Manor Varkov source anchor missing")
    p=varkov.bounds
    pos=unreal.Vector((p.min.x+p.max.x)/2+1400,(p.min.y+p.max.y)/2,
                      (p.min.z+p.max.z)/2+350)
    cls=unreal.EditorAssetLibrary.load_blueprint_class("/Game/Anomalia/Characters/BP_Anomalia_Survival")
    require(cls is not None,"Actual survival character Blueprint is not installed in this stage")
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    pawn=actors.spawn_actor_from_class(cls,pos)
    require(pawn is not None,"Native Survivor spawn failed")
    pawn.tags=list(pawn.tags)+[unreal.Name("RACCONIA_PIE_TEMP_SURVIVOR")]
    door=actors.spawn_actor_from_class(unreal.AnomaliaZPrigimaliaDoorActor,pos+unreal.Vector(450,250,0))
    require(door is not None,"Existing native replicated interactive door actor cannot spawn")
    # Existing native door component provides collision and server-validated
    # toggle API. We do NOT pretend a real detailed door leaf mesh is assigned.
    # This door is ephemeral PIE fixture, NOT installed in buildings.
    start=actors.spawn_actor_from_class(unreal.PlayerStart,pos+unreal.Vector(0,700,200))
    require(start is not None,"RACCONIA transient PlayerStart failed")
    ws=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_world_settings()
    ws.set_editor_property("default_game_mode",unreal.GameModeBase.static_class())
    require({str(p):(p.stat().st_size,p.stat().st_mtime_ns) for p in files}==before,
            "A source map unexpectedly changed on disk during PIE setup")
    R["sourceDModified"]=False
    R["savedWorldModified"]=False
    R["worldPartitionOriginalPBRActors"]=len(meshes)
    R["originalLandmarks"]=len(anchors)
    state.update(editor=ed,door=door,cls=cls,phase="await_pie")
    record()
    ed.editor_request_begin_play()
    state["tick"]=unreal.register_slate_post_tick_callback(tick)
except Exception as ex:
    finish(ex)
