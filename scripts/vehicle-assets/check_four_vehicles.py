import json
import os
from pathlib import Path
import unreal

models = {
    "cross": "/Game/Anomalia/Vehicles/dirt_bike/SM_dirt_bike.SM_dirt_bike",
    "motorcycle": "/Game/Anomalia/Vehicles/motorcycle/SM_motorcycle.SM_motorcycle",
    "scooter": "/Game/Anomalia/Vehicles/scooter/SM_scooter.SM_scooter",
    "quad": "/Game/Anomalia/Vehicles/quad/SM_quad.SM_quad",
}
sound_path = "/Game/Audio/MetaSounds/Ambient/sfx_Amb_VEH_CityMotorcycle_meta.sfx_Amb_VEH_CityMotorcycle_meta"
report = {"models": {}, "engine_sound": None}
for name, path in models.items():
    mesh = unreal.load_asset(path)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Vehicle mesh failed to load: {name} {path}")
    extent = mesh.get_bounds().box_extent
    scale = 0.1 if name == "scooter" else 1.0
    report["models"][name] = {
        "asset_loaded": True,
        "dimensions_cm": [round(2*extent.x*scale, 1), round(2*extent.y*scale, 1), round(2*extent.z*scale, 1)],
    }
sound = unreal.load_asset(sound_path)
if not sound:
    sound_path = "/Game/Audio/MetaSounds/NPC/sfx_NPC_VehEngine_Hatchback_Meta.sfx_NPC_VehEngine_Hatchback_Meta"
    sound = unreal.load_asset(sound_path)
if not sound:
    raise RuntimeError("Neither City Sample motorcycle engine sound nor the fallback loaded")
report["engine_sound"] = {"asset_loaded": True, "path": sound_path, "class": sound.get_class().get_name()}
out = Path(os.environ["ANOMALIA_VEHICLE_CHECK_OUT"])
out.mkdir(parents=True, exist_ok=True)
(out/"vehicle-runtime-check.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("VEHICLE_ASSETS_AND_ENGINE_SOUND_READY")
