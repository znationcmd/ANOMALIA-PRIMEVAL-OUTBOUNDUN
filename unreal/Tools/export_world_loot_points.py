"""Editor utility: merge explicit loot markers into the native loot layout.
Markers are ordinary actors tagged AnomaliaLootPoint, BuildingType:<type>.
Optional Category:<catalog-category>, POI:<id>. Never infers interiors.
Exports loaded actors only; call for each reviewed map region and merge by stable ID.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import unreal

SAFE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
def export(map_name, layout_file, tiers_file, catalog_files):
    if not SAFE.fullmatch(map_name):
        raise ValueError("Invalid map identity")
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    actual = str(world.get_name())
    if actual != map_name:
        raise ValueError("Loaded world does not match requested map: " + actual)
    path = Path(layout_file)
    original = path.read_bytes()
    layout = json.loads(original)
    tiers = json.loads(Path(tiers_file).read_text(encoding="utf-8-sig"))
    building_types = {b for tier in tiers["tiers"] for b in tier["buildings"]}
    categories = set()
    for catalog in catalog_files:
        categories.update(i["category"] for i in json.loads(Path(catalog).read_text(encoding="utf-8-sig"))["items"])
    by_key = {(s["map"], s["id"]): s for s in layout["spawns"]}
    if len(by_key) != len(layout["spawns"]):
        raise ValueError("Existing layout contains duplicate identities")
    added = 0
    actor_system = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in actor_system.get_all_level_actors():
        tags = [str(t) for t in actor.tags]
        if "AnomaliaLootPoint" not in tags:
            continue
        kinds = [t.split(":", 1)[1] for t in tags if t.startswith("BuildingType:")]
        if len(kinds) != 1 or kinds[0] not in building_types:
            raise ValueError("Marker needs one known BuildingType: " + actor.get_actor_label())
        cats = [t.split(":", 1)[1] for t in tags if t.startswith("Category:")]
        pois = [t.split(":", 1)[1] for t in tags if t.startswith("POI:")]
        if any(c not in categories for c in cats) or len(pois) > 1 or any(not SAFE.fullmatch(p) for p in pois):
            raise ValueError("Invalid marker category or POI")
        pos = actor.get_actor_location()
        xyz = [float(pos.x), float(pos.y), float(pos.z)]
        if any(not math.isfinite(v) or abs(v) > 2400000 for v in xyz):
            raise ValueError("Marker outside supported world bounds")
        # Actor GUID remains stable when a marker is renamed or the editor restarts.
        guid = str(actor.get_editor_property("actor_guid"))
        ident = "world-" + hashlib.sha256((map_name + ":" + guid).encode()).hexdigest()[:32]
        row = dict(id=ident, map=map_name, buildingType=kinds[0], x=xyz[0], y=xyz[1], z=xyz[2])
        if cats: row["categories"] = sorted(set(cats))
        if pois: row["poiId"] = pois[0]
        by_key[(map_name, ident)] = row
        added += 1
    if not added:
        raise ValueError("No explicit loot markers loaded; existing layout preserved")
    if len(by_key) > 512:
        raise ValueError("Native 512-point limit reached; layout preserved")
    layout["spawns"] = sorted(by_key.values(), key=lambda s: (s["map"], s["id"]))
    encoded = (json.dumps(layout, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if len(encoded) > 1024 * 1024:
        raise ValueError("Native layout size limit exceeded")
    # Backup first; atomic replacement; no deletion of unvisited regions.
    backup = path.with_name(path.name + "." + hashlib.sha256(original).hexdigest()[:12] + ".bak")
    if not backup.exists(): backup.write_bytes(original)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(encoded)
    os.replace(temporary, path)
    return {"markers_exported": added, "total_points": len(by_key),
            "coverage": "explicit loaded markers only; gameplay placement review still required"}
