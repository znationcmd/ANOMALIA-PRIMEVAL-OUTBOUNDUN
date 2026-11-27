import ast
import math
import unittest
from pathlib import Path

SOURCE=Path(__file__).resolve().parents[1]/"unreal/Scripts/author_skarvik_final_safe_town_access_b4.py"
tree=ast.parse(SOURCE.read_text(encoding="utf-8"))
function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="permitted_endpoint_join")
scope={"math":math}
exec(compile(ast.Module(body=[function],type_ignores=[]),str(SOURCE),"exec"),scope)
join=scope["permitted_endpoint_join"]

class JunctionGuardTests(unittest.TestCase):
    def test_only_terminal_areas_can_meet_saved_asphalt(self):
        self.assertTrue(join(0,0,(0,0),(.1,0),100))
        self.assertTrue(join(.004,0,(0,0),(.1,0),100))
        self.assertTrue(join(.096,0,(0,0),(.1,0),100))
        self.assertFalse(join(.006,0,(0,0),(.1,0),100))
        self.assertFalse(join(.05,0,(0,0),(.1,0),100))
        self.assertFalse(join(.15,0,(0,0),(.1,0),100))
    def test_short_lanes_keep_an_interior_overlap_guard(self):
        self.assertTrue(join(.001,0,(0,0),(.01,0),10))
        self.assertFalse(join(.002,0,(0,0),(.01,0),10))
        self.assertFalse(join(.005,0,(0,0),(.01,0),10))
    def test_no_degenerate_or_nonfinite_lane_exemption(self):
        self.assertFalse(join(0,0,(0,0),(0,0),0))
        self.assertFalse(join(0,0,(0,0),(.1,0),float("nan")))

if __name__=="__main__":unittest.main()
