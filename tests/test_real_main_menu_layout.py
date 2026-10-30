"""Regression contracts for the REAL cooked Unreal 5.8 start/pause menu.

Only the native Windows screenshot/click probe can validate runtime behavior;
these source assertions catch regressions before invoking the expensive build.
"""
from pathlib import Path
import re
import unittest

BASE=Path(__file__).resolve().parent.parent/"unreal/Source/AnomaliaZPrigimalia"
CPP=(BASE/"AnomaliaZPrigimaliaSessionWidget.cpp").read_text(encoding="utf-8")
PROBE=(BASE/"AnomaliaZPrigimaliaPlayableProbe.cpp").read_text(encoding="utf-8")

class RealMenuLayout(unittest.TestCase):
    def test_real_last_survivor_instead_of_fake_static_wallpaper(self):
        self.assertIn("PC->SetViewTarget(MenuCamera)",CPP)
        self.assertIn("LastMenuPreviewLocation=Survivor->GetActorLocation()",CPP)
        self.assertIn("MenuCamera->SetActorLocationAndRotation",CPP)
        self.assertIn("bStartupIntro=false",CPP)
        self.assertIn("StartupArtworkFrame->SetVisibility(ESlateVisibility::Collapsed)",CPP)
        self.assertIn('SessionMainBrand',CPP)
        self.assertIn("AddBrandText(TEXT(\"ANOMALIA'\"),51",CPP)
        self.assertIn('TEXT("Z"),58',CPP)
    def test_large_right_aligned_menu_not_left_miniature(self):
        self.assertIn("FAnchors(.675f,.245f,.956f,.855f)",CPP)
        self.assertIn('TEXT("MENU PRINCIPAL")',CPP)
        self.assertIn('TEXT("▶  JOUER")',CPP)
        self.assertIn("L->SetJustification(ETextJustify::Center)",CPP)
        self.assertNotIn("FrameSlot->SetAnchors(FAnchors(.035f,.12f,.31f,.77f))",CPP)
    def test_start_and_pause_are_separated(self):
        self.assertIn('TEXT("SessionOnline")',CPP)
        self.assertIn('TEXT("SessionInvite")',CPP)
        self.assertIn('TEXT("SessionCharacterNew")',CPP)
        self.assertIn('TEXT("SessionMods")',CPP)
        self.assertIn('TEXT("ServerBrowserFullScreen")',CPP)
        self.assertIn('if(!bMainMenu || !WorkshopFrame) return;',CPP)
        self.assertIn("else BuildOnlinePlayers(Canvas);",CPP)
    def test_cooked_game_probe_checks_rendered_main_menu_and_real_clicks(self):
        self.assertIn('AnomaliaZPrigimaliaMenuOnly',PROBE)
        self.assertIn('real_right_aligned_3d_main_menu_visible_without_old_poster',PROBE)
        self.assertIn('working_start_server_browser_workforge_and_separate_pause',PROBE)
        self.assertIn('"-actual-main-menu.png"',PROBE)
        self.assertIn("FScreenshotRequest::RequestScreenshot",PROBE)
        self.assertIn("Layout->GetAnchors().Minimum.X<.60f",PROBE)
        self.assertIn('Real survivor body is missing in cooked Windows game',PROBE)
        self.assertIn('GetMesh()->GetSkeletalMeshAsset()',PROBE)
        survivor=(BASE/"AnomaliaZPrigimaliaSurvivor.cpp").read_text(encoding="utf-8")
        self.assertIn('ApprovedProjectMeshes',survivor)
        self.assertIn('PRIGIMALIA_NO_SURVIVOR_MESH',survivor)
if __name__ == "__main__":
    unittest.main()
