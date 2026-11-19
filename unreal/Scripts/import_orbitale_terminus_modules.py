"""Import the Quaternius station sector from the repository into the active project."""
import json
from pathlib import Path

import unreal

source = Path(__file__).resolve().parents[1] / "SourceAssets" / "OrbitaleTerminus17"
project = Path(unreal.Paths.project_dir()).resolve()
if project != Path("D:/ANOMALIA/unreal").resolve():
    raise RuntimeError("Expected the real ANOMALIA Unreal project.")

manifest = source / "orbitale-terminus-modules.json"
layout = json.loads(manifest.read_text(encoding="utf-8"))
tools = unreal.AssetToolsHelpers.get_asset_tools()
for asset_path in sorted({row["mesh"] for row in layout["modules"]}):
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        continue
    folder, name = asset_path.rsplit("/", 1)
    task = unreal.AssetImportTask()
    task.filename = str(source / (name + ".fbx"))
    task.destination_path = folder
    task.destination_name = name
    task.automated = True
    task.replace_existing = False
    task.save = True
    options = unreal.FbxImportUI()
    options.set_editor_property("automated_import_should_detect_type", False)
    options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
    options.set_editor_property("import_as_skeletal", False)
    options.static_mesh_import_data.set_editor_property("combine_meshes", True)
    task.options = options
    tools.import_asset_tasks([task])
    if not isinstance(unreal.EditorAssetLibrary.load_asset(asset_path), unreal.StaticMesh):
        raise RuntimeError("Model import did not produce a static mesh: " + asset_path)

destination = project / "Config/Anomalia/orbitale-terminus-modules.json"
destination.parent.mkdir(parents=True, exist_ok=True)
if destination.exists():
    unreal.log("ORBITALE keeps the installed station layout.")
else:
    with destination.open("x", encoding="utf-8") as stream:
        stream.write(manifest.read_text(encoding="utf-8"))
