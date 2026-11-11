import json, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class NamingPlanTests(unittest.TestCase):
    def test_regions_cover_full_map_without_overlap_and_south_is_fifteen_percent(self):
        plan=json.loads((ROOT/'public/config/anomalia-locality-names.json').read_text(encoding='utf-8'))
        north=next(m for m in plan['maps'] if m['mapId']=='bot-sever-v1')
        ge,ru=north['regions']
        area=lambda r:(r['northMetres']-r['southMetres'])*(r['eastMetres']-r['westMetres'])
        self.assertEqual(area(ge),375_000_000)
        self.assertEqual(area(ge)+area(ru),2_500_000_000)
        self.assertEqual(ge['northMetres'],ru['southMetres'])
        self.assertEqual(ge['language'],'ka')
        self.assertEqual(ru['language'],'ru')
        self.assertTrue(plan['rules']['namesAreAuthoredLabelsNotVerifiedPlacements'])
    def test_catalogue_and_utf8_names_roundtrip(self):
        catalogue=json.loads((ROOT/'public/config/anomalia-map-catalog.json').read_text(encoding='utf-8'))
        self.assertEqual(catalogue['mapCount'],len(catalogue['maps']))
        row=next(m for m in catalogue['maps'] if m['id']=='bot-sever-v1')
        self.assertEqual((row['displayName'],row['widthKm'],row['heightKm']),('БОТ СЕВЕР',50,50))
        self.assertFalse(row['nativeWorldCreated'])
        self.assertFalse(row['serverSelectable'])

if __name__=='__main__':unittest.main()
