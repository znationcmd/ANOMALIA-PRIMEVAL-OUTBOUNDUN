"""Numerical checks for the real urban review scene layout and open pool recesses."""
import importlib.util
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
