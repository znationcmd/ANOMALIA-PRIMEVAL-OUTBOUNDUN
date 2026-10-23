"""Numerical checks for the real urban review scene layout and open pool recesses."""
import importlib.util
import tempfile
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('layout',Path(__file__).resolve().parents[1]/'unreal/Scripts/settlement_layout.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class UrbanLayoutTests(unittest.TestCase):
    def test_buildings_are_separate_and_outside_roads_and_pavements(self):
        plan=module.layout();self.assertEqual(len(plan['buildings']),28)
        ids=set()
        for index,building in enumerate(plan['buildings']):
            self.assertNotIn(building['id'],ids);ids.add(building['id'])
            footprint=module.rectangle(building)
            for other in plan['buildings'][index+1:]:self.assertFalse(module.overlaps(footprint,module.rectangle(other)),(building['id'],other['id']))
            for road in plan['roads']:self.assertFalse(module.overlaps(footprint,module.rectangle(road,2)),(building['id'],road['id']))

    def test_expansion_buildings_fit_the_reserved_parcels(self):
        root=Path(__file__).resolve().parents[1]
        source=importlib.util.spec_from_file_location('parcels_geometry',root/'scripts/ue5/generate-assets-expansion.py')
        geometry=importlib.util.module_from_spec(source);source.loader.exec_module(geometry)
        with tempfile.TemporaryDirectory() as folder:
            manifest=geometry.generate(Path(folder));actual={m['id']:m['dimensionsMetresYUp'] for m in manifest['models']}
        for building in module.layout()['buildings']+module.service_fleet():
            if building['model'] not in actual:continue
            dims=actual[building['model']]
            self.assertLessEqual(dims[0],building['width']+.01,building['id'])
            self.assertLessEqual(dims[2],building['depth']+.01,building['id'])

    def test_emergency_fleet_has_clear_parking_near_each_service(self):
        plan=module.layout();buildings={b['id']:b for b in plan['buildings']}
        fleet=module.service_fleet()
        self.assertEqual({v['model'] for v in fleet},{'police','fire_engine','ambulance'})
        for index,vehicle in enumerate(fleet):
            service=buildings[vehicle['service']]
            self.assertLess((vehicle['x']-service['x'])**2+(vehicle['y']-service['y'])**2,30**2)
            for other in plan['buildings']+fleet[index+1:]:
                self.assertFalse(module.overlaps(module.rectangle(vehicle),module.rectangle(other)),(vehicle['id'],other['id']))
            for road in plan['roads']:
                self.assertFalse(module.overlaps(module.rectangle(vehicle),module.rectangle(road,2)))

    def test_ground_area_is_conserved_except_for_four_pool_recesses(self):
        plan=module.layout();rectangles=module.ground_rectangles(plan['groundBounds'],plan['pools'])
        holes=[module.rectangle(pool) for pool in plan['pools']]
        for index,rect in enumerate(rectangles):
            for other in rectangles[index+1:]:self.assertFalse(module.overlaps(rect,other))
            for hole in holes:self.assertFalse(module.overlaps(rect,hole))
        area=lambda r:(r[2]-r[0])*(r[3]-r[1])
        self.assertAlmostEqual(sum(area(r) for r in rectangles),area(plan['groundBounds'])-sum(area(h) for h in holes))
        self.assertEqual(len(holes),4)
        self.assertEqual(module.layout(),plan)


if __name__=='__main__':unittest.main()
