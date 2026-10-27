"""Audit installed character assets; explicitly create isolated test BPs on request.

Default execution is read-only for project assets. Set ANOMALIA_CHARACTER_MODE=create
and ANOMALIA_CHARACTER_PROFILES=Manny,Quinn (or provide an explicit JSON manifest
with ANOMALIA_CHARACTER_MANIFEST). Never changes maps, GameModes or existing BPs.
Native compilation, PIE and network verification are separate gates.
"""
import json
import os
from pathlib import Path
import uuid

import unreal

OUT = "/Game/Anomalia/Characters"
PARENT = "/Script/AnomaliaPrimeval.AnomaliaSurvivor"
PACK_ROOTS = (
    "/Game/ControlRig/Characters/Mannequins",
    "/Game/QuantumCharacter",
    "/Game/Survival_Character",
)
PROFILES = {
    "Manny": {
        "mesh": PACK_ROOTS[0] + "/Meshes/SKM_Manny",
        "animation": PACK_ROOTS[0] + "/Animations/ABP_Manny",
    },
    "Quinn": {
        "mesh": PACK_ROOTS[0] + "/Meshes/SKM_Quinn",
        "animation": PACK_ROOTS[0] + "/Animations/ABP_Quinn",
    },
    # Quantum has sequences but no compatible AnimBlueprint in the installed pack.
    "Quantum": {"mesh": "/Game/QuantumCharacter/Mesh/SKM_QuantumCharacter", "animation": None},
    "Survival": {
        "mesh": "/Game/Survival_Character/Meshes/Modular_Parts/SK_Survival_Character_Body",
        "animation": "/Game/Survival_Character/Demo/Characters/Mannequins/Animations/ABP_Quinn",
    },
}


def exact_asset(package, expected_type):
    if not isinstance(package, str) or not package.startswith("/Game/") or "." in package:
        raise ValueError("Expected an exact /Game/... package path: " + str(package))
    asset = unreal.load_asset(package)
    if not isinstance(asset, expected_type):
        raise RuntimeError("Missing or wrong asset type: " + package)
    return asset


def audit():
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    registry.search_all_assets(True)
    rows = []
    for root in PACK_ROOTS:
        for data in registry.get_assets_by_path(root, recursive=True):
            cls = str(data.asset_class_path.asset_name)
            row = {"path": str(data.package_name), "class": cls}
            try:
                if cls in ("SkeletalMesh", "AnimBlueprint", "AnimSequence"):
                    obj = data.get_asset()
                    if not obj:
                        raise RuntimeError("Asset could not be loaded")
                    prop = "target_skeleton" if cls == "AnimBlueprint" else "skeleton"
                    skeleton = obj.get_editor_property(prop)
                    row["skeleton"] = skeleton.get_path_name() if skeleton else None
                    if cls == "SkeletalMesh":
                        row["materials"] = [
                            m.material_interface.get_path_name() if m.material_interface else None
                            for m in obj.get_editor_property("materials")
                        ]
            except Exception as exc:
                row["error"] = str(exc)
            rows.append(row)
    return sorted(rows, key=lambda r: r["path"])


def mesh_template(bp):
    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    library = unreal.SubobjectDataBlueprintFunctionLibrary
    matches = []
    for handle in subsystem.k2_gather_subobject_data_for_blueprint(bp):
        data = library.get_data(handle)
        if str(library.get_variable_name(data)) != "Mesh":
            continue
        obj = library.get_object_for_blueprint(data, bp)
        if isinstance(obj, unreal.SkeletalMeshComponent):
            # Reject a template on the native parent, which could affect all children.
            package = bp.get_path_name().split(".")[0]
            if not obj.get_path_name().startswith(package + "."):
                raise RuntimeError("Inherited mesh template is outside the child package")
            matches.append(obj)
    if len(matches) != 1:
        raise RuntimeError("Expected exactly one editable inherited Mesh template")
    return matches[0]


