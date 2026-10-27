"""Actual editor GPU views and pose observations; no PIE/network claim."""
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import time
import unreal

OUT = Path(os.environ["ANOMALIA_CHARACTER_VIEWS"])
OUT.mkdir(parents=True, exist_ok=False)
report = {"state": "FAILED", "screenshots": [], "characters": {}, "PIE": "not_run",
          "multiplayer": "not_run", "player_profile_save": "not_run", "assetsSaved": False}
state = {"index": 0, "task": None, "busy": False, "started": time.monotonic(),
         "until": time.monotonic() + 25, "poseBaseline": {}}
views = [
    ("three-characters", (450, -650, 260), (0, 0, 100)),
    ("manny", (-200, -300, 145), (-200, 0, 100)),
    ("quinn", (0, -300, 145), (0, 0, 100)),
    ("survival-outfit-front", (200, -300, 145), (200, 0, 100)),
    ("survival-outfit-back", (200, 300, 145), (200, 0, 100)),
]


def bone_positions(mesh):
    result = {}
    for name in ("pelvis", "spine_03", "hand_l"):
        t = mesh.get_bone_transform(unreal.Name(name), unreal.RelativeTransformSpace.RTS_COMPONENT).translation
        result[name] = [t.x, t.y, t.z]
    return result


def finish(error=None):
    if state.get("finishing"):
        return
    state["finishing"] = True
    if "handle" in state:
        unreal.unregister_slate_post_tick_callback(state.pop("handle"))
    if error:
        report["error"] = str(error)
    else:
        report["state"] = "REAL_EDITOR_CHARACTER_VIEWS_CAPTURED_NOT_PIE_ACCEPTANCE"
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    state["task"] = None
    gc.collect()
    unreal.SystemLibrary.quit_editor()


def camera():
    _, eye, target = views[state["index"]]
    d = [target[i] - eye[i] for i in range(3)]
    rotation = unreal.Rotator(pitch=math.degrees(math.atan2(d[2], math.hypot(*d[:2]))),
                             yaw=math.degrees(math.atan2(d[1], d[0])), roll=0)
    unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(
        unreal.Vector(*eye), rotation)


def tick(delta):
    if state["busy"] or state.get("finishing"):
        return
    try:
        if time.monotonic() - state["started"] > 360:
            raise RuntimeError("Character viewport capture timed out")
        if time.monotonic() < state["until"]:
            return
        if not state["poseBaseline"]:
            state["poseBaseline"] = {n: bone_positions(m) for n, m in state["meshes"].items()}
            state["until"] = time.monotonic() + 3
            return
        for name, mesh in state["meshes"].items():
            current = bone_positions(mesh)
            displacement = max(math.dist(current[b], state["poseBaseline"][name][b]) for b in current)
            entry = report["characters"][name]
            entry["maxObservedEditorBoneDisplacementCm"] = max(entry.get("maxObservedEditorBoneDisplacementCm", 0), displacement)
            entry["editorPoseChanged"] = entry["maxObservedEditorBoneDisplacementCm"] > .01
        name, eye, target = views[state["index"]]
        if state["task"] is None:
            state["busy"] = True
            state["task"] = unreal.AutomationLibrary.take_high_res_screenshot(
                1280, 720, str(OUT / (name + ".png")), delay=1., force_game_view=True)
            if not state["task"] or not state["task"].is_valid_task():
                raise RuntimeError("Actual character screenshot task unavailable")
            state["busy"] = False
            return
        if not state["task"].is_task_done():
            return
        image = OUT / (name + ".png")
        if not image.is_file() or image.stat().st_size < 4096:
            raise RuntimeError("Missing real screenshot: " + name)
        report["screenshots"].append({"file": image.name, "cameraCm": eye, "targetCm": target,
                                      "sha256": hashlib.sha256(image.read_bytes()).hexdigest(), "bytes": image.stat().st_size})
        state["index"] += 1
        if state["index"] == len(views):
            finish()
            return
        state["task"] = None
        camera()
        state["until"] = time.monotonic() + 8
    except Exception as exc:
        finish(exc)


try:
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level("/Game/Anomalia/CharacterTests/L_Anomalia_Characters"):
        raise RuntimeError("Saved character test map missing")
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    state["meshes"] = {}
    for actor in actors.get_all_level_actors():
        label = actor.get_actor_label()
        if not label.startswith("ANOMALIA_TEST_"):
            continue
        name = label.removeprefix("ANOMALIA_TEST_")
        mesh = actor.get_editor_property("mesh")
        mesh.set_update_animation_in_editor(True)
        mesh.set_editor_property("visibility_based_anim_tick_option", unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
        state["meshes"][name] = mesh
        body = mesh.get_editor_property("skeletal_mesh_asset")
        instance = mesh.get_anim_instance()
        entry = {"mesh": body.get_path_name(), "animationClass": str(mesh.get_editor_property("anim_class")),
                 "animationInstanceClass": instance.get_class().get_name() if instance else None, "garments": []}
        if name == "Survival":
            for prop in ("jacket_mesh", "pants_mesh", "boots_mesh", "gloves_mesh", "backpack_mesh"):
                part = actor.get_editor_property(prop)
                garment = part.get_editor_property("skeletal_mesh_asset")
                if not garment:
                    raise RuntimeError("Garment missing after map reload: " + prop)
                row = {"component": prop, "mesh": garment.get_path_name()}
                try:
                    row["leaderMatchesBody"] = part.get_editor_property("leader_pose_component") == mesh
                except Exception as exc:
                    row["leaderReadError"] = str(exc)
                entry["garments"].append(row)
        report["characters"][name] = entry
    if set(state["meshes"]) != {"Manny", "Quinn", "Survival"}:
        raise RuntimeError("Expected exactly three saved test characters")
    actors.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector())
    for command in ("r.DynamicGlobalIlluminationMethod 0", "r.ReflectionMethod 0", "r.Shadow.Virtual.Enable 0",
                    "r.Nanite 0", "r.AntiAliasingMethod 2", "sg.ShadowQuality 1", "r.ScreenPercentage 100", "t.MaxFPS 20"):
        unreal.SystemLibrary.execute_console_command(world, command)
    unreal.AutomationLibrary.set_editor_viewport_view_mode(unreal.ViewModeIndex.VMI_LIT)
    camera()
    state["handle"] = unreal.register_slate_post_tick_callback(tick)
except Exception as exc:
    finish(exc)
