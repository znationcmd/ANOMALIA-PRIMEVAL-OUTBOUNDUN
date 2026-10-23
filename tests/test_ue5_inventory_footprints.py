"""User-provided ANOMALIA footprint contract, independent of DayZ's data."""
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]

class InventoryFootprintTests(unittest.TestCase):
    def test_requested_shapes_match_catalogue(self):
        rows=[row for name in ['loot_items_catalog.json','rp_items_catalog.json']
              for row in json.loads((ROOT/'public/config'/name).read_text())['items']]
        items={row['id']:row for row in rows}
        expected={'canned_beans':(1,2),'apple':(1,1),'water_bottle':(1,3),'water_in_fuel_can':(2,3),
                  'mlock91':(1,3),'m4a1':(3,3),'mosin_9130':(3,4),'stanag_magazine':(1,2),
                  'fire_axe':(1,5),'shovel':(2,3),'rp_recovery_kit':(2,3),'hunting_jacket':(2,4)}
        for ident,size in expected.items():
            with self.subTest(item=ident):
                self.assertEqual((items[ident]['inventoryWidth'],items[ident]['inventoryHeight']),size)
        for row in rows:
            self.assertGreaterEqual(row['inventoryWidth'],1)
            self.assertGreaterEqual(row['inventoryHeight'],1)
            self.assertLessEqual(row['inventoryWidth'],12)
            self.assertLessEqual(row['inventoryHeight'],20)

if __name__=='__main__':unittest.main()
