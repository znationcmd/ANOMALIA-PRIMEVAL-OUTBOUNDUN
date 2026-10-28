"""Measure Survival alone in a transient PIE scene; no UI/network/persistence acceptance."""
import hashlib
import json
import os
from pathlib import Path
import time
import traceback
import unreal

OUT = Path(os.environ["ANOMALIA_PIE_REPORT"])
OUT.mkdir(parents=True, exist_ok=False)
report = {"state": "FAILED", "newAssetsSaved": [], "screenshots": [], "engine": unreal.SystemLibrary.get_engine_version(),
          "characters": [], "errors": [], "mode": "single_player_PIE",
          "input": "automated native pawn/component API calls; physical keyboard not tested",
          "inventoryUI": "not_tested", "save_reconnect": "not_tested", "multiplayer": "not_tested",
          "originalAssetsSaved": False}
s = {"start": time.monotonic(), "phase": "wait_world", "phase_at": time.monotonic(),
     "index": 0, "finished": False, "until": time.monotonic()+3}
names = ("Survival",)
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
        report["state"] = "SURVIVAL_PLAYTEST_PROFILE_RELOAD_AND_PIE_PASSED_NOT_UI_NETWORK_ACCEPTANCE"
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
    s["phase_at"] = unreal.GameplayStatics.get_time_seconds(s["world"])
    s["phase_at_wall"] = time.monotonic()

