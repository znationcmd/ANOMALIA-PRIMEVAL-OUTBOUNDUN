"""Contracts for the ACTUAL packaged Unreal Engine menu, not WebGL/Electron."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SESSION = ROOT / "unreal/Source/AnomaliaPrimeval/AnomaliaSessionWidget.cpp"
HEADER = ROOT / "unreal/Source/AnomaliaPrimeval/AnomaliaSessionWidget.h"
PROBE = ROOT / "unreal/Source/AnomaliaPrimeval/AnomaliaPlayableProbe.cpp"


class NativeWorkshopMenuTests(unittest.TestCase):
    def test_button_opens_native_fullscreen_workshop(self):
        s = SESSION.read_text(encoding="utf-8")
        self.assertIn('ModsButton=Button(TEXT("SessionMods"),TEXT("Mods"))', s)
        self.assertIn('ModsButton->OnClicked.AddDynamic(this,&UAnomaliaSessionWidget::ShowMods)', s)
        self.assertIn('void UAnomaliaSessionWidget::ShowMods()', s)
        self.assertIn('WorkshopFrame->SetVisibility(ESlateVisibility::Visible)', s)
        self.assertIn('TEXT("WorkshopFullScreen")', s)
        self.assertIn('TEXT("ANOMALIA WORKSHOP")', s)
        self.assertIn('TEXT("WorkshopReturn")', s)
        self.assertIn("void UAnomaliaSessionWidget::CloseWorkshop()", s)
        self.assertIn('WorkshopFrame->SetVisibility(ESlateVisibility::Collapsed)', s)
        self.assertNotIn('void UAnomaliaSessionWidget::ShowMods() { RefreshMods(); SelectPage(2); }', s)

    def test_native_search_categories_and_real_sources(self):
        s = SESSION.read_text(encoding="utf-8")
        h = HEADER.read_text(encoding="utf-8")
        for token in ('"WorkshopSearch"', '"WorkshopCategory"', '"WorkshopCards"',
                      "OnTextChanged.AddDynamic", "OnSelectionChanged.AddDynamic",
                      'TEXT("private-workspaces")', 'TEXT("Config/workshop.json")',
                      'TEXT("manifest.json")'):
            self.assertIn(token, s)
        self.assertIn("UFUNCTION() void RefreshWorkshop();", h)
        self.assertIn("WorkshopCategoryChanged(FString SelectedItem, ESelectInfo::Type SelectionType)", h)
        self.assertIn("const int64 Size=IFileManager::Get().FileSize(*File)", s)
        self.assertIn("UAnomaliaModResolver::ValidateModManifest", s)
        self.assertIn("Chargement UE5 non connecté", s)

    def test_real_native_packaged_client_probe_asserts_workshop_visible(self):
        p = PROBE.read_text(encoding="utf-8")
        for token in ('TEXT("WorkshopFullScreen")', 'TEXT("WorkshopSearch")',
                      'TEXT("WorkshopCategory")', 'TEXT("WorkshopCards")',
                      'TEXT("WorkshopReturn")', '"-workshop.png"',
                      "Native in-game Workshop missing or not visible",
                      "Native Workshop return button failed to close"):
            self.assertIn(token, p)


if __name__ == "__main__":
    unittest.main()
