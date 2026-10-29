"""Run in Unreal's Python editor on a copied ANOMALIA district map.
Updates placed mesh components only; never modifies source meshes or textures.
The caller must supply a working map under /Game/Anomalia/Maps/.
"""
import json
import unreal

def apply_to_working_district(map_path, report_path):
    if not map_path.startswith("/Game/Anomalia/Maps/"):
        raise ValueError("Use an ANOMALIA working map; original City Sample is protected")
    if not unreal.EditorAssetLibrary.does_asset_exist(map_path):
        raise ValueError("Working district does not exist")
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level(map_path):
        raise RuntimeError("Could not load working district")
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    report = {"map": map_path, "status": "applied_not_benchmarked",
              "changed": [], "errors": [], "not_created": ["interiors", "interactive doors", "loot"]}
    # Distances in centimetres. Building silhouettes remain visible much farther
    # than small dressing; no mesh/texture source asset is edited.
    with unreal.ScopedEditorTransaction("ANOMALIA district visibility budget"):
        for actor in actors.get_all_level_actors():
            label = actor.get_actor_label().lower()
            # Dressing is opt-in through explicit actor tags, never name guesses.
            tags = {str(tag) for tag in actor.tags}
            category = next((t for t in ("Anomalia.SmallDebris", "Anomalia.StreetProp",
                                         "Anomalia.Vegetation", "Anomalia.Building") if t in tags), None)
            if category is None:
                continue
            distance = {"Anomalia.SmallDebris": 3500.0,
                        "Anomalia.StreetProp": 10000.0,
                        "Anomalia.Vegetation": 15000.0,
                        "Anomalia.Building": 80000.0}[category]
            for component in actor.get_components_by_class(unreal.StaticMeshComponent):
                try:
                    component.set_cull_distance(distance)
                    if category == "Anomalia.SmallDebris":
                        component.set_cast_shadow(False)
                    report["changed"].append({"actor": actor.get_actor_label(),
                                               "category": category, "distance_cm": distance})
                except Exception as error:
                    report["errors"].append({"actor": label, "error": str(error)})
    if report["errors"]:
        report["status"] = "partial_not_saved"
    elif not report["changed"]:
        report["status"] = "no_tagged_actors_no_changes"
    else:
        if not levels.save_current_level():
            raise RuntimeError("Could not save working district")
    with open(report_path, "w", encoding="utf-8") as output:
        json.dump(report, output, ensure_ascii=False, indent=2)
    return report
