"""Offline nine-world identity and CHERNASKALUXRIA 100 km map-source tests."""
import importlib.util
import json
import math
import unittest
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def source():
    sys.path.insert(0,str(ROOT/"scripts/ue5"))
    file=ROOT/"scripts/ue5/chernaskaluxria_world.py"
    spec=importlib.util.spec_from_file_location("chernaskaluxria_test_source",file)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class NinthWorldTest(unittest.TestCase):
    def test_9_separate_worlds_and_unique_server_paths(self):
        maps=json.loads((ROOT/"public/config/anomalia-map-catalog.json").read_text())["maps"]
        assert len(maps)==10
        assert len({v["id"] for v in maps})==10
        assert len({v["saveNamespace"] for v in maps})==10
        assert len({v["originalUnrealPackage"] for v in maps})==10
        assert sum(v["widthKm"]*v["heightKm"] for v in maps)==17533
        world=next(v for v in maps if v["displayName"]=="CHERNASKALUXRIA")
        assert world["id"]=="chernaskaluxria-v1"
        assert world["originalUnrealPackage"]=="/Game/Maps/PRIGIMALIA_CHERNASKALUXRIA"
        assert world["widthKm"]==100 and world["heightKm"]==100
        assert world["serverSelectable"] is False
        native=(ROOT/"unreal/Source/AnomaliaZPrigimalia/AnomaliaZPrigimaliaServerBrowserLibrary.cpp").read_text()
        assert 'TEXT("chernaskaluxria-v1")' in native
        assert 'TEXT("/Game/Maps/PRIGIMALIA_CHERNASKALUXRIA")' in native

    def test_source_plan_400_independent_import_tiles_not_nine_maps(self):
        m=source()
        s=m.world_manifest()
        tiles=s["tiles"]
        assert s["tileCount"]==400 and len(tiles)==400
        assert s["tileGrid"]==[20,20]
        assert s["tileSideKm"]==5
        assert s["globalHeightSamplesPerAxis"]==20161
        assert math.isclose(s["sampleSpacingMetres"],5000/1008)
        assert s["unrealPackage"]=="/Game/Maps/PRIGIMALIA_CHERNASKALUXRIA"
        assert len(s["regions"])==9
        assert len({t["tileId"] for t in tiles})==400
        assert all(not t["nativeLandscapeImported"] for t in tiles)
        assert s["gameplayValidated"] is False
        assert s["existingMapsModified"] is False
        by_xy={(t["col"],t["row"]):t for t in tiles}
        for row in range(20):
            for col in range(20):
                cur=by_xy[(col,row)]["boundsMetres"]
                assert cur["east"]-cur["west"]==5000
                assert cur["north"]-cur["south"]==5000
                if col<19:assert cur["east"]==by_xy[col+1,row]["boundsMetres"]["west"]
                if row<19:assert cur["south"]==by_xy[col,row+1]["boundsMetres"]["north"]

    def test_original_biomes_and_heightfield_are_continuous(self):
        m=source()
        regions=set(m.NAMES)
        assert len(regions)==9
        covered={t["dominantBiome"] for t in m.world_tiles()}
        assert covered==regions, "Every biome needs a region on the 100 km map"
        for name,x,y,_,_ in m.REGIONS:
            w=m.region_weights(x*1000.,y*1000.)
            assert abs(sum(w.values())-1)<1e-10
            assert name in w
        samples=[(0,0),(-48000,1000),(-36000,-34000),(27000,-27000),
                 (26000,35000),(32000,8000),(-23000,33000)]
        for e,n in samples:
            h=m.terrain_height(e,n)
            assert math.isfinite(h) and -500<h<2000
            assert h==m.terrain_height(e,n)
            assert abs(h-m.terrain_height(e+.01,n))<2
        assert m.terrain_height(55000,0)==-250

if __name__=="__main__":
    unittest.main()
