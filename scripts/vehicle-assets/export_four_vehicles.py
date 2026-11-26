import hashlib
import json
import os
from pathlib import Path
import unreal

output = Path(os.environ["VEHICLE_EXPORT_OUT"])
models = (
    ("dirt_bike", "/Game/Anomalia/Vehicles/dirt_bike/SM_dirt_bike.SM_dirt_bike"),
    ("motorcycle", "/Game/Anomalia/Vehicles/motorcycle/SM_motorcycle.SM_motorcycle"),
    ("scooter", "/Game/Anomalia/Vehicles/scooter/SM_scooter.SM_scooter"),
    ("quad", "/Game/Anomalia/Vehicles/quad/SM_quad.SM_quad"),
)
report = []
for name, path in models:
    mesh = unreal.load_asset(path)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Native static mesh could not be loaded: {path}")
    bounds = mesh.get_bounds().box_extent
    task = unreal.AssetExportTask()
    task.object = mesh
    task.filename = str(output / f"ANOMALIA_{name}.fbx")
    task.automated = True
    task.prompt = False
    task.replace_identical = True
    task.options = unreal.FbxExportOption()
    task.options.ascii = False
    task.options.export_materials = True
    if not unreal.Exporter.run_asset_export_task(task):
        raise RuntimeError(f"FBX export task failed: {name}")
    target = Path(task.filename)
    if not target.is_file() or target.stat().st_size < 1024:
        raise RuntimeError(f"FBX export is empty: {name}")
    report.append({
        "vehicle": name,
        "asset": path,
        "export": target.name,
        "bytes": target.stat().st_size,
        "dimensions_cm": [round(2 * bounds.x, 1), round(2 * bounds.y, 1), round(2 * bounds.z, 1)],
        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
    })
(output / "exports.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("ANOMALIA_FOUR_VEHICLE_EXPORT_OK")
