"""Safety preflight tests only; these do not substitute for Unreal tests."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock


class Mesh:
    def __init__(self, skeleton):
        self.skeleton = skeleton

    def get_editor_property(self, name):
        return self.skeleton


class Animation(Mesh):
    pass


fake = types.SimpleNamespace(SkeletalMesh=Mesh, AnimBlueprint=Animation)
sys.modules["unreal"] = fake
spec = importlib.util.spec_from_file_location(
    "character_setup", Path(__file__).resolve().parents[1] / "unreal/Content/Python/setup_anomalia_character.py"
)
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class CharacterSetupPreflight(unittest.TestCase):
    def setUp(self):
        fake.load_asset = Mock()
        fake.EditorAssetLibrary = Mock()
        fake.EditorAssetLibrary.does_asset_exist.return_value = False
        self.skeleton = object()
        self.mesh = Mesh(self.skeleton)
        self.animation = Animation(self.skeleton)
        fake.load_asset.side_effect = [self.mesh, self.animation]

    def test_missing_exact_mesh_does_not_fall_back_to_other_pack(self):
        fake.load_asset.side_effect = None
        fake.load_asset.return_value = None
        with self.assertRaises(RuntimeError):
            setup.exact_asset("/Game/Missing/SKM_Manny", Mesh)
        fake.load_asset.assert_called_once_with("/Game/Missing/SKM_Manny")

    def test_existing_blueprint_is_rejected_before_loading_or_editing(self):
        fake.EditorAssetLibrary.does_asset_exist.return_value = True
        with self.assertRaisesRegex(RuntimeError, "refusing overwrite"):
            setup.prepare("Manny", setup.PROFILES["Manny"])
        fake.load_asset.assert_not_called()

    def test_skeleton_mismatch_is_rejected(self):
        fake.load_asset.side_effect = [self.mesh, Animation(object())]
        with self.assertRaisesRegex(RuntimeError, "skeleton mismatch"):
            setup.prepare("Manny", setup.PROFILES["Manny"])

    def test_unverified_animation_blocks_quantum_creation(self):
        with self.assertRaisesRegex(RuntimeError, "verified animation"):
            setup.prepare("Quantum", setup.PROFILES["Quantum"])

    def test_verified_pair_yields_exact_named_target(self):
        prepared = setup.prepare("Quinn", setup.PROFILES["Quinn"])
        self.assertEqual(prepared[1], "/Game/Anomalia/Characters/BP_Anomalia_Quinn")
        self.assertIs(prepared[2], self.mesh)

    def test_non_project_and_ambiguous_object_paths_are_rejected(self):
        for name in ("/Engine/Mesh", "/Game/Mesh.Mesh", "/Games/Mesh", None):
            with self.subTest(name=name), self.assertRaises(ValueError):
                setup.exact_asset(name, Mesh)
        fake.load_asset.assert_not_called()

    def test_unknown_profile_cannot_create_arbitrary_asset_name(self):
        with self.assertRaises(ValueError):
            setup.prepare("../Vehicle", setup.PROFILES["Manny"])


if __name__ == "__main__":
    unittest.main()
