"""Native Unreal loading art is ONLY shown during map loading, not menus."""
from pathlib import Path
import re
import unittest
BASE=Path(__file__).resolve().parent.parent/"unreal/Source/AnomaliaZPrigimalia"
MOD=(BASE/"AnomaliaZPrigimalia.cpp").read_text(encoding="utf-8")
BUILD=(BASE/"AnomaliaZPrigimalia.Build.cs").read_text(encoding="utf-8")
SESSION=(BASE/"AnomaliaZPrigimaliaSessionWidget.cpp").read_text(encoding="utf-8")
class LoadingRotationTests(unittest.TestCase):
    def test_exactly_four_images_and_cycle(self):
        self.assertEqual(len(re.findall(r'TEXT\("loading-0[1-4]\.jpg"\)',MOD)),4)
        self.assertIn("const int32 Index=((Last+Offset)%4+4)%4;",MOD)
        self.assertIn('TEXT("rotation.txt")',MOD)
        self.assertIn('FFileHelper::SaveStringToFile(FString::FromInt(Index),*Rotation)',MOD)
        self.assertIn("if(!FPaths::FileExists(ImagePath))continue;",MOD)
    def test_only_actual_loads_are_hooked(self):
        self.assertIn("FCoreUObjectDelegates::PreLoadMap.AddRaw",MOD)
        self.assertIn('GetMoviePlayer()->SetupLoadingScreen(Screen);',MOD)
        self.assertIn('Screen.bAutoCompleteWhenLoadingCompletes=true;',MOD)
        self.assertIn('SNew(SThrobber)',MOD)
        self.assertIn('PrivateDependencyModuleNames.Add("MoviePlayer")',BUILD)
        self.assertNotIn("T_StartupPoster",MOD)
        self.assertNotIn('loading-01.jpg',SESSION)
    def test_no_loading_art_auto_replaced_in_main_menu(self):
        self.assertIn("if(bMainMenu)",SESSION)
        self.assertIn('BuildServerBrowser(Canvas);',SESSION)
        self.assertIn('BuildTravelLoading(Canvas);',SESSION)
if __name__=="__main__":unittest.main()