def prepare(name, profile):
    if name not in PROFILES:
        raise ValueError("Unknown character profile: " + name)
    target = OUT + "/BP_Anomalia_" + name
    if unreal.EditorAssetLibrary.does_asset_exist(target):
        raise RuntimeError("Existing asset preserved; refusing overwrite: " + target)
    mesh = exact_asset(profile.get("mesh"), unreal.SkeletalMesh)
    if not profile.get("animation"):
        raise RuntimeError(name + ": explicit verified animation Blueprint required")
    animation = exact_asset(profile["animation"], unreal.AnimBlueprint)
    skeleton = mesh.get_editor_property("skeleton")
    if not skeleton or animation.get_editor_property("target_skeleton") != skeleton:
        raise RuntimeError(name + ": animation/body skeleton mismatch; retarget explicitly")
    anim_class = unreal.EditorAssetLibrary.load_blueprint_class(profile["animation"])
    if not anim_class:
        raise RuntimeError("Animation generated class missing")
    return name, target, mesh, anim_class


def create(prepared, parent):
    name, target, mesh, anim_class = prepared
    # Preflight all profiles before creating anything. No existing asset is edited.
    if unreal.EditorAssetLibrary.does_asset_exist(target):
        raise RuntimeError("Target appeared during setup; refusing overwrite: " + target)
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", parent)
    bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "BP_Anomalia_" + name, OUT, unreal.Blueprint, factory
    )
    if not bp:
        raise RuntimeError("Blueprint creation failed: " + target)
    body = mesh_template(bp)
    body.set_editor_property("skeletal_mesh_asset", mesh)
    body.set_editor_property("animation_mode", unreal.AnimationMode.ANIMATION_BLUEPRINT)
    body.set_editor_property("anim_class", anim_class)
    body.set_editor_property("relative_location", unreal.Vector(0, 0, -90))
    body.set_editor_property("relative_rotation", unreal.Rotator(pitch=0, yaw=-90, roll=0))
    if unreal.BlueprintEditorLibrary.compile_blueprint(bp) is not True:
        raise RuntimeError("Blueprint compilation failed; not saved: " + target)
    # Compilation must preserve both body and animation on the generated default.
    generated = unreal.EditorAssetLibrary.load_blueprint_class(target)
    cdo = unreal.get_default_object(generated)
    default_mesh = cdo.get_editor_property("mesh")
    if default_mesh.get_editor_property("skeletal_mesh_asset") != mesh:
        raise RuntimeError("Body override was not retained after compilation")
    if default_mesh.get_editor_property("anim_class") != anim_class:
        raise RuntimeError("Animation override was not retained after compilation")
    if not unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False):
        raise RuntimeError("Blueprint save failed: " + target)
    return {"path": target, "status": "created_and_saved; PIE_not_verified"}


def main():
    report = {"engine": unreal.SystemLibrary.get_engine_version(), "assets": audit(),
              "created": [], "errors": [], "PIE": "not_run", "multiplayer": "not_run"}
    try:
        mode = os.environ.get("ANOMALIA_CHARACTER_MODE", "audit")
        if mode not in ("audit", "create"):
            raise ValueError("Mode must be audit or create")
        if mode == "create":
            if not report["engine"].startswith("5.8.3-"):
                raise RuntimeError("Creation requires verified Unreal 5.8.3")
            if any("error" in row for row in report["assets"]):
                raise RuntimeError("Asset audit errors must be resolved before creation")
            profiles = dict(PROFILES)
            manifest = os.environ.get("ANOMALIA_CHARACTER_MANIFEST")
            if manifest:
                profiles.update(json.loads(Path(manifest).read_text(encoding="utf-8")))
            names = os.environ.get("ANOMALIA_CHARACTER_PROFILES", "Manny,Quinn").split(",")
            if len(names) != len(set(names)):
                raise ValueError("Duplicate profile selection")
            prepared = [prepare(name, profiles[name]) for name in names]
            parent = unreal.load_class(None, PARENT)
            if not parent:
                raise RuntimeError("Compile the ANOMALIA native module before creation")
            unreal.EditorAssetLibrary.make_directory(OUT)
            for entry in prepared:
                report["created"].append(create(entry, parent))
    except Exception as exc:
        report["errors"].append(str(exc))
        raise
    finally:
        folder = Path(unreal.Paths.project_saved_dir()) / "CharacterAudit"
        folder.mkdir(parents=True, exist_ok=True)
        destination = folder / ("character-" + uuid.uuid4().hex + ".json")
        with destination.open("x", encoding="utf-8") as output:
            json.dump(report, output, indent=2)
        unreal.log("ANOMALIA character report: " + str(destination))


if __name__ == "__main__":
    main()
