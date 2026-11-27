"""Read-only Unreal Asset Registry inspection of existing ZombieFemale content on D:."""
import json, os, traceback
from pathlib import Path
import unreal

OUT = Path(os.environ["ANOMALIA_ZOMBIE_ASSET_REPORT"])
ROOT = Path(unreal.Paths.project_dir()).resolve()
PACKAGE_ROOT = "/Game/ZombieFemale/Asset"
doc = {
    "state": "FAILED",
    "projectRoot": str(ROOT),
    "packageRoot": PACKAGE_ROOT,
    "readOnly": True,
    "assets": [],
    "countsByClass": {},
    "errors": []
}
try:
    if str(ROOT).upper() != "D:\\ANOMALIA\\UNREAL":
        raise RuntimeError("Refusing to inspect an unexpected project root: " + str(ROOT))
    paths = unreal.EditorAssetLibrary.list_assets(PACKAGE_ROOT, recursive=True, include_folder=False) or []
    counts = {}
    for path in sorted(paths):
        try:
            asset = unreal.EditorAssetLibrary.load_asset(path)
            if not asset:
                doc["errors"].append({"path": path, "error": "load_asset returned None"})
                continue
            cls = asset.get_class().get_name()
            counts[cls] = counts.get(cls, 0) + 1
            row = {"path": path, "name": asset.get_name(), "class": cls}
            for field in ("skeleton", "target_skeleton", "preview_mesh", "physics_asset"):
                try:
                    value = asset.get_editor_property(field)
                    if value:
                        row[field] = value.get_path_name()
                except Exception:
                    pass
            for method in ("get_play_length", "get_number_of_frames", "get_num_frames"):
                try:
                    value = getattr(asset, method)()
                    row[method] = float(value) if method == "get_play_length" else int(value)
                except Exception:
                    pass
            doc["assets"].append(row)
        except Exception as exc:
            doc["errors"].append({"path": path, "error": str(exc)})
    doc["countsByClass"] = counts
    doc["state"] = "ZOMBIE_ASSETS_AUDITED_READONLY" if not doc["errors"] else "ZOMBIE_ASSET_AUDIT_PARTIAL"
except Exception as exc:
    doc["error"] = str(exc)
    doc["traceback"] = traceback.format_exc()
finally:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    unreal.log("ANOMALIA_ZOMBIE_ASSET_AUDIT_REPORT=" + str(OUT))