def begin_actor():
    name = names[s["index"]]
    cls = s["classes"][name]
    actor = unreal.GameplayStatics.get_player_pawn(s["world"],0)
    require(actor is not None and actor.get_class()==cls,"Native GameMode did not spawn the saved Survival child")
    actor.set_actor_location(unreal.Vector(-1500, s["index"]*400, 110), False, True)
    require(actor.get_controller() == s["pc"] and actor.is_locally_controlled(), "Possession failed "+name)
    mesh = actor.get_editor_property("mesh")
    require(mesh.get_anim_instance() is not None, "No runtime AnimInstance "+name)
    require(actor.get_editor_property("follow_camera").is_active(), "Inactive follow camera "+name)
    inv = actor.get_editor_property("inventory_component")
    require(inv is not None, "No runtime inventory "+name)
    s.update(actor=actor, mesh=mesh, inv=inv, vitals=actor.get_editor_property("vitals_component"),
             movement=actor.get_editor_property("character_movement"))
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
        require(now-s["start"]<360, "PIE check timed out at "+s["phase"])
        if s["phase"]=="wait_world":
            w=worlds.get_game_world()
            if not editor.is_in_play_in_editor() or not w:
                return
            require("UEDPIE_" in w.get_path_name(), "Not a PIE world: "+w.get_path_name())
            require(not unreal.GameplayStatics.is_game_paused(w),"PIE startup is paused")
            pc=unreal.GameplayStatics.get_player_controller(w,0)
            if not pc or now<s["until"]:
                return
            s.update(world=w,pc=pc)
            unreal.GameplayStatics.open_level(w,s["map"],True,"AnomaliaServerId="+s["scope"])
            s["phase"]="travel_to_playtest";s["phase_at_wall"]=now
            return
        if s["phase"] in ("travel_to_playtest","profile_reload"):
            require(now-s["phase_at_wall"]<60,"Scoped playtest travel timed out")
            w=worlds.get_game_world()
            if not w:
                return
            gm=unreal.GameplayStatics.get_game_mode(w)
            if not gm or gm.get_class()!=s["game_mode_class"]:
                return
            require(gm.get_editor_property("server_id")==s["scope"],"Wrong server profile; test stopped")
            actor=unreal.GameplayStatics.get_player_pawn(w,0)
            if not actor or actor.get_class()!=s["classes"]["Survival"] or unreal.GameplayStatics.get_time_seconds(w)<3:
                return
            if s["phase"]=="profile_reload" and actor==s["before_reload_actor"]:
                return
            s.update(world=w,pc=unreal.GameplayStatics.get_player_controller(w,0))
            inv=actor.get_editor_property("inventory_component")
            apples=sum(x.count for x in inv.get_editor_property("stacks") if str(x.item_id)=="apple")
            if s["phase"]=="travel_to_playtest":
                require(apples==2,"Seeded inventory did not load through native GameMode")
                report["nativeGameModeLoadedSeededInventory"]=True
                report["world"]=w.get_path_name()
                begin_actor()
            else:
                require(apples==1,"Consumed item did not survive native profile/map reload")
                report["nativeProfileReloadAppleCount"]=apples
                report["nativeProfileReloadNewPawn"]=True
                s["actor"]=actor
                s["shot_views"]=[("Survival_equipped_front",True,180),("Survival_jacket_removed_front",False,180),("Survival_equipped_back",True,0)]
                s.update(shot_index=0,shot_task=None,shot_ready=0)
                phase("screenshots")
            return
        if s["phase"]=="screenshots":
            require(now-s["phase_at_wall"]<60,"PIE screenshot timed out")
            name,equipped,yaw=s["shot_views"][s["shot_index"]]
            if not s["shot_ready"]:
                require(s["actor"].set_clothing_mesh("Jacket",s["jacket"] if equipped else None),"Screenshot outfit switch rejected")
                s["pc"].set_control_rotation(unreal.Rotator(pitch=-8,yaw=yaw))
                s["shot_ready"]=now+2
                return
            if now<s["shot_ready"]:
                return
            if s["shot_task"] is None:
                s["shot_task"]=unreal.AutomationLibrary.take_high_res_screenshot(1280,720,str(OUT/(name+".png")),delay=1.,force_game_view=True)
                require(s["shot_task"] and s["shot_task"].is_valid_task(),"PIE capture task unavailable")
                return
            if not s["shot_task"].is_task_done():
                return
            p=OUT/(name+".png")
            require(p.is_file() and p.stat().st_size>4096,"PIE screenshot missing")
            report["screenshots"].append({"file":p.name,"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"bytes":p.stat().st_size,"jacketEquipped":equipped,"cameraControlYaw":yaw})
            s["shot_index"]+=1
            if s["shot_index"]==len(s["shot_views"]):
                finish()
            else:
                s.update(shot_task=None,shot_ready=0)
            return
        actor=s["actor"];row=s["row"];elapsed=unreal.GameplayStatics.get_time_seconds(s["world"])-s["phase_at"]
        row["runtimeMovementMode"]=str(s["movement"].get_editor_property("movement_mode"))
        row["runtimeMaxWalkSpeedCmS"]=s["movement"].get_editor_property("max_walk_speed")
        row["inputIgnored"]=actor.is_move_input_ignored()
        row["lastPositionCm"]=pos(actor)
        row["phase"]=s["phase"]
        row["phaseSimulationSeconds"]=elapsed
        require(not row["inputIgnored"],"Possessed character has movement input disabled")
        require(now-s["phase_at_wall"]<25,"Simulation phase stalled: "+s["phase"])
        if now-s.get("checkpoint_at",0)>1:
            s["checkpoint_at"]=now
            record()
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
            actor.un_crouch();phase("stand")
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
                    garment=s["jacket"]
                    require(actor.set_clothing_mesh("Jacket",None),"Runtime jacket removal failed")
                    require(actor.get_editor_property("jacket_mesh").get_editor_property("skeletal_mesh_asset") is None,"Jacket remains")
                    require(actor.set_clothing_mesh("Jacket",garment),"Runtime jacket re-equip failed")
                    row["runtimeJacketRemoveReequip"]=True
                record()
                s["index"]+=1
                if s["index"]==len(names):
                    actor.restore_survival(80,80,100)
                    stack=next(x for x in s["inv"].get_editor_property("stacks") if str(x.item_id)=="apple")
                    require(stack.count==2,"Unexpected test inventory before consumption")
                    require(s["inv"].request_use_stack(stack.stack_id,stack.count),"Native item use rejected: "+str(s["inv"].get_editor_property("use_message")))
                    remaining=sum(x.count for x in s["inv"].get_editor_property("stacks") if str(x.item_id)=="apple")
                    require(remaining==1 and actor.get_editor_property("hunger")>80,"Native apple consumption had no inventory/survival effect")
                    report["nativeAppleConsumption"]={"remaining":remaining,"hungerAfter":actor.get_editor_property("hunger")}
                    s["before_reload_actor"]=actor
                    phase("profile_reload")
                    unreal.GameplayStatics.open_level(s["world"],s["map"],True,"AnomaliaServerId="+s["scope"])
                else:
                    begin_actor()
    except Exception as exc:
        finish(exc)

try:
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    ROOT="/Game/Anomalia/CharacterTests/SurvivalPlayable_"+os.environ["GITHUB_RUN_ID"]
    MAP=ROOT+"/L_Survival_Playtest"
    PAWN=ROOT+"/BP_Survival_Playtest"
    GM=ROOT+"/GM_Survival_Playtest"
    SCOPE="survival-playtest-"+os.environ["GITHUB_RUN_ID"]
    require(all(not unreal.EditorAssetLibrary.does_asset_exist(p) for p in (MAP,PAWN,GM)),"Existing assets preserved")
    require(not (Path(unreal.Paths.project_saved_dir())/"Servers"/SCOPE).exists(),"Existing server profile preserved")
    source_class=unreal.EditorAssetLibrary.load_blueprint_class("/Game/Anomalia/Characters/BP_Anomalia_Survival")
    require(source_class is not None,"Verified Survival Blueprint missing")
    body=unreal.get_default_object(source_class).get_editor_property("mesh")
    body_asset=body.get_editor_property("skeletal_mesh_asset")
    anim_class=body.get_editor_property("anim_class")
    require(body_asset is not None and anim_class is not None,"Verified body/AnimBP missing")
    garments={"Jacket":("JacketMesh","jacket_mesh","Jacket"),"Pants":("PantsMesh","pants_mesh","Jeans"),
              "Boots":("BootsMesh","boots_mesh","Shoes"),"Gloves":("GlovesMesh","gloves_mesh","Gloves"),
              "Backpack":("BackpackMesh","backpack_mesh","Backpack")}
    parts={}
    for slot,(_,prop,suffix) in garments.items():
        a=unreal.load_asset("/Game/Survival_Character/Meshes/Modular_Parts/SK_Survival_Character_"+suffix)
        require(a is not None and a.get_editor_property("skeleton")==body_asset.get_editor_property("skeleton"),"Unapproved garment skeleton "+slot)
        parts[slot]=a
    factory=unreal.BlueprintFactory()
    factory.set_editor_property("parent_class",unreal.load_class(None,"/Script/AnomaliaPrimeval.AnomaliaSurvivor"))
    bp=unreal.AssetToolsHelpers.get_asset_tools().create_asset("BP_Survival_Playtest",ROOT,unreal.Blueprint,factory)
    require(bp is not None,"Playtest child creation failed")
    subsystem=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    lib=unreal.SubobjectDataBlueprintFunctionLibrary
    wanted={"Mesh":None,**{row[0]:slot for slot,row in garments.items()}}
    templates={}
    for handle in subsystem.k2_gather_subobject_data_for_blueprint(bp):
        data=lib.get_data(handle)
        name=str(lib.get_variable_name(data))
        if name not in wanted:
            continue
        component=lib.get_object_for_blueprint(data,bp)
        require(isinstance(component,unreal.SkeletalMeshComponent) and component.get_path_name().startswith(PAWN+"."),"Parent component template preserved "+name)
        templates[name]=component
    require(set(templates)==set(wanted),"Editable inherited garment templates missing: "+str(set(wanted)-set(templates)))
    templates["Mesh"].set_editor_property("skeletal_mesh_asset",body_asset)
    templates["Mesh"].set_editor_property("animation_mode",unreal.AnimationMode.ANIMATION_BLUEPRINT)
    templates["Mesh"].set_editor_property("anim_class",anim_class)
    templates["Mesh"].set_editor_property("relative_location",unreal.Vector(0,0,-90))
    templates["Mesh"].set_editor_property("relative_rotation",unreal.Rotator(yaw=-90))
    for slot,(variable,prop,_) in garments.items():
        templates[variable].set_editor_property("skeletal_mesh_asset",parts[slot])
    require(unreal.BlueprintEditorLibrary.compile_blueprint(bp) is True,"Playtest child compilation failed")
    pawn_class=unreal.EditorAssetLibrary.load_blueprint_class(PAWN)
    cdo=unreal.get_default_object(pawn_class)
    require(cdo.get_editor_property("mesh").get_editor_property("skeletal_mesh_asset")==body_asset,"Body default not retained")
    for slot,(_,prop,_) in garments.items():
        require(cdo.get_editor_property(prop).get_editor_property("skeletal_mesh_asset")==parts[slot],"Garment default not retained "+slot)
    require(unreal.EditorAssetLibrary.save_loaded_asset(bp,only_if_is_dirty=False),"Playtest child save failed")
    report["newAssetsSaved"].append(PAWN)
    native_gm=unreal.load_class(None,"/Script/AnomaliaPrimeval.AnomaliaGameMode")
    gm=unreal.BlueprintEditorLibrary.create_blueprint_asset_with_parent(GM,native_gm)
    require(gm is not None,"Native test GameMode creation failed")
    gm_class=unreal.BlueprintEditorLibrary.generated_class(gm)
    unreal.get_default_object(gm_class).set_editor_property("default_pawn_class",pawn_class)
    require(unreal.BlueprintEditorLibrary.compile_blueprint(gm) is True,"Native test GameMode compilation failed")
    gm_class=unreal.BlueprintEditorLibrary.generated_class(gm)
    require(unreal.EditorAssetLibrary.save_loaded_asset(gm,only_if_is_dirty=False),"Test GameMode save failed")
    report["newAssetsSaved"].append(GM)
    w=unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    require(w is not None,"New playable test world failed")
    w.get_world_settings().set_editor_property("default_game_mode",gm_class)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    floor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,-10))
    floor.static_mesh_component.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cube"))
    floor.static_mesh_component.set_collision_profile_name("BlockAll")
    floor.set_actor_scale3d(unreal.Vector(200,200,.2))
    actors.spawn_actor_from_class(unreal.PlayerStart,unreal.Vector(0,0,100))
    actors.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(0,0,600),unreal.Rotator(pitch=-45,yaw=-30))
    actors.spawn_actor_from_class(unreal.SkyLight,unreal.Vector(0,0,500))
    actors.spawn_actor_from_class(unreal.SkyAtmosphere,unreal.Vector())
    seed=actors.spawn_actor_from_class(pawn_class,unreal.Vector(500,0,100))
    inv=seed.get_editor_property("inventory_component")
    require(inv.try_add_item("apple",2) and inv.try_add_item("water",2),"Initial test inventory could not be seeded")
    saved,error=inv.save_inventory_to_player_profile(SCOPE,"local-owner")
    require(saved,"Isolated profile seed failed: "+str(error))
    require(actors.destroy_actor(seed),"Transient seed actor removal failed")
    require(unreal.EditorLoadingAndSavingUtils.save_map(w,MAP),"New playtest map save failed")
    report["newAssetsSaved"].append(MAP)
    require(editor.load_level(MAP),"Saved playtest map reload failed")
    require(worlds.get_editor_world().get_world_settings().get_editor_property("default_game_mode")==gm_class,"GameMode override did not survive reload")
    report.update(playtestMap=MAP,playtestPawn=PAWN,playtestGameMode=GM,serverScope=SCOPE,
                  fixture="new saved test assets only; native GameMode and isolated test profile",
                  clothingPersistence="CDO outfit defaults; per-player clothing choice persistence not implemented",
                  save_reconnect="map travel in same editor process only; network reconnection not tested")
    s.update(classes={"Survival":pawn_class},game_mode_class=gm_class,jacket=parts["Jacket"],parts=parts,
             garments=garments,map=MAP,scope=SCOPE)
    # Begin PIE in a transient base world, then travel with an explicit isolated URL.
    w=unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    w.get_world_settings().set_editor_property("default_game_mode",unreal.GameModeBase.static_class())
    for command in ("r.DynamicGlobalIlluminationMethod 0","r.ReflectionMethod 0",
                    "r.Shadow.Virtual.Enable 0","r.Nanite 0","sg.TextureQuality 1",
                    "r.Streaming.MipBias 1","t.MaxFPS 30","t.IdleWhenNotForeground 0"):
        unreal.SystemLibrary.execute_console_command(w,command)
    editor.editor_request_begin_play()
    s["handle"]=unreal.register_slate_post_tick_callback(tick)
except Exception as exc:
    finish(exc)
