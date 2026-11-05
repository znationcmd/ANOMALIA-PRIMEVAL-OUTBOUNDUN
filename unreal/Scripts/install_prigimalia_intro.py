"""Install the original intro clip and its separate spoken title in the CURRENT Unreal project.

Run in Unreal Editor with Python Editor Script Plugin enabled:
    Tools > Execute Python Script > unreal/Scripts/install_prigimalia_intro.py

Before running, unpack the delivery ZIP so that both media files are in
unreal/SourceAssets/Intro beside this script's parent project directory.
This script never deletes or overwrites a different existing asset/file.
"""
from pathlib import Path
import filecmp
import shutil
import unreal

movie_name = "ANOMALIAZ_PRIGIMALIA_Intro_Instrumental_30s.mp4"
voice_name = "SW_IntroTitle.wav"
project_file = Path(str(unreal.Paths.get_project_file_path())).resolve()
unreal_root = project_file.parent
source_folder = unreal_root / "SourceAssets" / "Intro"
movie_source = source_folder / movie_name
voice_source = source_folder / voice_name
movie_target = Path(str(unreal.Paths.project_content_dir())).resolve() / "Movies" / movie_name
voice_asset = "/Game/AnomaliaZPrigimalia/Branding/SW_IntroTitle"

if project_file.name != "AnomaliaZPrigimalia.uproject":
    raise RuntimeError(f"Wrong Unreal project: {project_file}. No modifications applied.")
for source in (movie_source, voice_source):
    if not source.is_file() or source.stat().st_size <= 0:
        raise RuntimeError(f"Required media missing: {source}. No modifications applied.")
if movie_target.is_file() and not filecmp.cmp(movie_source, movie_target, shallow=False):
    raise RuntimeError(f"Existing movie differs; refusing to overwrite: {movie_target}")
if unreal.EditorAssetLibrary.does_asset_exist(voice_asset):
    unreal.log_warning(f"Existing title voice preserved: {voice_asset}")
    voice_is_present = True
else:
    voice_is_present = False

movie_target.parent.mkdir(parents=True, exist_ok=True)
if not movie_target.exists():
    shutil.copy2(movie_source, movie_target)
    unreal.log(f"PRIGIMALIA intro movie staged: {movie_target}")
else:
    unreal.log(f"PRIGIMALIA intro movie already installed: {movie_target}")

if not voice_is_present:
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(voice_source))
    task.set_editor_property("destination_path", "/Game/AnomaliaZPrigimalia/Branding")
    task.set_editor_property("destination_name", "SW_IntroTitle")
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", False)
    task.set_editor_property("save", True)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    if not unreal.EditorAssetLibrary.does_asset_exist(voice_asset):
        raise RuntimeError("Voice import failed: SW_IntroTitle SoundWave was not created.")

unreal.log(
    "PRIGIMALIA_INTRO_MEDIA_READY: movie+title voice available. "
    "Compile the new intro C++ branch and launch ANOMALIA_Playable_v1 in standalone. "
    "The real animated 3D sequence still requires explicit engine work and rig validation."
)
