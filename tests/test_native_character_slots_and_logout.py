"""Contracts for safe live-3D main menu, independently saved solo survivors,
and authoritative logout actor removal. Follow with a native UE C++ compile.
"""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parent.parent/"unreal/Source/AnomaliaZPrigimalia"
GM=(ROOT/"AnomaliaZPrigimaliaGameMode.cpp").read_text(encoding="utf-8")
GH=(ROOT/"AnomaliaZPrigimaliaGameMode.h").read_text(encoding="utf-8")
UI=(ROOT/"AnomaliaZPrigimaliaSessionWidget.cpp").read_text(encoding="utf-8")
UH=(ROOT/"AnomaliaZPrigimaliaSessionWidget.h").read_text(encoding="utf-8")
class CharacterSlotsTests(unittest.TestCase):
    def test_legacy_local_owner_is_untouched_and_slots_are_separate(self):
        self.assertIn('Slot<=1?TEXT("local-owner")',GM)
        self.assertIn('TEXT("local-owner-slot-%d")',GM)
        self.assertIn("LocalCharacterProfileId(GetLocalCharacterSlot())",GM)
        self.assertIn('TEXT("active-slot.txt")',GM)
        self.assertIn("Slot<=8",GM)
        self.assertIn('GetNetMode()!=NM_Standalone',GM)
        self.assertIn('UAnomaliaZPrigimaliaConfigLibrary::SavePlayerProfile(',GM)
        self.assertIn("if(!SaveLocalGame())",GM)
        self.assertIn("HasLocalCharacterSlot(Slot)",GM)
        self.assertIn('UFUNCTION(BlueprintPure',GH)
    def test_menu_allows_real_profile_creation_selection_and_protected_export(self):
        for name in ("RefreshCharacterSlots", "SelectCharacterSlot",
                     "CreateCharacterSlot", "ExportCharacterForTransfer"):
            self.assertIn("void UAnomaliaZPrigimaliaSessionWidget::"+name+"()",UI)
            self.assertIn("UFUNCTION() void "+name+"();",UH)
        for control in ("SessionCharacterSlots","SessionCharacterSelect","SessionCharacterNew",
                        "SessionCharacterTransfer"):
            self.assertIn(control,UI)
        self.assertIn("UGameplayStatics::OpenLevel(this,FName(*GetWorld()->GetMapName()))",UI)
        self.assertIn("SaveLocalGame()",UI)
        self.assertIn('TEXT("CharacterTransfers")',UI)
        self.assertIn("L'import vers un serveur nécessite sa validation anti-duplication",UI)
    def test_actual_world_last_saved_pawn_is_menu_backdrop(self):
        self.assertIn("Survivor->GetActorLocation()",UI)
        self.assertIn("PC->SetViewTarget(MenuCamera)",UI)
        self.assertIn("MenuCamera->SetActorLocationAndRotation(Eye,(Center-Eye).Rotation())",UI)
        self.assertIn("LastMenuPreviewLocation=Survivor->GetActorLocation()",UI)
        self.assertIn('Survivor->TeleportTo(Position,FRotator(0,Yaw,0),false,false)',GM)
    def test_disconnect_removes_saved_actor_but_not_other_world_content(self):
        self.assertIn("void AAnomaliaZPrigimaliaGameMode::Logout(AController* Exiting)",GM)
        self.assertIn("const bool bSaved=SavePersistentPlayer(Exiting)",GM)
        self.assertIn("if(Exiting->GetPawn()==Survivor)Exiting->UnPossess();",GM)
        self.assertIn("Survivor->Destroy();",GM)
        self.assertIn("Super::Logout(Exiting)",GM)
        self.assertNotIn("Vehicle->Destroy();\n    Super::Logout",GM)
    def test_multiplayer_identity_never_derived_from_untrusted_client_slot(self):
        self.assertIn("if (GetNetMode() == NM_Standalone && Controller->IsLocalController())",GM)
        self.assertIn("Controller->PlayerState->GetUniqueId()",GM)
        self.assertNotIn("ServerRPC_SelectLocalCharacterSlot",GM)
if __name__=="__main__":unittest.main()
