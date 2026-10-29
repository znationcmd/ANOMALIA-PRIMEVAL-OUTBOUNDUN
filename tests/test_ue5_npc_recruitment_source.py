"""Static source-contract checks for the NPC recruitment port.

These do not compile or execute Unreal code; native build/PIE tests remain required.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "unreal/Source/AnomaliaZPrigimalia"
HEADER = (BASE / "AnomaliaNpcRecruitmentSubsystem.h").read_text(encoding="utf-8")
SOURCE = (BASE / "AnomaliaNpcRecruitmentSubsystem.cpp").read_text(encoding="utf-8")
LEGACY = (ROOT / "src/npc-recruitment.js").read_text(encoding="utf-8")


class UE5NpcRecruitmentSourceTests(unittest.TestCase):
    def test_original_legacy_module_is_preserved(self):
        for operation in ("strikeNonlethal", "bindNpc", "dragNpc",
                          "admitNpc", "advanceRecruitment", "deployRecruit", "assignRecruit"):
            with self.subTest(operation=operation):
                self.assertIn(f"function {operation}", LEGACY)

    def test_unreal_port_exposes_equivalent_gameplay_operations(self):
        self.assertIn("UAnomaliaNpcRecruitmentSubsystem : public UWorldSubsystem", HEADER)
        for method in (
            "RegisterWorldNpc", "ApplyNonlethalStrike", "BindNpc", "DragNpc",
            "RegisterStation", "AdmitNpc", "AdvanceTraining",
            "BeginDeployment", "FinishDeployment", "AssignRole",
        ):
            with self.subTest(method=method):
                self.assertIn(method, HEADER)
                self.assertIn(f"UAnomaliaNpcRecruitmentSubsystem::{method}", SOURCE)

    def test_eight_jobs_and_persistent_attributes_are_explicit(self):
        for role in ("Fighter", "Archer", "Performer", "Blacksmith",
                     "Tanner", "Carpenter", "Cook", "Farmer"):
            self.assertIn(role, HEADER)
        for attribute in ("AppearanceId", "EquipmentIds", "ExtensionData",
                          "Health", "Level", "Torpor"):
            self.assertIn(attribute, HEADER)

    def test_mutations_require_authoritative_world_and_server_identity(self):
        self.assertIn("GetNetMode() != NM_Client", SOURCE)
        self.assertIn("GetPersistentPlayerId(Controller)", SOURCE)
        self.assertIn("Controller->GetWorld() != GetWorld()", SOURCE)
        self.assertIn("BlueprintAuthorityOnly", HEADER)
        self.assertIn("Npc->BoundByPlayerId != Station->OwnerId", SOURCE)

    def test_server_verified_world_actions_are_not_claimed_implemented(self):
        self.assertIn("bServerVerifiedRope", HEADER)
        self.assertIn("bServerVerifiedPlacement", HEADER)
        self.assertIn("ConsumedSupplies", HEADER)
        self.assertIn("Status = EAnomaliaRecruitStatus::PendingDeployment", SOURCE)
        self.assertIn("if (!bWorldSpawnSucceeded)", SOURCE)
        self.assertIn("Npc->Status = EAnomaliaRecruitStatus::Ready;", SOURCE)

    def test_original_training_and_rope_rules(self):
        self.assertIn("RopeRangeMeters = 14.f", SOURCE)
        self.assertIn("BindRangeMeters = 3.f", SOURCE)
        self.assertIn("TrainingBaseSeconds = 90.f", SOURCE)
        self.assertIn("OutSpeedMultiplier = 0.5f", SOURCE)


if __name__ == "__main__":
    unittest.main()
