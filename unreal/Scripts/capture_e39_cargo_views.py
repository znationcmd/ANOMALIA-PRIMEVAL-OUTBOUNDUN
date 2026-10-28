"""Real GPU editor views of unchanged v7 art; preview poses, not gameplay tests."""
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import time
import unreal

OUT = Path(os.environ["ANOMALIA_E39_CARGO_VIEWS"])
OUT.mkdir(parents=True, exist_ok=False)
report = {"state": "FAILED", "screenshots": [], "gameplayTested": False,
          "multiplayerTested": False, "sourceArtModified": False, "mapSaved": False,
          "poseMethod": "Static editor preview at authored pivot; no server interaction"}
state = {"index": 0, "task": None, "busy": False, "started": time.monotonic(),
         "until": time.monotonic() + 30}
views = [
    ("closed-rear", (-380, 0, 154), (-205, 0, 85), 0),
    ("open-rear-eye-height", (-380, 0, 154), (-205, 0, 80), 65),
    ("open-oblique", (-310, -150, 170), (-205, 0, 75), 65),
    ("open-overhead", (-235, -90, 215), (-205, 0, 65), 65),
]


def finish(error=None):
    if state.get("finishing"):
        return
    state["finishing"] = True
    if "handle" in state:
        unreal.unregister_slate_post_tick_callback(state.pop("handle"))
    if error:
        report["error"] = str(error)
    else:
        report["state"] = "REAL_GPU_CARGO_PREVIEW_CAPTURED_NOT_GAMEPLAY_ACCEPTANCE"
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    state["task"] = None
    gc.collect()
    unreal.SystemLibrary.quit_editor()


def set_view():
    name, eye, target, angle = views[state["index"]]
    # This is an explicitly labelled static art preview. Runtime opening already
    # has separate native v7 evidence; this must never count as another RPC test.
    state["trunk"].set_actor_rotation(unreal.Rotator(pitch=-angle, yaw=0, roll=0), False)
    delta = [target[i] - eye[i] for i in range(3)]
    rotation = unreal.Rotator(pitch=math.degrees(math.atan2(delta[2], math.hypot(*delta[:2]))),
                             yaw=math.degrees(math.atan2(delta[1], delta[0])), roll=0)
    unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(
        unreal.Vector(*eye), rotation)


def tick(delta):
    if state["busy"] or state.get("finishing"):
        return
    try:
        if time.monotonic() - state["started"] > 360:
            raise RuntimeError("Cargo preview capture timed out")
        if time.monotonic() < state["until"]:
            return
        name, eye, target, angle = views[state["index"]]
        if state["task"] is None:
            state["busy"] = True
            state["task"] = unreal.AutomationLibrary.take_high_res_screenshot(
                1280, 720, str(OUT / (name + ".png")), delay=1., force_game_view=True)
            if not state["task"] or not state["task"].is_valid_task():
                raise RuntimeError("Actual viewport screenshot task unavailable")
            state["busy"] = False
            return
        if not state["task"].is_task_done():
            return
        image = OUT / (name + ".png")
        if not image.is_file() or image.stat().st_size < 4096:
            raise RuntimeError("Missing real viewport image: " + name)
        report["screenshots"].append({"file": image.name, "cameraCm": eye, "targetCm": target,
                                      "previewAngleDegrees": angle, "bytes": image.stat().st_size,
                                      "sha256": hashlib.sha256(image.read_bytes()).hexdigest()})
        state["index"] += 1
        if state["index"] == len(views):
            finish()
            return
        state["task"] = None
        set_view()
        state["until"] = time.monotonic() + 8
    except Exception as exc:
        finish(exc)


try:
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    manifest_path = Path(unreal.Paths.project_dir()) / "SourceAssets/BMWE39Review_v7/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["source"]["sha256"] != "984a9daab49b5a31c45bbc284c657fa5898a010f2201c003358cb6b6f411751d":
        raise RuntimeError("Original reviewed Black Snow E39 identity required")
    meshes = {}
    for model in manifest["models"]:
        mesh = unreal.load_asset(model["objectPath"])
        if not isinstance(mesh, unreal.StaticMesh):
            raise RuntimeError("Installed v7 mesh missing: " + model["id"])
        if unreal.EditorAssetLibrary.get_metadata_tag(mesh, "AnomaliaNativeSedanSha256") != model["sha256"]:
            raise RuntimeError("Installed v7 mesh identity mismatch: " + model["id"])
        meshes[model["id"]] = mesh
    world = unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    pivots = {p["id"]: p["pivotCm"] for p in manifest["panels"]}
    hubs = dict(zip(("wheel_fl", "wheel_fr", "wheel_rl", "wheel_rr"), manifest["wheelHubsCm"]))
    for model in manifest["models"]:
        name = model["id"]
        actor = actors.spawn_actor_from_class(unreal.StaticMeshActor,
                                             unreal.Vector(*(pivots.get(name) or hubs.get(name) or (0, 0, 0))))
        actor.set_actor_label("E39_CARGO_PREVIEW_" + name)
        actor.static_mesh_component.set_static_mesh(meshes[name])
        if name == "trunk":
            state["trunk"] = actor
    ground = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, -55))
    ground.static_mesh_component.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cube"))
    ground.set_actor_scale3d(unreal.Vector(30, 30, 1))
    sun = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 1000))
    sun.set_actor_rotation(unreal.Rotator(pitch=-45, yaw=-35), False)
    actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 1000))
    actors.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector())
    for command in ("r.DynamicGlobalIlluminationMethod 0", "r.ReflectionMethod 0",
                    "r.Shadow.Virtual.Enable 0", "r.Nanite 0", "r.AntiAliasingMethod 2",
                    "sg.ShadowQuality 1", "r.ScreenPercentage 100", "t.MaxFPS 20"):
        unreal.SystemLibrary.execute_console_command(world, command)
    unreal.AutomationLibrary.set_editor_viewport_view_mode(unreal.ViewModeIndex.VMI_LIT)
    report.update(source=manifest["source"], namespace="BMWE39Review_v7",
                  modelHashes={m["id"]: m["sha256"] for m in manifest["models"]})
    set_view()
    state["handle"] = unreal.register_slate_post_tick_callback(tick)
except Exception as exc:
    finish(exc)
