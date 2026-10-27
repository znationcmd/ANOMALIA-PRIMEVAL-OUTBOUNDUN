"""ANOMALIA: create an editable playable survivor Blueprint from installed Fab assets.
Run in Unreal Editor: Tools > Execute Python Script (enable Python Editor Script Plugin).
Does not redistribute Fab assets or overwrite existing Blueprints.
"""
import unreal

ROOT = "/Game"
OUT = "/Game/Anomalia/Characters"
NAME = "BP_AnomaliaSurvivor_Fab"

def log(message):
    unreal.log("[ANOMALIA Character] " + str(message))

def find_meshes():
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    assets = registry.get_assets_by_class(unreal.TopLevelAssetPath("/Script/Engine", "SkeletalMesh"), True)
    return [a for a in assets if str(a.package_name).startswith(ROOT)]

def choose_mesh(assets):
    # Prefer the actual Fab survival character if installed, then Quantum, then Manny.
    priorities = [
        ("survival", "character"),
        ("quantumcharacter", "skm_quantum_character"),
        ("controlrig", "skm_manny"),
    ]
    for words in priorities:
        matches = [a for a in assets if all(w in str(a.package_name).lower() for w in words)]
        if matches:
            return unreal.load_asset(str(matches[0].package_name))
    return None

def main():
    assets = find_meshes()
    mesh = choose_mesh(assets)
    if not mesh:
        raise RuntimeError("No compatible SkeletalMesh found. Verify Fab import and Manny/Quantum assets.")
    survivor_class = unreal.load_class(None, "/Script/AnomaliaPrimeval.AnomaliaSurvivor")
    if not survivor_class:
        raise RuntimeError("Compile AnomaliaPrimeval C++ module before running this script.")
    unreal.EditorAssetLibrary.make_directory(OUT)
    target = OUT + "/" + NAME
    if unreal.EditorAssetLibrary.does_asset_exist(target):
        log("Existing Blueprint kept unchanged: " + target)
        return
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", survivor_class)
    bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(NAME, OUT, unreal.Blueprint, factory)
    if not bp:
        raise RuntimeError("Failed to create survivor Blueprint")
    # Set default inherited Character mesh on generated class CDO.
    generated = unreal.EditorAssetLibrary.load_blueprint_class(target)
    cdo = unreal.get_default_object(generated)
    body = cdo.get_editor_property("mesh")
    body.set_editor_property("skeletal_mesh_asset", mesh)
    unreal.EditorAssetLibrary.save_loaded_asset(bp)
    log("Created " + target + " using " + mesh.get_path_name())
    log("Assign the Blueprint as Default Pawn Class in your GameMode and test in PIE.")
    log("Quantum clothing uses a different skeleton: retarget meshes before attaching to Survival Character.")

if __name__ == "__main__":
    main()
