import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME_MODE_HEADER = (ROOT / "unreal/Source/AnomaliaZPrigimalia/AnomaliaGameMode.h").read_text(encoding="utf-8")
GAME_MODE_SOURCE = (ROOT / "unreal/Source/AnomaliaZPrigimalia/AnomaliaGameMode.cpp").read_text(encoding="utf-8")


class UE5PlayerLifecyclePersistenceTests(unittest.TestCase):
    def test_profile_identity_comes_from_server_verified_network_id(self):
        self.assertIn("Controller->PlayerState->GetUniqueId()", GAME_MODE_SOURCE)
        self.assertIn("if (!NetId.IsValid()) return FString();", GAME_MODE_SOURCE)
        self.assertIn("FSHA1::HashBuffer", GAME_MODE_SOURCE)
        self.assertIn("return FSHA1::HashBuffer", GAME_MODE_SOURCE)

    def test_load_runs_after_player_start_and_restores_profile_fields(self):
        self.assertIn("HandleStartingNewPlayer_Implementation", GAME_MODE_HEADER)
        self.assertIn("Super::HandleStartingNewPlayer_Implementation(NewPlayer)", GAME_MODE_SOURCE)
        self.assertIn("LoadPersistentPlayer(NewPlayer)", GAME_MODE_SOURCE)
        self.assertIn('TEXT("hunger")', GAME_MODE_SOURCE)
        self.assertIn('TEXT("thirst")', GAME_MODE_SOURCE)
        self.assertIn('TEXT("health")', GAME_MODE_SOURCE)
        self.assertIn("LoadInventoryFromPlayerProfile", GAME_MODE_SOURCE)
        self.assertIn("RestoreSurvival", GAME_MODE_SOURCE)

    def test_save_is_server_owned_periodic_and_runs_on_logout(self):
        self.assertIn("GetWorldTimerManager().SetTimer(ProfileSaveTimer", GAME_MODE_SOURCE)
        self.assertIn("120.f, true", GAME_MODE_SOURCE)
        self.assertIn("virtual void Logout(AController* Exiting) override;", GAME_MODE_HEADER)
        self.assertIn("SavePersistentPlayer(Exiting)", GAME_MODE_SOURCE)
        self.assertIn("SaveAllPlayerProfiles()", GAME_MODE_SOURCE)
        self.assertIn("SaveInventoryToPlayerProfile", GAME_MODE_SOURCE)
        self.assertIn("SavePlayerProfile(ServerId, PlayerId", GAME_MODE_SOURCE)
        self.assertIn("if (!HasAuthority()", GAME_MODE_SOURCE)

    def test_profile_updates_preserve_other_root_and_survival_fields(self):
        self.assertIn("Root->SetObjectField(TEXT(\"survival\"), Survival)", GAME_MODE_SOURCE)
        self.assertIn("ExistingSurvival", GAME_MODE_SOURCE)
        self.assertIn('Error == TEXT("Profile not found")', GAME_MODE_SOURCE)
        self.assertIn("invalid player profile left untouched", GAME_MODE_SOURCE)


if __name__ == "__main__":
    unittest.main()
