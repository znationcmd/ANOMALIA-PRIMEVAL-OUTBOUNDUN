"""Create a NON-DESTRUCTIVE, real 3D 30-second Sequencer intro preview.

UE5.8 editor use (after cloning this branch):
  1. Open the correct AnomaliaZPrigimalia.uproject.
  2. Open an independent PREVIEW level whose name contains IntroStage.
  3. Place your actual Survivor and German Shepherd actors in that preview level.
  4. Select ONLY those two actors and execute this script in the Unreal Editor.

The script creates ONE NEW /Game/.../Cinematics/LS_... asset.
It never saves or modifies existing maps, characters, blueprints or animations.
Do not run against your real gameplay maps. No silent fallback to fake meshes.
This is a 3D Sequencer authoring step; it is NOT an MP4 render or final integration.
"""
import json
from pathlib import Path

import unreal

SEQUENCE_FOLDER = "/Game/AnomaliaZPrigimalia/Cinematics"
SEQUENCE_NAME = "LS_IntroSurvivorDog_30s"
SEQUENCE_PATH = SEQUENCE_FOLDER + "/" + SEQUENCE_NAME
FRAMES = 900
FPS = 30
ANIM_SEARCH_PATHS = (
    "/Game/Anomalia",
    "/Game/QuantumCharacter",
    "/Game/German_Shepherd_3D_Model",
    "/Game/Characters",
    "/Game/ThirdPerson",
)

def fail(message):
    raise RuntimeError("PRIGIMALIA 3D INTRO: " + message)

def skeletals(actor):
    return [c for c in actor.get_components_by_class(unreal.SkeletalMeshComponent)
            if getattr(c, "get_skeletal_mesh_asset", None)
            and c.get_skeletal_mesh_asset()]

def skeleton_of(actor):
    components = skeletals(actor)
    if not components:
        fail(f"No actual skeletal mesh loaded on {actor.get_actor_label()}")
    mesh = components[0].get_skeletal_mesh_asset()
    skeleton = mesh.get_editor_property("skeleton")
    if not skeleton:
        fail(f"Mesh has no skeleton: {mesh.get_path_name()}")
    return components[0], skeleton

def find_clips(registry, skeleton, role):
    candidates = []
    inspected = set()
    for root in ANIM_SEARCH_PATHS:
        for info in registry.get_assets_by_path(root, recursive=True):
            if str(info.asset_class_path.asset_name) != "AnimSequence":
                continue
            pkg = str(info.package_name)
            if pkg in inspected:
                continue
            inspected.add(pkg)
            name = str(info.asset_name).lower()
            priority = 0
            if "idle" in name or "breath" in name or "stand" in name:
                priority = 100
            elif "walk" in name:
                priority = 80
            elif "look" in name or "turn" in name:
                priority = 65
            else:
                continue
            if role == "dog" and "shepherd" in pkg.lower():
                priority += 20
            try:
                clip = info.get_asset()
                if not clip or clip.get_editor_property("skeleton") != skeleton:
                    continue
                seconds = float(clip.get_play_length())
                if seconds <= 0.05:
                    continue
                candidates.append((priority, seconds, pkg, clip))
            except Exception as exc:
                unreal.log_warning(f"Skipping animation {pkg}: {exc}")
    candidates.sort(key=lambda row: (-row[0], row[2]))
    return candidates

def add_actor_animation(binding, anim, start=0, end=FRAMES):
    # Editor track defaults differ by project; reuse an empty Animation Track.
    track = next((t for t in binding.get_tracks()
                  if isinstance(t, unreal.MovieSceneSkeletalAnimationTrack)), None)
    if track is None:
        track = binding.add_track(unreal.MovieSceneSkeletalAnimationTrack)
    sections = list(track.get_sections())
    section = sections[0] if sections else track.add_section()
    section.params.animation = anim
    section.set_range(start, end)
    return section

def vec(x, y, z):
    return unreal.Vector(float(x), float(y), float(z))

def move_camera(camera_binding, midpoint):
    track = next((t for t in camera_binding.get_tracks()
                  if isinstance(t, unreal.MovieScene3DTransformTrack)), None)
    if track is None:
        track = camera_binding.add_track(unreal.MovieScene3DTransformTrack)
    sections = list(track.get_sections())
    section = sections[0] if sections else track.add_section()
    section.set_range(0, FRAMES)
    channels = list(section.get_channels())
    if len(channels) < 6:
        fail("Transform camera key channels unavailable; no map was changed.")

    # Original, cinematic camera motion (units are centimeters).
    # X,Y,Z + rotation roll,pitch,yaw. Target sits between survivor and dog.
    specs = (
        (0,   -900, -450, 240, 112),
        (180, -630, -300, 170, 105),
        (360, -410, -480, 155, 100),
        (600, -570,  300, 210, 114),
        (780, -740,  170, 180, 115),
        (899, -780, -250, 210, 115),
    )
    for frame, dx, dy, dz, tz in specs:
        position = vec(midpoint.x + dx, midpoint.y + dy, midpoint.z + dz)
        target = vec(midpoint.x, midpoint.y, midpoint.z + tz)
        rot = unreal.MathLibrary.find_look_at_rotation(position, target)
        values = [position.x, position.y, position.z,
                  rot.roll, rot.pitch, rot.yaw]
        for channel, value in zip(channels[:6], values):
            channel.add_key(unreal.FrameNumber(frame), float(value))
    return track

