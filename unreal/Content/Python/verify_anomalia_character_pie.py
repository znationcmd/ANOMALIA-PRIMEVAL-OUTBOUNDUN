"""Run measured single-player PIE checks; no inventory UI or multiplayer acceptance."""
import hashlib
import json
import os
from pathlib import Path
import time
import traceback
import unreal

OUT = Path(os.environ["ANOMALIA_PIE_REPORT"])
OUT.mkdir(parents=True, exist_ok=False)
report = {"state": "FAILED", "engine": unreal.SystemLibrary.get_engine_version(),
          "characters": [], "errors": [], "mode": "single_player_PIE",
          "input": "automated native pawn/component API calls; physical keyboard not tested",
          "inventoryUI": "not_tested", "save_reconnect": "not_tested", "multiplayer": "not_tested",
          "originalAssetsSaved": False}
s = {"start": time.monotonic(), "phase": "wait_world", "phase_at": time.monotonic(),
     "index": 0, "finished": False, "until": time.monotonic()+3}
names = ("Manny", "Quinn", "Survival")
editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
worlds = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)

def require(ok, why):
    if not ok:
        raise RuntimeError(why)

def pos(actor):
    v = actor.get_actor_location()
    return [v.x, v.y, v.z]

def record():
    (OUT/"report.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")

def finish(error=None):
    if s["finished"]:
        return
    s["finished"] = True
    if error:
        report["errors"].append(str(error))
        report["traceback"] = traceback.format_exc()
    else:
        report["state"] = "SINGLE_PLAYER_PIE_API_CHECKS_PASSED_NOT_FULL_GAMEPLAY_ACCEPTANCE"
    record()
    if s.get("handle"):
        unreal.unregister_slate_post_tick_callback(s.pop("handle"))
    editor.editor_request_end_play()
    def close(delta):
        if not editor.is_in_play_in_editor():
            unreal.unregister_slate_post_tick_callback(s.pop("close_handle"))
            unreal.SystemLibrary.quit_editor()
    s["close_handle"] = unreal.register_slate_post_tick_callback(close)

def phase(name):
    s["phase"] = name
    s["phase_at"] = time.monotonic()

def begin_actor():
    name = names[s["index"]]
    cls = unreal.EditorAssetLibrary.load_blueprint_class("/Game/Anomalia/Characters/BP_Anomalia_"+name)
    actors = unreal.GameplayStatics.get_all_actors_of_class(s["world"], cls)
    require(len(actors) == 1, "Expected one placed test pawn for "+name)
    actor = actors[0]
    actor.set_actor_location(unreal.Vector(-1500, s["index"]*400, 110), False, True)
    s["pc"].possess(actor)
    require(s["pc"].get_pawn() == actor and actor.is_locally_controlled(), "Possession failed "+name)
    mesh = actor.get_editor_property("mesh")
    require(mesh.get_anim_instance() is not None, "No runtime AnimInstance "+name)
    require(actor.get_editor_property("follow_camera").is_active(), "Inactive follow camera "+name)
    inv = actor.get_editor_property("inventory_component")
    require(inv is not None, "No runtime inventory "+name)
    s.update(actor=actor, mesh=mesh, inv=inv, vitals=actor.get_editor_property("vitals_component"),
             movement=actor.get_character_movement())
    row={"name":name,"pawn":actor.get_path_name(),"possessed":True,
         "animationInstance":mesh.get_anim_instance().get_class().get_path_name(),
         "cameraActive":True,"startCm":pos(actor),"maxWalkSpeedObserved":0.0,
         "maxSprintSpeedObserved":0.0,"jumpRiseCm":0.0,"maxBoneDisplacementCm":0.0}
    report["characters"].append(row)
    s["row"]=row
    s["bone_start"]=mesh.get_bone_transform("hand_l",unreal.RelativeTransformSpace.RTS_COMPONENT).translation
    s["capsule_standing"]=actor.get_editor_property("capsule_component").get_scaled_capsule_half_height()
    phase("settle")

