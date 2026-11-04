"""Read-only inventory of persisted SKARVIK building actors for real loot-placement planning.

Loads bounded batches of existing World Partition actors, records their actual
transforms and static-mesh bounds, then unloads them. It never places loot,
changes actors, or saves any map. Exterior meshes are NOT asserted to contain
traversable interiors.
"""
import hashlib, json, os, traceback
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
REPORT = Path(os.environ["SKARVIK_BUILDING_INVENTORY_REPORT"])
MAP_PACKAGE = "/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1"
PREFIXES = (
    ("mainland", "SKARVIK_FINAL_NATIVE_GRADED_ORIGINAL_MESH_"),
    ("island", "SKARVIK_FINAL_NATIVE_ISLAND_ORIGINAL_MESH_"),
    ("citysample", "SKARVIK_FINAL_CITYSAMPLE_3D_SOURCE_"),
)
PROTECTED = (
    ROOT / "Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap",
    ROOT / "Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap",
    ROOT / "Content/Maps/PRIGIMALIA_SKARVIK_ISLANDS_v1.umap",
    Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap"),
)
doc = {
    "state": "FAILED", "readOnly": True, "mapPackage": MAP_PACKAGE,
    "lootSpawnActorsCreated": 0, "mapsSaved": False,
    "interiorsVerified": False, "exteriorMeshesAreNotInteriorProof": True,
    "counts": {}, "buildings": [], "missingMesh": [], "errors": []
}
try:
    marker = ROOT / ".skarvik-ci-stage-marker"
    if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper() or not marker.is_file() or marker.read_text(encoding="utf-8-sig").strip() != "41188816555":
        raise RuntimeError("Untrusted isolated C: staging project")
    if not all(p.is_file() for p in PROTECTED):
        raise RuntimeError("A protected SKARVIK or original map package is missing")
    before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in PROTECTED}
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level.load_level(MAP_PACKAGE):
        raise RuntimeError("Could not open the existing final SKARVIK World Partition")
    wp = unreal.WorldPartitionBlueprintLibrary
    descs = list(wp.get_actor_descs() or [])
    selected = []
    for desc in descs:
        label = str(desc.label)
        for kind, prefix in PREFIXES:
            if label.startswith(prefix):
                selected.append((kind, desc))
                break
    expected = {"mainland": 906, "island": 128, "citysample": 720}
    counts = {kind: sum(1 for k, _ in selected if k == kind) for kind, _ in PREFIXES}
    doc["counts"] = counts
    if counts != expected:
        raise RuntimeError("Persisted building actor counts differ from trusted reopen proof: " + repr(counts))
    editor_actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    batch_size = 64
    for start in range(0, len(selected), batch_size):
        batch = selected[start:start + batch_size]
        wp.load_actors([desc.guid for _, desc in batch])
        loaded = {a.get_actor_label(): a for a in editor_actors.get_all_level_actors()}
        for kind, desc in batch:
            label = str(desc.label)
            actor = loaded.get(label)
            if not actor:
                doc["errors"].append({"label": label, "reason": "actor did not load"})
                continue
            component = actor.get_component_by_class(unreal.StaticMeshComponent)
            mesh = component.get_editor_property("static_mesh") if component else None
            if not isinstance(mesh, unreal.StaticMesh):
                doc["missingMesh"].append(label)
                continue
            loc = actor.get_actor_location()
            rot = actor.get_actor_rotation()
            scale = actor.get_actor_scale3d()
            bounds = mesh.get_bounds()
            tags = sorted(str(t) for t in actor.tags)
            doc["buildings"].append({
                "kind": kind, "label": label, "mesh": mesh.get_path_name(),
                "locationCm": [round(float(loc.x), 2), round(float(loc.y), 2), round(float(loc.z), 2)],
                "rotationDeg": [round(float(rot.roll), 2), round(float(rot.pitch), 2), round(float(rot.yaw), 2)],
                "scale": [round(float(scale.x), 4), round(float(scale.y), 4), round(float(scale.z), 4)],
                "meshBoundsExtentCm": [round(float(bounds.box_extent.x), 2), round(float(bounds.box_extent.y), 2), round(float(bounds.box_extent.z), 2)],
                "tags": tags,
                "placementStatus": "EXTERIOR_OR_BUILDING_ACTOR_CANDIDATE_ONLY_INTERIOR_NOT_VERIFIED"
            })
        wp.unload_actors([desc.guid for _, desc in batch])
    for p in PROTECTED:
        if hashlib.sha256(p.read_bytes()).hexdigest() != before[str(p)]:
            raise RuntimeError("Read-only inventory altered a protected map package")
    doc["buildings"].sort(key=lambda x: (x["kind"], x["label"]))
    doc["state"] = "READ_ONLY_BUILDING_TRANSFORMS_INVENTORIED" if not doc["errors"] and not doc["missingMesh"] else "READ_ONLY_INVENTORY_PARTIAL"
    doc["sourcesUnchanged"] = True
    unreal.log("SKARVIK_BUILDING_INVENTORY_COUNTS=" + json.dumps(counts, sort_keys=True))
except Exception as exc:
    doc["error"] = str(exc)
    doc["traceback"] = traceback.format_exc()
finally:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    unreal.log("SKARVIK_BUILDING_INVENTORY_REPORT=" + str(REPORT))
