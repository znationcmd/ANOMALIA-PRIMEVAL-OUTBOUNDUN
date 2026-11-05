"""Install ANOMALIA'Z PRIGIMALIA 88-second text-free horror intro v4 and click-only blood scene.

Execute from the actual Unreal Editor's Python scripting console:
    py unreal/Scripts/install_prigimalia_intro.py
or via Tools > Execute Python Script.

Extract the independent media pack into `unreal/SourceAssets/Intro/`
on the machine with Unreal Engine 5.8 first.

This intentionally uses distinct v4 file / asset names so it cannot
replace the user's v1 intro or any live map, vehicle or player save.
"""
from pathlib import Path
import filecmp
import shutil
import unreal

movie_names = (
    "ANOMALIAZ_PRIGIMALIA_Intro_SANS_TEXTE_88s.mp4",
    "ANOMALIAZ_PRIGIMALIA_Clic_Sang_SANS_TEXTE_v4.mp4",
)
voice_name = "SW_IntroTitle_Zombie_v4.wav"
voice_object_name = "SW_IntroTitle_Zombie_v4"
voice_asset = "/Game/AnomaliaZPrigimalia/Branding/" + voice_object_name
project_file = Path(str(unreal.Paths.get_project_file_path())).resolve()
root = project_file.parent
source_folder = root / "SourceAssets" / "Intro"
movies_folder = Path(str(unreal.Paths.project_content_dir())).resolve() / "Movies"

if project_file.name != "AnomaliaZPrigimalia.uproject":
    raise RuntimeError(f"Wrong Unreal project: {project_file}. No modifications applied.")

# Preflight ALL files before making any project changes.
for filename in (*movie_names, voice_name):
    path = source_folder / filename
    if not path.is_file() or path.stat().st_size < 1024:
        raise RuntimeError(f"Required 88-second intro media missing: {path}. No modifications applied.")

for name in movie_names:
    source = source_folder / name
    target = movies_folder / name
    if target.is_file() and not filecmp.cmp(source, target, shallow=False):
        raise RuntimeError(f"Different movie already installed: {target}. Refusing overwrite.")

if unreal.EditorAssetLibrary.does_asset_exist(voice_asset):
    unreal.log_warning(f"Deep title voice already imported; preserved: {voice_asset}")
    voice_imported = True
else:
    voice_imported = False

movies_folder.mkdir(parents=True, exist_ok=True)
for name in movie_names:
    source = source_folder / name
    target = movies_folder / name
    if not target.exists():
        shutil.copy2(source, target)
        unreal.log(f"PRIGIMALIA horror media installed: {target}")
    else:
        unreal.log(f"PRIGIMALIA horror media already installed: {target}")

if not voice_imported:
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(source_folder / voice_name))
    task.set_editor_property("destination_path", "/Game/AnomaliaZPrigimalia/Branding")
    task.set_editor_property("destination_name", voice_object_name)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", False)
    task.set_editor_property("save", True)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    if not unreal.EditorAssetLibrary.does_asset_exist(voice_asset):
        raise RuntimeError("Deep title voice import did not create its SoundWave.")

unreal.log(
    "PRIGIMALIA_HORROR_V2_MEDIA_READY: 88-second no-text intro with ORIGINAL horror soundtrack, "
    "silent bleeding title movie and deep title voice prepared. "
    "C++ compilation + packaged Windows test still required."
)