def tick(delta):
    if s["finished"]:
        return
    try:
        now=time.monotonic()
        require(now-s["start"]<240, "PIE check timed out at "+s["phase"])
        if s["phase"]=="wait_world":
            w=worlds.get_game_world()
            if not editor.is_in_play_in_editor() or not w:
                return
            require("UEDPIE_" in w.get_path_name(), "Not a PIE world: "+w.get_path_name())
            pc=unreal.GameplayStatics.get_player_controller(w,0)
            if not pc or now<s["until"]:
                return
            s.update(world=w,pc=pc)
            report["world"]=w.get_path_name()
            begin_actor()
            return
        actor=s["actor"];row=s["row"];elapsed=now-s["phase_at"]
        velocity=actor.get_velocity()
        speed=(velocity.x**2+velocity.y**2)**0.5
        t=s["mesh"].get_bone_transform("hand_l",unreal.RelativeTransformSpace.RTS_COMPONENT).translation
        b=s["bone_start"]
        row["maxBoneDisplacementCm"]=max(row["maxBoneDisplacementCm"],((t.x-b.x)**2+(t.y-b.y)**2+(t.z-b.z)**2)**0.5)
        if s["phase"]=="settle" and elapsed>1.5:
            s["walk_start"]=pos(actor);phase("walk")
        elif s["phase"]=="walk":
            actor.add_movement_input(unreal.Vector(1,0,0),1,False)
            row["maxWalkSpeedObserved"]=max(row["maxWalkSpeedObserved"],speed)
            if elapsed>1.6:
                row["walkDistanceCm"]=abs(pos(actor)[0]-s["walk_start"][0])
                require(row["walkDistanceCm"]>100,"Pawn did not walk "+row["name"])
                s["stamina_before"]=s["vitals"].get_editor_property("stamina")
                s["vitals"].request_sprint(True);phase("sprint")
        elif s["phase"]=="sprint":
            actor.add_movement_input(unreal.Vector(1,0,0),1,False)
            row["maxSprintSpeedObserved"]=max(row["maxSprintSpeedObserved"],speed)
            if elapsed>1.6:
                row["staminaBefore"]=s["stamina_before"]
                row["staminaAfter"]=s["vitals"].get_editor_property("stamina")
                s["vitals"].request_sprint(False)
                require(row["maxSprintSpeedObserved"]>row["maxWalkSpeedObserved"]+20,"Sprint did not increase speed "+row["name"])
                require(row["staminaAfter"]<row["staminaBefore"],"Sprint did not consume stamina "+row["name"])
                s["movement"].stop_movement_immediately()
                actor.crouch();phase("crouch")
        elif s["phase"]=="crouch" and elapsed>0.8:
            h=actor.get_editor_property("capsule_component").get_scaled_capsule_half_height()
            row["standingCapsuleHalfHeightCm"]=s["capsule_standing"]
            row["crouchedCapsuleHalfHeightCm"]=h
            require(h<s["capsule_standing"]-5,"Crouch capsule did not shrink "+row["name"])
            actor.uncrouch();phase("stand")
        elif s["phase"]=="stand" and elapsed>0.8:
            require(abs(actor.get_editor_property("capsule_component").get_scaled_capsule_half_height()-s["capsule_standing"])<1,"Uncrouch failed")
            s["jump_start"]=pos(actor)[2]
            actor.jump();phase("jump")
        elif s["phase"]=="jump":
            row["jumpRiseCm"]=max(row["jumpRiseCm"],pos(actor)[2]-s["jump_start"])
            if elapsed>0.25:
                actor.stop_jumping()
            if elapsed>2:
                require(row["jumpRiseCm"]>10,"No jump rise "+row["name"])
                require(not s["movement"].is_falling(),"Did not land on test floor "+row["name"])
                require(row["maxBoneDisplacementCm"]>0.1,"No runtime bone motion "+row["name"])
                weight_before=s["inv"].get_current_weight_kg()
                require(s["inv"].try_add_item("apple",1),"Runtime inventory rejected catalog apple "+row["name"])
                row["inventoryWeightBeforeKg"]=weight_before
                row["inventoryWeightWithAppleKg"]=s["inv"].get_current_weight_kg()
                require(row["inventoryWeightWithAppleKg"]>weight_before,"Inventory weight did not rise")
                require(s["inv"].try_remove_item("apple",1),"Inventory remove failed")
                row["inventoryAddRemoveApple"]=True
                row["endCm"]=pos(actor)
                if row["name"]=="Survival":
                    garment=unreal.load_asset("/Game/Survival_Character/Meshes/Modular_Parts/SK_Survival_Character_Jacket")
                    require(actor.set_clothing_mesh("Jacket",None),"Runtime jacket removal failed")
                    require(actor.get_editor_property("jacket_mesh").get_editor_property("skeletal_mesh_asset") is None,"Jacket remains")
                    require(actor.set_clothing_mesh("Jacket",garment),"Runtime jacket re-equip failed")
                    row["runtimeJacketRemoveReequip"]=True
                record()
                s["index"]+=1
                if s["index"]==len(names):
                    finish()
                else:
                    begin_actor()
    except Exception as exc:
        finish(exc)

try:
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    require(editor.load_level("/Game/Anomalia/CharacterTests/L_Anomalia_Characters"),"Missing isolated character test map")
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in actors.get_all_level_actors():
        if a.get_actor_label()=="ANOMALIA test floor":
            a.set_actor_scale3d(unreal.Vector(200,200,.2))
    actors.spawn_actor_from_class(unreal.SkyAtmosphere,unreal.Vector())
    settings=unreal.get_default_object(unreal.LevelEditorPlaySettings)
    settings.set_editor_property("play_number_of_clients",1)
    settings.set_editor_property("play_net_mode",unreal.PlayNetMode.PIE_STANDALONE)
    w=worlds.get_editor_world()
    for command in ("r.DynamicGlobalIlluminationMethod 0","r.ReflectionMethod 0",
                    "r.Shadow.Virtual.Enable 0","r.Nanite 0","t.MaxFPS 30"):
        unreal.SystemLibrary.execute_console_command(w,command)
    editor.editor_request_begin_play()
    s["handle"]=unreal.register_slate_post_tick_callback(tick)
except Exception as exc:
    finish(exc)
