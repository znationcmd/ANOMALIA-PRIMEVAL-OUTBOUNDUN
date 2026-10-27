import importlib.util
import json
from pathlib import Path
import struct
import unittest

ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
identity=module('place_identity','unreal/Scripts/place_identity.py')
sign=module('place_sign_mesh','scripts/world-features/build-place-sign.py')

class PlaceIdentityTests(unittest.TestCase):
    def test_all_settlements_have_stable_distinct_original_names(self):
        rows=[identity.place_identity(f'settlement_{r}_{c}') for r in range(6) for c in range(6)]
        self.assertEqual(len({r['name'] for r in rows}),36)
        self.assertEqual(identity.place_identity('settlement_2_4')['name'],rows[16]['name'])
        self.assertTrue(identity.place_identity('base-oracle','military')['name'].startswith('Base militaire de '))
        self.assertNotEqual(identity.place_identity('port-a','port')['name'],identity.place_identity('port-b','port')['name'])
        with self.assertRaises(ValueError): identity.place_identity('../escape')

    def test_sign_proposals_preserve_places_and_ignore_empty_sites(self):
        plan={'settlements':[dict(id='settlement_0_0',east=123,north=456,buildingCount=160),dict(id='settlement_0_1',east=0,north=0,buildingCount=0)]}
        signs=identity.settlement_signs(plan)
        self.assertEqual(len(signs),2)
        self.assertEqual(signs[0]['id'],'settlement_0_0')
        self.assertEqual(signs[0]['east'],135)
        self.assertEqual(signs[0]['kind'],'city')
        self.assertEqual(plan['settlements'][0]['east'],123)
        plan['settlements'].append(plan['settlements'][0])
        with self.assertRaises(ValueError): identity.settlement_signs(plan)

    def test_original_sign_is_deterministic_materialled_full_scale_geometry(self):
        data=sign.build();self.assertEqual(data,sign.build())
        magic,version,length=struct.unpack_from('<III',data)
        self.assertEqual((magic,version,length),(0x46546c67,2,len(data)))
        size=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+size])
        self.assertEqual(len(doc['materials']),3)
        positions=[doc['accessors'][p['attributes']['POSITION']] for p in doc['meshes'][0]['primitives']]
        self.assertGreater(sum(p['count'] for p in positions),1000)
        self.assertAlmostEqual(min(p['min'][1] for p in positions),0)
        self.assertAlmostEqual(max(p['max'][0] for p in positions),1.4,places=5)
        self.assertAlmostEqual(max(p['max'][1] for p in positions),2.325,places=5)

    def test_coastal_entrances_can_move_into_the_same_towns_reserved_corridor(self):
        signs=identity.settlement_signs({'settlements':[dict(id='settlement_0_4',east=1000,north=2000,buildingCount=120)]})
        for item in signs:
            rows=list(identity.sign_candidates(item))
            self.assertEqual(rows[0],dict(east=item['east'],north=item['north']))
            self.assertEqual(len({(r['east'],r['north']) for r in rows}),40)
            self.assertTrue(all(abs(r['east']-1000)<=18 and abs(r['north']-2000)<=410 for r in rows))
            self.assertTrue(any(r['north']==2000 for r in rows))
        buildings=[dict(id='settlement_0_4_house_1_1',east=1250,north=1800,width=10,depth=12),
                   dict(id='settlement_0_5_house_1_1',east=9000,north=9000,width=10,depth=12)]
        fallback=list(identity.sign_candidates(signs[0],buildings))[40:]
        self.assertEqual(len(fallback),4)
        self.assertTrue(all(abs(r['east']-1250)<=9.5 and abs(r['north']-1800)<=10.5 for r in fallback))

if __name__=='__main__': unittest.main()
