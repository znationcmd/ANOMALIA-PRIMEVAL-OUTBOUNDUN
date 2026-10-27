"""Spawn/reload test actors in a new map; no claim of PIE or rendered validation."""
import json
import os
from pathlib import Path
import uuid
import unreal

ROOT = "/Game/Anomalia/Characters"
MAP = "/Game/Anomalia/CharacterTests/L_Anomalia_Characters"
NAMES = ("Manny", "Quinn", "Survival")
SURVIVAL = "/Game/Survival_Character/Meshes/Modular_Parts/SK_Survival_Character_"
GARMENTS = {"Jacket": ("jacket_mesh", "Jacket"), "Pants": ("pants_mesh", "Jeans"),
            "Boots": ("boots_mesh", "Shoes"), "Gloves": ("gloves_mesh", "Gloves"),
            "Backpack": ("backpack_mesh", "Backpack")}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    report = {"engine": unreal.SystemLibrary.get_engine_version(), "actors": [],
              "clothing": [], "errors": [], "PIE": "not_run", "render": "not_run",
              "multiplayer": "not_run", "player_profile_save": "not_run"}
    try:
        require(os.environ.get("ANOMALIA_CREATE_TEST_SCENE") == "1", "Explicit scene creation mode required")
        require(not unreal.EditorAssetLibrary.does_asset_exist(MAP), "Existing map preserved: " + MAP)
        gm_path = "/Game/Anomalia/CharacterTests/GM_Anomalia_CharacterTests"
        require(not unreal.EditorAssetLibrary.does_asset_exist(gm_path), "Existing test GameMode preserved")
        classes = {n: unreal.EditorAssetLibrary.load_blueprint_class(ROOT + "/BP_Anomalia_" + n) for n in NAMES}
        require(all(classes.values()), "All three test Blueprints must already exist")
        parent = unreal.load_class(None, "/Script/AnomaliaPrimeval.AnomaliaSurvivor")
        for name in NAMES:
            bp = unreal.load_asset(ROOT + "/BP_Anomalia_" + name)
            require(unreal.BlueprintEditorLibrary.get_blueprint_parent_class(bp) == parent, "Wrong native parent: " + name)
        world = unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
        require(world is not None, "New test world failed")
        subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        floor = subsystem.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, -10))
        require(floor is not None, "Test floor spawn failed")
        floor.static_mesh_component.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cube"))
        floor.set_actor_scale3d(unreal.Vector(40, 40, .2))
        floor.set_actor_label("ANOMALIA test floor")
        subsystem.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 500), unreal.Rotator(pitch=-45, yaw=-30))
        subsystem.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 400))
        subsystem.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(0, -500, 100))
        actors = {}
        for index, name in enumerate(NAMES):
            actor = subsystem.spawn_actor_from_class(classes[name], unreal.Vector(index * 200 - 200, 0, 100))
            require(actor is not None, "Actor spawn failed: " + name)
            actor.set_actor_label("ANOMALIA_TEST_" + name)
            mesh = actor.get_editor_property("mesh")
            body = mesh.get_editor_property("skeletal_mesh_asset")
            anim = mesh.get_editor_property("anim_class")
            require(body is not None and anim is not None, "Missing saved body/animation: " + name)
            require(actor.get_editor_property("inventory_component") is not None, "Missing actual inventory: " + name)
            require(actor.get_editor_property("vitals_component") is not None, "Missing actual vitals: " + name)
            require(actor.get_editor_property("follow_camera") is not None, "Missing actual camera: " + name)
            require(actor.get_editor_property("capsule_component").get_scaled_capsule_half_height() > 0, "Missing capsule: " + name)
            report["actors"].append({"name": name, "mesh": body.get_path_name(), "animation": anim.get_path_name(),
                                      "inventory_component": True, "vitals_component": True, "camera": True, "capsule": True})
            actors[name] = actor
        survivor = actors["Survival"]
        if hasattr(survivor, "set_clothing_mesh"):
            for slot, (property_name, suffix) in GARMENTS.items():
                garment = unreal.load_asset(SURVIVAL + suffix)
                require(garment is not None, "Missing garment " + suffix)
                require(survivor.set_clothing_mesh(slot, garment), "Garment rejected: " + slot)
                component = survivor.get_editor_property(property_name)
                require(component.get_editor_property("skeletal_mesh_asset") == garment, "Garment not applied: " + slot)
                require(survivor.set_clothing_mesh(slot, None), "Removal rejected: " + slot)
                require(component.get_editor_property("skeletal_mesh_asset") is None, "Garment not removed: " + slot)
                require(survivor.set_clothing_mesh(slot, garment), "Re-equip rejected: " + slot)
                report["clothing"].append({"slot": slot, "apply_remove_reapply": "passed", "visual": "not_verified"})
            wrong = unreal.load_asset("/Game/QuantumCharacter/Mesh/Modules/SKM_Jeans")
            require(not survivor.set_clothing_mesh("Pants", wrong), "Mismatched Quantum garment accepted")
            report["mismatched_skeleton_rejected"] = True
        else:
            report["clothing_blocker"] = "Installed native Survivor has no clothing API; source migration required"
        gm = unreal.BlueprintEditorLibrary.create_blueprint_asset_with_parent(gm_path, unreal.GameModeBase)
        require(gm is not None, "Test GameMode creation failed")
        gm_class = unreal.BlueprintEditorLibrary.generated_class(gm)
        unreal.get_default_object(gm_class).set_editor_property("default_pawn_class", classes["Manny"])
        require(unreal.BlueprintEditorLibrary.compile_blueprint(gm) is True, "Test GameMode compilation failed")
        require(unreal.get_default_object(unreal.BlueprintEditorLibrary.generated_class(gm)).get_editor_property("default_pawn_class") == classes["Manny"], "Test pawn class did not persist")
        require(unreal.EditorAssetLibrary.save_loaded_asset(gm, only_if_is_dirty=False), "Test GameMode save failed")
        world.get_world_settings().set_editor_property("default_game_mode", unreal.BlueprintEditorLibrary.generated_class(gm))
        require(unreal.EditorLoadingAndSavingUtils.save_map(world, MAP), "New map save failed")
        report["map_saved"] = MAP
        loaded = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
        require(loaded is not None, "New map reload failed")
        labels = {a.get_actor_label() for a in subsystem.get_all_level_actors()}
        require(all("ANOMALIA_TEST_" + n in labels for n in NAMES), "Actors missing after map reload")
        report["map_reloaded"] = True
        report["test_game_mode"] = gm_path
    except Exception as exc:
        report["errors"].append(str(exc))
        raise
    finally:
        folder = Path(unreal.Paths.project_saved_dir()) / "CharacterAudit"
        folder.mkdir(parents=True, exist_ok=True)
        with (folder / ("scene-" + uuid.uuid4().hex + ".json")).open("x", encoding="utf-8") as output:
            json.dump(report, output, indent=2)
        unreal.log("ANOMALIA_SCENE_REPORT " + json.dumps(report))


if __name__ == "__main__":
    main()
