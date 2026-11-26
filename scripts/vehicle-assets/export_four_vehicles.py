import hashlib
import json
import os
import re
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
    task.options.ascii = True
    if not unreal.Exporter.run_asset_export_task(task):
        raise RuntimeError(f"FBX export task failed: {name}")
    target = Path(task.filename)
    export_scale = 0.1 if name == "scooter" else 1.0
    if name == "scooter":
        fbx = target.read_text(encoding="utf-8-sig")
        vertex_array = re.compile(r"(Vertices:\s*\*\d+\s*\{\s*a:\s*)(.*?)(\s*\})", re.DOTALL)
        scalar = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")
        arrays = list(vertex_array.finditer(fbx))
        if not arrays:
            raise RuntimeError("No FBX vertex arrays found to correct scooter scale")
        cursor = 0
        chunks = []
        for match in arrays:
            chunks.append(fbx[cursor:match.start()])
            values = scalar.findall(match.group(2))
            if not values or len(values) % 3:
                raise RuntimeError("Invalid FBX scooter vertex array")
            index = [0]
            def scale_vertex(value):
                result = float(value.group(0)) * export_scale
                index[0] += 1
                return format(result, ".9g")
            scaled = scalar.sub(scale_vertex, match.group(2))
            chunks.append(match.group(1) + scaled + match.group(3))
            cursor = match.end()
        chunks.append(fbx[cursor:])
        target.write_text("".join(chunks), encoding="utf-8")
    if not target.is_file() or target.stat().st_size < 1024:
        raise RuntimeError(f"FBX export is empty: {name}")
    report.append({
        "vehicle": name,
        "asset": path,
        "export": target.name,
        "bytes": target.stat().st_size,
        "dimensions_cm": [round(2 * bounds.x * export_scale, 1), round(2 * bounds.y * export_scale, 1), round(2 * bounds.z * export_scale, 1)],
        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
    })
(output / "exports.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("ANOMALIA_FOUR_VEHICLE_EXPORT_OK")
