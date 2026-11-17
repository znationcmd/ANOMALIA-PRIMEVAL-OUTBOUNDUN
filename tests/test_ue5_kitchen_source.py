"""Source-contract regressions; these do not replace UE5 compilation or PIE."""
from pathlib import Path
import json
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
CPP=ROOT/"unreal/Source/AnomaliaZPrigimalia/Survival/AnomaliaZPrigimaliaKitchenActions.cpp"
HEADER=ROOT/"unreal/Source/AnomaliaZPrigimalia/AnomaliaZPrigimaliaInventoryComponent.h"
WATER_H=ROOT/"unreal/Source/AnomaliaZPrigimalia/Survival/AnomaliaZPrigimaliaWaterSource.h"
WATER_CPP=ROOT/"unreal/Source/AnomaliaZPrigimalia/Survival/AnomaliaZPrigimaliaWaterSource.cpp"
UI=ROOT/"unreal/Source/AnomaliaZPrigimalia/AnomaliaZPrigimaliaInventoryWidget.cpp"
CATALOG=ROOT/"public/config/loot_items_catalog.json"
NATIVE_TEST=ROOT/"unreal/Source/AnomaliaZPrigimalia/Tests/AnomaliaZPrigimaliaKitchenTests.cpp"

class KitchenSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=json.loads(CATALOG.read_text(encoding="utf-8"))
        cls.items={item["id"]:item for item in cls.catalog["items"]}
        cls.cpp=CPP.read_text(encoding="utf-8")
        cls.header=HEADER.read_text(encoding="utf-8")
        cls.ui=UI.read_text(encoding="utf-8")

    def test_existing_containers_and_outputs_are_registered_once(self):
        self.assertEqual(self.catalog["schemaVersion"],1)
        from collections import Counter
        duplicates={key:n for key,n in Counter(x["id"] for x in self.catalog["items"]).items() if n>1}
        self.assertEqual(duplicates,{"car_battery":2})
        self.assertEqual(len(self.catalog["items"]),len(self.items)+1)
        self.assertGreaterEqual(len(self.items),242)
        for item_id in (
            "empty_water_bottle","water_bottle","dirty_water_bottle",
            "empty_military_canteen","military_canteen","dirty_military_canteen",
            "empty_filter_canteen","filter_canteen","dirty_filter_canteen",
            "cooking_pot","cooking_pot_water","dirty_cooking_pot_water",
            "frying_pan","water_purification_tablets",
            "cooked_meat","cooked_fish","cooked_egg","cooked_potato","cooked_vegetable"
        ):
            # cooked_meat/fish are original generic survival IDs (defined in
            # native inventory fallback rules), not loot catalogue entries.
            if item_id not in ("cooked_meat","cooked_fish"):
                self.assertIn(item_id,self.items)
            self.assertIn(item_id,self.cpp)
        for item_id in ("cooked_egg","cooked_potato","cooked_vegetable"):
            use=self.items[item_id]["use"]
            self.assertEqual(use["action"],"eat")
            self.assertGreater(use["hunger"],0)

    def test_quality_and_empty_containers_are_not_spawned(self):
        for item_id in ("dirty_military_canteen","dirty_filter_canteen",
                        "cooking_pot_water","dirty_cooking_pot_water",
                        "cooked_egg","cooked_potato","cooked_vegetable"):
            row=self.items[item_id]
            self.assertFalse(row["enabled"])
            self.assertEqual(row["nominal"],0)
            self.assertEqual(row["maxStack"],1)
        for item_id,empty in [("dirty_military_canteen","empty_military_canteen"),
                              ("dirty_filter_canteen","empty_filter_canteen")]:
            use=self.items[item_id]["use"]
            self.assertEqual(use["action"],"drink")
            self.assertEqual(use["returnItem"],empty)
            self.assertEqual(use["effect"],"raw_food")

    def test_no_client_selected_water_quality_or_cooked_output(self):
        for call in ("RequestFillContainer","RequestTreatWater",
                     "RequestBoilPot","RequestCookFood"):
            self.assertIn("bool "+call+"(",self.header)
            self.assertIn("Server"+call+"(",self.header)
            self.assertIn("Server"+call+"_Implementation(",self.cpp)
        self.assertIn("FilledItemFor(Utensil->ItemId,Source->bPotable)",self.cpp)
        self.assertIn("Source->CanFillFrom(GetOwner()->GetActorLocation())",self.cpp)
        self.assertIn("GetWorld()->GetRealTimeSeconds()",self.cpp)
        self.assertIn("GetPersistentPlayerId(",self.cpp)
        self.assertIn("HasPendingPlayer(",self.cpp)
        self.assertIn("SavePlayerProfile(",self.cpp)
        self.assertIn("BuildInventoryProfile(",self.cpp)
        self.assertIn("Restore();",self.cpp)

    def test_heating_is_fuelled_and_delayed(self):
        self.assertIn("HeatSourceComponent::Sample(",self.cpp)
        self.assertIn("SetTimer(KitchenCookTimer",self.cpp)
        self.assertIn("SetTimer(KitchenCheckTimer",self.cpp)
        self.assertIn("CheckKitchenFire",self.cpp)
        self.assertIn("GetWorld()->GetTimerManager().ClearTimer(KitchenCookTimer)",self.cpp)
        self.assertIn("FName CookedFoodFor",self.header)
        for raw in ("raw_meat","raw_fish","egg","potato","vegetable"):
            self.assertIn("Id==TEXT("+json.dumps(raw)+")",self.cpp)

    def test_authored_source_and_ui_bindings(self):
        header=WATER_H.read_text(encoding="utf-8")
        source=WATER_CPP.read_text(encoding="utf-8")
        self.assertIn("bPotable = false",header)
        self.assertIn("FillRadiusCm = 250.f",header)
        self.assertIn("FVector::DistSquared(",source)
        self.assertIn("DOREPLIFETIME(",source)
        for call in ("RequestFillContainer","RequestTreatWater","RequestBoilPot","RequestCookFood"):
            self.assertIn("Inventory->"+call+"(",self.ui)
        self.assertTrue(NATIVE_TEST.exists())

if __name__=="__main__":
    unittest.main()
