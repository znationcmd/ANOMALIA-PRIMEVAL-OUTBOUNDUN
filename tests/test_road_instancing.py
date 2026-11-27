"""Road cluster planner tests; require no Unreal installation."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"scripts/ue5/worldgen/plan_road_instancing.py"
spec=importlib.util.spec_from_file_location("road_instancing_plan",SOURCE)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def road(i,x=1000.0,y=1000.0):
    return {"class":"StaticMeshActor","id":f"SKARVIK_ROAD_{i:05d}",
        "centerCm":[x,y,12.],"mesh":"/Game/Road/Kit_City_Road/SM_ROAD_19_10_0_0_road",
        "materialSignature":"CitySample-Shared",
        "collisionProfile":"BlockAll","runtimeGrid":"MainGrid","dataLayer":"Roads",
        "mobility":"Static","spatiallyLoaded":True,"hasGameplayState":False}


class InstancingTest(unittest.TestCase):
    def test_9765_reused_pieces_in_128_m_cells(self):
        # Synthetic stress case, not a claim about actual SKARVIK cell counts.
        source=[road(i,x=(i%80)*400,y=(i//80)*400) for i in range(9765)]
        p=mod.plan(source)
        self.assertEqual(p["sourceActors"],9765)
        self.assertEqual(sum(x["instanceCount"] for x in p["clusters"]),9765)
        self.assertLess(p["targetClusterActors"],100)
        self.assertTrue(all(c["instanceCount"]<=256 for c in p["clusters"]))
        self.assertFalse(p["canDeleteOriginalRoadActors"])
        self.assertTrue(p["cookedPackageSizeNotMeasured"])
        self.assertEqual(len({c["clusterId"] for c in p["clusters"]}),p["targetClusterActors"])

    def test_material_mesh_collision_and_datalayer_never_merge(self):
        src=[road(1),road(2),road(3),road(4),road(5)]
        src[1]["materialSignature"]="Different"
        src[2]["collisionProfile"]="OverlapAll"
        src[3]["dataLayer"]="Special"
        src[4]["mesh"]="/Game/AnotherRoad"
        self.assertEqual(mod.plan(src)["targetClusterActors"],5)

    def test_new_cell_and_negative_coordinates(self):
        a,b,c=road(1,-1,0),road(2,0,0),road(3,12800,0)
        groups=mod.plan([a,b,c])["clusters"]
        self.assertEqual(len(groups),3)
        self.assertEqual(sorted(g["gridXY"][0] for g in groups),[-1,0,1])

    def test_chunk_cap_and_determinism(self):
        batch=[road(i) for i in range(515)]
        a=mod.plan(batch)
        b=mod.plan(list(reversed(batch)))
        self.assertEqual([x["instanceCount"] for x in a["clusters"]],[256,256,3])
        self.assertEqual(a,b)

    def test_invalid_actor_must_be_rejected_not_silently_merged(self):
        for update in ({"materialSignature":None},{"spatiallyLoaded":False},
                       {"hasGameplayState":True},{"mobility":"Movable"},
                       {"centerCm":[float("nan"),0,0]}):
            record=road(1)
            record.update(update)
            with self.assertRaises(ValueError):
                mod.plan([record])

    def test_empty(self):
        out=mod.plan([])
        self.assertEqual(out["targetClusterActors"],0)
        self.assertEqual(out["potentialActorReductionPercent"],0)


if __name__=="__main__":
    unittest.main()
