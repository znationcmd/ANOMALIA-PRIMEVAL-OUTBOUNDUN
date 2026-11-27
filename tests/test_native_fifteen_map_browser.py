"""Source contracts for 15 independent Unreal worlds. No gameplay success is claimed."""
import json
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"public/config/anomalia-map-catalog.json"
UI_H=ROOT/"unreal/Source/AnomaliaZPrigimalia/AnomaliaZPrigimaliaSessionWidget.h"
UI_CPP=ROOT/"unreal/Source/AnomaliaZPrigimalia/AnomaliaZPrigimaliaSessionWidget.cpp"
MAP_CPP=ROOT/"unreal/Source/AnomaliaZPrigimalia/AnomaliaZPrigimaliaServerBrowserLibrary.cpp"
MAP_H=ROOT/"unreal/Source/AnomaliaZPrigimalia/AnomaliaZPrigimaliaServerBrowserLibrary.h"

class FifteenMapSelector(unittest.TestCase):
    def test_exact_original_and_four_new_map_entries(self):
        plan=json.loads(DATA.read_text(encoding="utf-8"))
        worlds=plan["maps"]
        self.assertEqual(plan["mapCount"],15)
        self.assertEqual(len(worlds),15)
        self.assertEqual(len({m["id"] for m in worlds}),15)
        self.assertEqual(len({m["saveNamespace"] for m in worlds}),15)
        self.assertTrue(all(m["independentWorld"] for m in worlds))
        self.assertTrue(all(not m["serverSelectable"] for m in worlds[-4:]))
        cpp=MAP_CPP.read_text(encoding="utf-8")
        matches=re.findall(
            r'\{TEXT\("([^"]+)"\), TEXT\("([^"]+)"\), TEXT\("([^"]*)"\)\}',cpp)
        self.assertEqual(len(matches),15)
        self.assertEqual([(m["id"],m["displayName"],m["originalUnrealPackage"] or "") for m in worlds],
                         matches)
        self.assertEqual([m["displayName"] for m in worlds[-4:]],
                         ["ROSКАТVIA-B1","НОГОКВ-51","PARADISIOMANIA","DEADROOT"])

    def test_menu_filters_real_servers_not_world_entries(self):
        widget=UI_CPP.read_text(encoding="utf-8")
        head=UI_H.read_text(encoding="utf-8")
        catalog=MAP_H.read_text(encoding="utf-8")
        self.assertIn("MapFilterSelect",head)
        self.assertIn("MapFilterChanged",head)
        self.assertIn("GetWorldChoices()",widget)
        self.assertIn("MapFilterSelect->OnSelectionChanged.AddDynamic",widget)
        self.assertIn('Entry.Map.Equals(RequestedMap,ESearchCase::IgnoreCase)',widget)
        self.assertIn('void UAnomaliaZPrigimaliaSessionWidget::JoinSelectedServer()',widget)
        self.assertIn("bMultiplayerVerified = false",catalog)
        self.assertIn("bNativePackageFound",catalog)
        self.assertIn("FPackageName::DoesPackageExist",MAP_CPP.read_text(encoding="utf-8"))

if __name__=="__main__":
    unittest.main()
