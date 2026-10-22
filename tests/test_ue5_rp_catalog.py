"""Validate real additive RP catalogue values and existing-catalogue preservation."""
import json
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]

class RPCatalogTests(unittest.TestCase):
    def test_existing_catalogue_preserved_and_rp_ids_do_not_shadow_it(self):
        original = json.loads((ROOT/'public/config/loot_items_catalog.json').read_text())['items']
        extra = json.loads((ROOT/'public/config/rp_items_catalog.json').read_text())['items']
        empty = {'empty_water_bottle', 'empty_military_canteen', 'empty_filter_canteen', 'dirty_water_bottle'}
        self.assertEqual(len([row for row in original if row['id'] not in empty]),232)
        self.assertEqual({row['id'] for row in original if row['id'] in empty},empty)
        self.assertEqual(len(extra),79)
        # Existing battery appears under lighting and engine parts; native loader merges
        # its categories while retaining the unchanged source rows.
        from collections import Counter
        duplicates = {key:value for key,value in Counter(row['id'] for row in original).items() if value>1}
        self.assertEqual(duplicates,{'car_battery':2})
        self.assertFalse({row['id'].lower() for row in original} & {row['id'].lower() for row in extra})
        ids = [row['id'].lower() for row in original+extra]
        self.assertEqual(len(set(ids)),314)
        for row in extra:
            self.assertGreater(row['weightKg'],0)
            self.assertGreaterEqual(row['maxStack'],row['quantity'])
            self.assertLessEqual(row['minTier'],row['maxTier'])

    def test_banknote_values_and_mass_and_gold_mass_match_ids(self):
        extra = {row['id']:row for row in json.loads((ROOT/'public/config/rp_items_catalog.json').read_text())['items']}
        bank = json.loads((ROOT/'public/config/rp_economy.json').read_text())
        self.assertEqual({row['itemId']:row['valueCents'] for row in bank['denominations']},
                         {f'eur_note_{n}':n*100 for n in [5,10,20,50,100,200,500]})
        for n in [5,10,20,50,100,200,500]:
            self.assertEqual(extra[f'eur_note_{n}']['weightKg'],.001)
        for grams in [1,10,100,250,500,1000]:
            self.assertEqual(extra[f'gold_bar_{grams}g']['weightKg'],grams/1000)
        self.assertNotIn('rp_cash_bundle',{row['itemId'] for row in bank['denominations']})

    def test_rp_spawn_filters_have_native_tier_group_and_valid_items(self):
        extra = json.loads((ROOT/'public/config/rp_items_catalog.json').read_text())['items']
        tiers = json.loads((ROOT/'public/config/loot_tiers.json').read_text())['tiers']
        self.assertIn('rp_common',tiers[0]['categories'])
        self.assertIn('rp_rare',tiers[3]['categories'])
        notes = [row for row in extra if row['category']=='rp_cash']
        self.assertEqual(len(notes),7)
        self.assertTrue(all(row['minTier']==1 for row in notes))

    def test_rp_substances_and_tobacco_require_explicit_policy_and_use_rules(self):
        rows=json.loads((ROOT/'public/config/rp_items_catalog.json').read_text())['items']
        substances=[row for row in rows if row['category']=='rp_substances']
        self.assertEqual(len(substances),36)
        self.assertEqual({row['use']['effect'] for row in substances},
                         {'stimulant','opioid','depressant','hallucinogen','cannabinoid','veterinary','anomaly'})
        self.assertTrue(all(row['use']['restrictedGroup']=='substances' and row['use']['action']=='rp' for row in substances))
        tobacco=[row for row in rows if row['category']=='rp_tobacco' and 'use' in row]
        self.assertEqual(len(tobacco),3)
        for row in tobacco:
            self.assertEqual(row['use']['restrictedGroup'],'tobacco')
            self.assertEqual(row['use']['requiredItem'],'lighter')
            self.assertEqual(row['use']['returnItem'],'cigarette_butt')

    def test_medical_and_hazardous_items_keep_distinct_interactions(self):
        items={row['id']:row for row in json.loads((ROOT/'public/config/loot_items_catalog.json').read_text())['items']}
        self.assertEqual(items['blood_bag']['use']['requiredItem'],'iv_kit')
        self.assertEqual(items['tetracycline']['use']['effect'],'antibiotic')
        self.assertNotIn('health',items['tetracycline']['use'])
        self.assertEqual(items['alcohol_90']['use']['action'],'heal')
        self.assertNotIn('use',items['water_in_fuel_can'])
        self.assertEqual(items['water_purification_tablets']['use']['requiredItem'],'dirty_water_bottle')
        self.assertEqual(items['water_purification_tablets']['use']['returnItem'],'water_bottle')
        for ident in ['vodka','whisky','rum','red_wine','white_wine','rose_wine','champagne']:
            self.assertEqual(items[ident]['use']['restrictedGroup'],'alcohol')

if __name__=='__main__':
    unittest.main()