def run():
    project = Path(str(unreal.Paths.get_project_file_path())).resolve()
    if project.name != "AnomaliaZPrigimalia.uproject":
        fail(f"Wrong project: {project}. Expected AnomaliaZPrigimalia.uproject.")
    if unreal.EditorAssetLibrary.does_asset_exist(SEQUENCE_PATH):
        fail(f"Sequence already exists: {SEQUENCE_PATH}. Refusing overwrite.")

    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not world or "intro" not in world.get_path_name().lower() or "stage" not in world.get_path_name().lower():
        fail("Open a dedicated copy of your staging level called IntroStage first; production maps are blocked.")

    actors = list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_selected_level_actors())
    if len(actors) != 2:
        fail("Select exactly two staged actors: Survivor and German Shepherd (not live gameplay actors).")
    dog = next((a for a in actors if "dog" in a.get_class().get_name().lower()
                or "shepherd" in a.get_actor_label().lower()), None)
    survivor = next((a for a in actors if a is not dog), None)
    if not dog or not survivor or dog is survivor:
        fail("Dog actor not found; check labels/classes in your IntroStage level.")

    body_mesh, body_skeleton = skeleton_of(survivor)
    dog_mesh, dog_skeleton = skeleton_of(dog)
    if body_skeleton == dog_skeleton:
        fail("Dog and survivor share one skeleton unexpectedly. Abort.")
    distance = float(unreal.MathLibrary.vector_distance(survivor.get_actor_location(),
                                                        dog.get_actor_location()))
    if distance > 1500:
        fail(f"Actors are {distance:.0f} cm apart. Reposition your preview actors together.")

    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    registry.wait_for_completion()
    survivor_clips = find_clips(registry, body_skeleton, "survivor")
    dog_clips = find_clips(registry, dog_skeleton, "dog")
    if not survivor_clips:
        fail("No compatible survivor idle/walk animation found; no placeholder added.")
    if not dog_clips:
        fail("No compatible dog idle/walk animation found; no placeholder added.")

    # All prerequisites checked BEFORE creating any new assets.
    unreal.EditorAssetLibrary.make_directory(SEQUENCE_FOLDER)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    sequence = tools.create_asset(SEQUENCE_NAME, SEQUENCE_FOLDER,
                                  unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
    if not sequence:
        fail("Failed to create LevelSequence.")
    sequence.set_display_rate(unreal.FrameRate(numerator=FPS, denominator=1))
    sequence.set_playback_start(0)
    sequence.set_playback_end(FRAMES)
    unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(sequence)
    ls = unreal.get_editor_subsystem(unreal.LevelSequenceEditorSubsystem)

    bound = ls.add_actors([survivor, dog])
    if len(bound) != 2:
        fail("Could not bind the two actors. No existing maps were saved.")
    add_actor_animation(bound[0], survivor_clips[0][3])
    add_actor_animation(bound[1], dog_clips[0][3])
    camera_binding = ls.create_camera(spawnable=True)
    if camera_binding is None:
        fail("Could not create camera in Sequencer.")
    p, d = survivor.get_actor_location(), dog.get_actor_location()
    middle = vec((p.x + d.x)/2.0, (p.y + d.y)/2.0, (p.z + d.z)/2.0)
    move_camera(camera_binding, middle)
    if not unreal.EditorAssetLibrary.save_loaded_asset(sequence, only_if_is_dirty=False):
        fail("Sequence could not be saved.")
    unreal.LevelSequenceEditorBlueprintLibrary.refresh_current_level_sequence()

    report = {
        "sequence": SEQUENCE_PATH,
        "preview_world": world.get_path_name(),
        "duration_seconds": FRAMES / FPS,
        "survivor": survivor.get_path_name(),
        "dog": dog.get_path_name(),
        "survivor_animation": survivor_clips[0][2],
        "dog_animation": dog_clips[0][2],
        "skeletons_verified": True,
        "camera_path_keyframes": 6,
        "modified_existing_maps": False,
        "rendered_mp4": False,
        "included_in_launcher": False,
        "status": "CREATED_NEEDS_UNREAL_VISUAL_REVIEW_AND_MOVIE_RENDER",
    }
    saved = Path(str(unreal.Paths.project_saved_dir())) / "Intro3D"
    saved.mkdir(parents=True, exist_ok=True)
    (saved / "intro3d_preview_audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    unreal.log("PRIGIMALIA 3D INTRO: " + json.dumps(report, ensure_ascii=False))

run()
