"""Source-level regression guards for Unreal survival v1.

These checks do not run Unreal Engine or prove native C++ compilation.
"""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "unreal/Source/AnomaliaPrimeval"


def cpp(name):
    return (SOURCE / name).read_text(encoding="utf-8")


class UE5VitalsSourceTests(unittest.TestCase):
    def test_server_authority_and_replication(self):
        header = cpp("AnomaliaVitalsComponent.h")
        code = cpp("AnomaliaVitalsComponent.cpp")
        self.assertIn("SetIsReplicatedByDefault(true)", code)
        self.assertIn("Survivor->HasAuthority()", code)
        self.assertIn("UFUNCTION(Server, Reliable)", header)
        self.assertIn("ServerRequestSprint_Implementation", code)
        for name in ("Stamina", "BodyTemperatureC", "bIsSprinting"):
            self.assertIn(f"DOREPLIFETIME(UAnomaliaVitalsComponent, {name})", code)
        self.assertIn("OnRep_Sprinting()", code)
        self.assertIn("bSprintRequested", code)
        self.assertIn("bExhausted", code)
        self.assertIn("Survivor->Health > 0.f", code)
        self.assertNotIn("UFUNCTION(Client", header)

    def test_player_pawn_and_input_are_wired(self):
        player = cpp("AnomaliaSurvivor.cpp")
        header = cpp("AnomaliaSurvivor.h")
        inputs = (ROOT / "unreal/Config/DefaultInput.ini").read_text(encoding="utf-8")
        self.assertIn("CreateDefaultSubobject<UAnomaliaVitalsComponent>", player)
        self.assertIn("UAnomaliaVitalsComponent", header)
        self.assertIn('BindAction(TEXT("Sprint"), IE_Pressed', player)
        self.assertIn('BindAction(TEXT("Sprint"), IE_Released', player)
        self.assertIn('ActionName="Sprint",Key=LeftShift', inputs)
        self.assertIn("VitalsComponent->RequestSprint(false)", player)

    def test_survival_config_is_bounded_and_server_scoped(self):
        header = cpp("AnomaliaConfigLibrary.h")
        source = cpp("AnomaliaConfigLibrary.cpp")
        self.assertIn("AmbientTemperatureC = 20.f", header)
        self.assertIn('TEXT("ambientTemperatureC")', source)
        self.assertIn("OutSettings.AmbientTemperatureC", source)
        self.assertIn("Settings.AmbientTemperatureC < -50.f", source)
        self.assertIn("Settings.AmbientTemperatureC > 60.f", source)
        settings = json.loads((ROOT / "unreal/Config/Anomalia/config.json").read_text())
        self.assertEqual(settings["survival"]["ambientTemperatureC"], 20)
        catalog = json.loads((ROOT / "unreal/Config/Anomalia/settings-catalog.json").read_text())
        match = [x for x in catalog["entries"] if x["id"] == "survival.ambientTemperatureC"]
        self.assertEqual(len(match), 1)
        self.assertEqual(match[0]["status"], "partial")

    def test_profile_restore_and_save_preserve_legacy(self):
        source = cpp("AnomaliaGameMode.cpp")
        self.assertIn('TEXT("stamina")', source)
        self.assertIn('TEXT("bodyTemperatureC")', source)
        self.assertIn("VitalsComponent->RestoreVitals", source)
        self.assertIn("if (bValidVitals)", source)
        self.assertIn("if (Survivor->VitalsComponent)", source)
        self.assertIn("SavePlayerProfile(ServerId, PlayerId", source)
        self.assertIn("ExistingSurvival", source)
        self.assertIn("if (!HasAuthority()", source)

    def test_damage_and_movement_only_on_server(self):
        code = cpp("AnomaliaVitalsComponent.cpp")
        self.assertIn("if (!Survivor->HasAuthority()) { ApplyMovementSpeed(); return; }", code)
        self.assertLess(code.index("if (!Survivor->HasAuthority()) { ApplyMovementSpeed(); return; }"),
                        code.index("const float Step = FMath::Min(DeltaTime, 0.25f)"))
        self.assertIn("Survivor->Health = FMath::Max(0.f", code)
        self.assertIn("Move->MaxWalkSpeed = bIsSprinting ? SprintWalkSpeed * Scale : TacticalSpeed;", code)
        self.assertIn("CalculateTacticalSpeed(4, LoadKg, Survivor->Fatigue, InjuryScale)", code)
        self.assertIn("BodyTemperatureC < 35.f", code)
        self.assertIn("BodyTemperatureC > 40.f", code)
        self.assertIn("FMath::Clamp(SavedTemperatureC, 25.f, 45.f)", code)

    def test_tactical_pace_is_real_character_gameplay(self):
        code = cpp("AnomaliaVitalsComponent.cpp")
        survivor = cpp("AnomaliaSurvivor.cpp")
        settings = (ROOT / "unreal/Config/DefaultInput.ini").read_text(encoding="utf-8")
        self.assertIn("InventoryComponent->GetCurrentWeightKg()", code)
        self.assertIn("GetMovementScale()", code)
        self.assertIn("Survivor->Fatigue", code)
        self.assertIn("ServerRequestPaceStep_Implementation", code)
        self.assertIn("DOREPLIFETIME(UAnomaliaVitalsComponent, PaceStep)", code)
        self.assertIn("DOREPLIFETIME(UAnomaliaVitalsComponent, bExhausted)", code)
        self.assertIn("GetCharacterMovement()->NavAgentProps.bCanCrouch = true", survivor)
        self.assertIn("if (bIsCrouched) UnCrouch(); else Crouch();", survivor)
        self.assertIn('ActionName="PaceMode",Key=RightAlt', settings)
        self.assertIn('ActionName="TacticalCrouch",Key=C', settings)


if __name__ == "__main__":
    unittest.main()
