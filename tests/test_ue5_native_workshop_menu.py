"""Contracts for the ACTUAL packaged Unreal Engine menu, not WebGL/Electron."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SESSION = ROOT / "unreal/Source/AnomaliaZPrigimalia/AnomaliaZPrigimaliaSessionWidget.cpp"
HEADER = ROOT / "unreal/Source/AnomaliaZPrigimalia/AnomaliaZPrigimaliaSessionWidget.h"
PROBE = ROOT / "unreal/Source/AnomaliaZPrigimalia/AnomaliaZPrigimaliaPlayableProbe.cpp"


class NativeWorkshopMenuTests(unittest.TestCase):
    def test_button_opens_native_fullscreen_workshop(self):
        s = SESSION.read_text(encoding="utf-8")
        self.assertIn('ModsButton=Button(TEXT("SessionMods"),TEXT("Mods"))', s)
        self.assertIn('ModsButton->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::ShowMods)', s)
        self.assertIn('void UAnomaliaZPrigimaliaSessionWidget::ShowMods()', s)
        self.assertIn('WorkshopFrame->SetVisibility(ESlateVisibility::Visible)', s)
        self.assertIn('TEXT("WorkshopFullScreen")', s)
        self.assertIn('TEXT("W O R K F O R G E")', s)
        self.assertIn('void UAnomaliaZPrigimaliaSessionWidget::BuildPremiumWorkshop(UCanvasPanel* Canvas)', s)
        self.assertIn('TEXT("WorkshopHeroBackdrop")', s)
        self.assertIn('T_WorkshopLogo.T_WorkshopLogo', s)
        self.assertIn('UUniformGridPanel::StaticClass()', s)
        for section in ('ANOMALIA  •  MODS', 'MODS POPULAIRES', 'MODS LES MIEUX NOTÉS', 'COMMUNAUTÉ'):
            self.assertIn(section, s)
        self.assertIn('TEXT("WorkshopReturn")', s)
        self.assertIn("void UAnomaliaZPrigimaliaSessionWidget::CloseWorkshop()", s)
        self.assertIn('WorkshopFrame->SetVisibility(ESlateVisibility::Collapsed)', s)
        self.assertNotIn('void UAnomaliaZPrigimaliaSessionWidget::ShowMods() { RefreshMods(); SelectPage(2); }', s)

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
        self.assertIn("UAnomaliaZPrigimaliaModResolver::ValidateModManifest", s)
        self.assertIn("Aucun paquet tiers activé", s)
        self.assertIn('WorkshopFilterVehicles', s)
        self.assertIn('WorkshopFilterCreatures', s)
        self.assertIn('Grid->SetSlotPadding(FMargin(3,4))', s)
        self.assertIn('Grid->AddChildToUniformGrid(Card,I/9,I%9)', s)
        self.assertIn('TEXT("WorkshopSort")', s)
        self.assertIn('void UAnomaliaZPrigimaliaSessionWidget::WorkshopShowMyMods()', s)
        self.assertIn('TEXT("WFNavForge")', s)
        self.assertIn('TEXT("WorkshopManageMods")', s)
        self.assertIn('for(int32 Index=0;Index<Visible.Num();Index+=4)', s)
        self.assertIn('Details->AddChildToVerticalBox', s)
        self.assertIn('UImage::StaticClass()', s)
        self.assertIn('TEXT("WorkshopModAction%d")', s)
        self.assertIn('T_WFHero.T_WFHero', s)
        self.assertIn('T_WFCategory%d', s)
        self.assertIn('T_WFModCardFallback.T_WFModCardFallback', s)
        self.assertIn('WorkshopCountLabel', s)
        self.assertIn('WorkshopCreatorsLabel', s)
        self.assertIn('Footer->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::OpenWorkshopTools)', s)
        self.assertIn('Footer->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::WorkshopOpenLocalModsFolder)', s)
        self.assertNotIn('Button->OnClicked.AddDynamic(this,Handler)', s)
        self.assertNotIn('12 458', s)
        self.assertNotIn('4,8/5', s)

        self.assertNotIn('Grid->AddChildToUniformGrid(Card,I/4,I%4)->SetPadding', s)

    def test_true_mods_tab_has_clickable_controls_and_no_fake_install(self):
        s = SESSION.read_text(encoding="utf-8")
        h = HEADER.read_text(encoding="utf-8")
        self.assertIn('TEXT("WFNavMods")', s)
        self.assertIn('TEXT("WorkshopPlay")', s)
        self.assertIn('WorkshopSearch->OnTextChanged.AddDynamic', s)
        self.assertEqual(s.count('TEXT("WorkshopSearch")'), 1)
        for name in ("WorkshopShowCatalogue", "WorkshopShowCategories", "WorkshopShowCollections",
                     "WorkshopShowCommunity", "WorkshopShowDownloads", "WorkshopShowSettings",
                     "WorkshopOpenLocalModsFolder"):
            self.assertIn(f"UFUNCTION() void {name}();", h)
            self.assertIn(f"void UAnomaliaZPrigimaliaSessionWidget::{name}()", s)
            self.assertIn(f"&UAnomaliaZPrigimaliaSessionWidget::{name}", s)
        self.assertIn("bWorkshopMyModsOnly=true", s)
        self.assertIn("Item.bInstalledManifest", s)
        self.assertIn("WorkshopFrame && WorkshopFrame->GetVisibility()==ESlateVisibility::Visible", s)
        self.assertIn("CloseWorkshop();", s)
        self.assertIn("Aucun paquet tiers activé", s)
        self.assertNotIn("12 458", s)
        self.assertNotIn("Installer</button>", s)

    def test_real_native_packaged_client_probe_asserts_workshop_visible(self):
        p = PROBE.read_text(encoding="utf-8")
        for token in ('TEXT("WorkshopFullScreen")', 'TEXT("WorkshopSearch")',
                      'TEXT("WorkshopCategory")', 'TEXT("WorkshopCards")',
                      'TEXT("WorkshopReturn")', '"-workshop.png"',
                      "Native in-game Workshop missing or not visible",
                      "Native Workshop return button failed to close"):
            self.assertIn(token, p)


    def test_logo_is_committed_and_imported_before_native_cook(self):
        script = ROOT / 'unreal/Scripts/import_workshop_branding.py'
        self.assertTrue(script.is_file())
        self.assertTrue((ROOT/'unreal/SourceAssets/Branding/workshop-logo.jpg').is_file())
        importer = script.read_text(encoding='utf-8')
        self.assertIn('T_WorkshopLogo', importer)
        workflow = (ROOT/'.github/workflows/ue5-pc-progress-update.yml').read_text(encoding='utf-8')
        self.assertIn('import_workshop_branding.py', workflow)
        self.assertLess(workflow.index('- name: Import actual ANOMALIA Workshop emblem'), workflow.index('- name: Cook the actual game'))


if __name__ == "__main__":
    unittest.main()
