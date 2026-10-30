"""Static native menu contract checks, followed by real UE Windows build/smoke.

Do not mistake source contracts for a successful runtime validation.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "unreal/Source/AnomaliaZPrigimalia"
CPP = (BASE / "AnomaliaZPrigimaliaSessionWidget.cpp").read_text(encoding="utf-8")
HEADER = (BASE / "AnomaliaZPrigimaliaSessionWidget.h").read_text(encoding="utf-8")
PROBE = (BASE / "AnomaliaZPrigimaliaPlayableProbe.cpp").read_text(encoding="utf-8")

class StartPauseServerFlowTests(unittest.TestCase):
    def test_start_menu_routes_play_to_real_server_browser(self):
        for token in ("ServerBrowserFullScreen", "ServerTabOfficial",
                      "ServerTabCommunity", "ServerTabFavorite",
                      "ServerBrowserSearch", "ServerBrowserSolo", "ServerBrowserJoin",
                      "void UAnomaliaZPrigimaliaSessionWidget::ShowServerBrowser()",
                      "void UAnomaliaZPrigimaliaSessionWidget::JoinSelectedServer()",
                      "WeakPC->ClientTravel(Address,TRAVEL_Absolute)",
                      "SavedDir(),TEXT(\"ServerBrowser\")"):
            self.assertIn(token, CPP)
        self.assertIn('if(bMainMenu){ ShowServerBrowser();return; }',CPP)
        self.assertIn('ServerBrowserFullScreen', PROBE)
        self.assertIn('main_menu_server_browser_tabs_and_search', PROBE)

    def test_only_real_configured_servers_and_validated_hosts(self):
        for token in ('256*1024','ServerEntries.Num()>=128','TryGetStringField(TEXT("address")',
                      'ServerCategory==TEXT("Favoris")','!Port.IsNumeric()',
                      "ClientTravel(Address,TRAVEL_Absolute)", "Joueurs : non vérifiés"):
            self.assertIn(token,CPP)
        self.assertNotIn('12 458 serveurs',CPP)
        self.assertNotIn('Ping simulé',CPP)

    def test_main_menu_shows_actual_survivor_and_world_not_fake_snapshot(self):
        for token in ("Survivor->GetActorLocation()","Survivor->GetActorForwardVector()",
                      "PC->SetViewTarget(MenuCamera)", "PreviousViewTarget=PC->GetViewTarget()",
                      "bMainMenu && PC && GetWorld()"):
            self.assertIn(token,CPP)
        self.assertIn("LoadPersistentPlayer(NewPlayer)",(BASE/"AnomaliaZPrigimaliaGameMode.cpp").read_text(encoding="utf-8"))

    def test_pause_has_players_not_mods(self):
        for token in ('if(bMainMenu)', 'else BuildOnlinePlayers(Canvas);',
                      'TEXT("SessionOnline")','TEXT("SessionInvite")',
                      'TEXT("PauseOnlinePlayers")','GameState->PlayerArray',
                      'Player->GetPlayerName()', 'void UAnomaliaZPrigimaliaSessionWidget::ShowOnlinePlayers()'):
            self.assertIn(token,CPP)
        self.assertIn("if(!bMainMenu || !WorkshopFrame) return;",CPP)
        self.assertIn("if(bMainMenu)\n    {\n        BuildPremiumWorkshop(Canvas);",CPP)
        self.assertIn('UFUNCTION() void RefreshOnlinePlayers();',HEADER)

    def test_loading_is_not_fake_progress(self):
        for token in ("ServerTravelLoading", "ServerTravelActivity",
                      "SetIsMarquee(true)", "Connexion en cours",
                      "UGameplayStatics::SetGamePaused(PC,false)"):
            self.assertIn(token,CPP)
        self.assertNotIn("SetPercent(1",CPP)

    def test_fixed_previous_workforge_compile_error(self):
        self.assertIn("auto StatBlock=[&]",CPP)
        self.assertNotIn("auto* StatBlock=[&]",CPP)

if __name__=="__main__":
    unittest.main()
