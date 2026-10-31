"""Read-only Unreal Engine 5.8 map asset loading audit on the ISOLATED Windows stage.

Do not call save, import, rename, move, delete, or spawn any assets. The only
output is a JSON report beneath RUNNER_TEMP. World load is NOT a gameplay test.
"""
import gc
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import unreal

inventory_path = Path(os.environ["ANOMALIA_MAP_AUDIT_INVENTORY"])
output_path = Path(os.environ["ANOMALIA_MAP_AUDIT_NATIVE"])
actual_root = str(Path(unreal.Paths.project_dir()).resolve()).replace("/", "\\").rstrip("\\").lower()
expected_root = r"d:\anomaliaz-prigimalia\unreal"
if actual_root != expected_root:
    raise RuntimeError(f"Refuse to audit wrong or original UE project: {actual_root}")
inventory = json.loads(inventory_path.read_text(encoding="utf-8-sig"))
if len(inventory["maps"]) != 10:
    raise RuntimeError("Map inventory count mismatch")

registry = unreal.AssetRegistryHelpers.get_asset_registry()
registry.wait_for_completion()
result = {
    "auditMode": "UE5.8-native-world-asset-load-readonly",
    "projectRoot": actual_root,
    "timestampUtc": datetime.now(timezone.utc).isoformat(),
    "gameplayTested": False,
    "landscapeComponentsRechecked": False,
    "worldPartitionStreamed": False,
    "maps": [],
}
try:
    for item in inventory["maps"]:
        matches = item["projects"]["stage"]["nativeFiles"]
        rows = []
        for m in matches:
            package = m["package"]
            row = {"package": package, "bytes": m["bytes"], "registered": False, "worldLoaded": False}
            try:
                row["registered"] = bool(unreal.EditorAssetLibrary.does_asset_exist(package))
                if row["registered"]:
                    obj = unreal.load_asset(package)
                    row["worldLoaded"] = bool(obj and isinstance(obj, unreal.World))
                    row["loadedClass"] = obj.get_class().get_name() if obj else None
                    del obj
                else:
                    row["error"] = "Native map file present but asset not registered"
            except Exception as exc:
                row["error"] = str(exc)
            rows.append(row)
            gc.collect()
        result["maps"].append({
            "id": item["id"],
            "displayName": item["displayName"],
            "expectedPackage": item["configuredPackage"],
            "nativeFilesPresent": len(matches),
            "nativeWorldLoads": sum(bool(row["worldLoaded"]) for row in rows),
            "targets": rows,
        })
        unreal.log("ANOMALIA_10_MAP_NATIVE_RELOAD " + item["displayName"] + " " +
                   str(sum(bool(row["worldLoaded"]) for row in rows)) + "/" + str(len(rows)))
finally:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    unreal.log("ANOMALIA_10_MAP_NATIVE_AUDIT_REPORT=" + str(output_path))
