"""Native, non-destructive verification of staged ANOMALIA'Z PRIGIMALIA assets.

Never treat a successful World Partition builder exit as sufficient proof:
all planned target map packages must actually reload as Unreal World objects.
Only after passing the checks may this script finalize the migration receipt
used by the staged textual-reference updater. No uasset/umap is renamed here.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir()).resolve()
project = Path(unreal.Paths.get_project_file_path()).resolve()
actual = str(root).replace("/", "\\").rstrip("\\").lower()
expected = r"d:\anomaliaz-prigimalia\unreal"
reportdir = root / "Saved" / "BrandMigration"
checkpoint_path = reportdir / "asset-rename-report.json"
marker_path = reportdir / "verified-source-backup.marker"
original_path = Path(r"D:\ANOMALIA\unreal\AnomaliaPrimeval.uproject")
relief_receipt_path = reportdir / "relief-builder-report.json"

def fail(message):
    raise RuntimeError("PRIGIMALIA_NATIVE_VERIFICATION_FAILED: " + message)

if actual != expected or project.stem != "AnomaliaZPrigimalia":
    fail("Refusing to run outside the exact isolated staging directory")
if not marker_path.is_file() or not original_path.is_file():
    fail("Staged backup marker or original project missing")
if not checkpoint_path.is_file():
    fail("No prior Unreal migration checkpoint; refusing to invent a proof")

checkpoint_bytes = checkpoint_path.read_bytes()
try:
    checkpoint = json.loads(checkpoint_bytes.decode("utf-8-sig"))
except (ValueError, UnicodeError) as exc:
    fail("Unreadable original native migration checkpoint: " + str(exc))

if checkpoint.get("project") != project.name:
    fail("Checkpoint belongs to another .uproject")
if checkpoint.get("stagedCopyConfirmed") is not True:
    fail("Checkpoint does not certify staged project")
if checkpoint.get("directoryRenamed") is not True:
    fail("Legacy asset-directory migration not confirmed")

legacy_count = int(checkpoint.get("legacyAssetsFound") or 0)
new_dir = "/Game/AnomaliaZPrigimalia"
old_dir = "/Game/Anomalia"
asset_api = unreal.EditorAssetLibrary
unreal.AssetRegistryHelpers.get_asset_registry().wait_for_completion()
if not asset_api.does_directory_exist(new_dir):
    fail("Renamed native assets directory does not exist")

migrated = list(asset_api.list_assets(new_dir, recursive=True, include_folder=False))
if legacy_count <= 0 or len(migrated) < legacy_count:
    fail("Renamed asset count is smaller than verified legacy inventory: "
         + str(len(migrated)) + " / " + str(legacy_count))

plan = checkpoint.get("mapRenamePlan") or []
confirmed = checkpoint.get("mapsRenamed") or []
if not plan:
    fail("No native map rename plan found; refuse blind packaging")

all_pairs = {}
for item in plan + confirmed:
    old = item.get("old", "")
    new = item.get("new", "")
    if not (old.startswith("/Game/") and new.startswith("/Game/")
            and old != new and "." not in old.rsplit("/", 1)[-1]
            and "." not in new.rsplit("/", 1)[-1]):
        fail("Malformed map pair in native checkpoint: " + repr(item))
    if old in all_pairs and all_pairs[old] != new:
        fail("Conflicting target packages for " + old)
    all_pairs[old] = new

if "/Game/ANOMALIA_Relief_Test" in all_pairs:
    if not relief_receipt_path.is_file():
        fail("World Partition Relief builder receipt missing")
    receipt = json.loads(relief_receipt_path.read_text(encoding="utf-8-sig"))
    if not (receipt.get("exitCode") == 0
            and receipt.get("targetPresent") is True
            and receipt.get("originalPreserved") is True
            and receipt.get("new") == all_pairs["/Game/ANOMALIA_Relief_Test"]):
        fail("Relief builder result not trustworthy")

# Native WorldPartitionRenameDuplicateBuilder crashed (access violation)
# specifically on ANOMALIA_Playable_v1. Do NOT retry that destructive rename.
# Preserve and actually load the original map package as a compatibility path,
# without claiming its rename has completed. Never broaden this exception.
LEGACY_WP_MAP = "/Game/Maps/ANOMALIA_Playable_v1"
LEGACY_WP_TARGET = "/Game/Maps/PRIGIMALIA_Playable_v1"
verified_maps = []
preserved_maps = []
for old, new in sorted(all_pairs.items()):
    current = new
    if not asset_api.does_asset_exist(new):
        if old != LEGACY_WP_MAP or new != LEGACY_WP_TARGET:
            fail("Missing migrated map package: " + new + " (original: " + old + ")")
        original_file = root / "Content" / "Maps" / "ANOMALIA_Playable_v1.umap"
        target_file = root / "Content" / "Maps" / "PRIGIMALIA_Playable_v1.umap"
        if not original_file.is_file() or target_file.exists():
            fail("Playable-v1 original map missing or partial target collision")
        if not asset_api.does_asset_exist(old):
            fail("Preserved playable-v1 map is not registered as an Unreal asset")
        current = old
    loaded = unreal.load_asset(current)
    if loaded is None or not isinstance(loaded, unreal.World):
        fail("Unreal cannot reload verified World: " + current)
    rel = current.removeprefix("/Game/") + ".umap"
    if not (root / "Content" / rel).is_file():
        fail("Reloaded World package missing in staged Content: " + current)
    if current == old:
        preserved_maps.append({
            "old": old, "plannedNew": new, "actual": old,
            "verified": True,
            "reason": "World Partition builder crashed; exact original map retained"
        })
    else:
        verified_maps.append({"old": old, "new": new})

if len(verified_maps) + len(preserved_maps) != len(all_pairs):
    fail("The verified-map count does not match the original rename plan")
if len(preserved_maps) > 1:
    fail("Unexpected additional legacy map preservation")

# Keep the earlier failed checkpoint byte-for-byte for audit. Never overwrite
# that evidence if there is a different file already at the backup location.
backup = reportdir / "asset-rename-before-native-revalidation.json"
if backup.exists():
    saved_checkpoint = backup.read_bytes()
    if saved_checkpoint != checkpoint_bytes:
        saved_hash = hashlib.sha256(saved_checkpoint).hexdigest()
        if not (checkpoint.get("nativeReloadVerified") is True
                and checkpoint.get("priorCheckpointSHA256") == saved_hash):
            fail("A different immutable prior checkpoint backup already exists")
else:
    backup.write_bytes(checkpoint_bytes)

prior_hash = hashlib.sha256(backup.read_bytes()).hexdigest()
result = dict(checkpoint)
result.update({
    "mapRenamePlan": [{"old": old, "new": new} for old, new in sorted(all_pairs.items())],
    "mapsRenamed": verified_maps,
    "mapsPreservedAtOriginalPath": preserved_maps,
    "allMapRenamesComplete": len(preserved_maps) == 0,
    "compatibilityMapVerified": bool(preserved_maps),
    "cookMapPackages": [item["new"] for item in verified_maps]
                       + [item["actual"] for item in preserved_maps],
    "remainingLegacyPathsIncludingRedirectors": len(asset_api.list_assets(
        old_dir, recursive=True, include_folder=False
    )) if asset_api.does_directory_exist(old_dir) else 0,
    "verified": True,
    "errors": [],
    "nativeReloadVerified": True,
    "validationMethod": "UE5.8-Unreal-AssetRegistry-and-World-load",
    "validatedMaps": len(verified_maps) + len(preserved_maps),
    "validatedAssets": len(migrated),
    "originalProjectPreserved": original_path.is_file(),
    "validationUtc": datetime.now(timezone.utc).isoformat(),
    "priorCheckpointSHA256": prior_hash,
})
temp = reportdir / "asset-rename-report.validated.tmp"
temp.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
temp.replace(checkpoint_path)
unreal.log("PRIGIMALIA_NATIVE_ASSETS_AND_MAPS_RELOADED=true")
unreal.log("PRIGIMALIA_NATIVE_MIGRATION_VERIFIED=true")
unreal.log("PRIGIMALIA_VERIFIED_MAP_COUNT=" + str(len(verified_maps)))
