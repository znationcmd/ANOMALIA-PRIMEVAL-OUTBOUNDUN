"""Reproduce the original RACCONIA heightmap scale and 1009 UE5 import."""
from __future__ import annotations
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/ue5/worldgen/prepare_racconia_import_grade.py"
spec=importlib.util.spec_from_file_location("racconia_import_grade",SCRIPT)
script=importlib.util.module_from_spec(spec)
spec.loader.exec_module(script)


def make_source(path:Path):
    img=Image.new("I;16",(1025,1025),33280)
    stream=io.BytesIO()
    img.save(stream,format="PNG")
    data={
        "map":"RACCONIA-VARKOVIA","landscapeWidthKm":16,
        "landscapeHeightKm":16,"origin":"southwest","unit":"km",
        "sites":[{"id":"AZS_"+str(i),"name":"Sample "+str(i),
             "x_km":6+i/50,"y_km":8+i/100,"ground_elevation_m":100}
             for i in range(29)],
        "roads":[{"id":"R"+str(i),"type":"liaison_maritime" if i>=28 else "chemin",
             "points_km":[[7,8],[8,8]]}for i in range(33)]
    }
    # Exactly FIVE maritime route source records.
    for i,r in enumerate(data["roads"]):
        r["type"]="liaison_maritime" if i>=28 else "chemin"
    with zipfile.ZipFile(path,"w") as zipout:
        zipout.writestr(script.SOURCE_PNG,stream.getvalue())
        zipout.writestr(script.SOURCE_JSON,json.dumps(data))
    return path


class HeightmapSourceTests(unittest.TestCase):
    def test_landscape_vertical_scale_is_2500_and_res_1009(self):
        self.assertAlmostEqual(script.elevation(33280),100,places=5)
        with tempfile.TemporaryDirectory() as td:
            src=make_source(Path(td)/"original.zip")
            original=src.read_bytes()
            out=Path(td)/"import-ready"
            report=script.build(src,out)
            self.assertEqual(report["originalSites"],29)
            self.assertEqual(report["originalRoutes"],33)
            self.assertEqual(report["maritimeRoutes"],5)
            self.assertEqual(report["unrealLandscape"]["scaleCm"][2],2500)
            self.assertEqual(report["unrealLandscape"]["components"],[8,8])
            height=(out/"RACCONIA_16KM_1009_NORTH_UP.r16").read_bytes()
            self.assertEqual(len(height),1009*1009*2)
            with Image.open(out/"RACCONIA_16KM_1009_NORTH_UP.png") as im:
                self.assertEqual(im.mode,"I;16")
                self.assertEqual(im.size,(1009,1009))
            self.assertLess(report["maxSiteHeightDifferenceMetres"],.01)
            self.assertFalse(report["nativeUnrealLevelCreated"])
            self.assertFalse(report["sourceFilesOverwritten"])
            self.assertEqual(src.read_bytes(),original)
            with self.assertRaises(FileExistsError):
                script.build(src,out)

    def test_preserve_source_orientation_and_bilinear(self):
        im=Image.new("I;16",(1025,1025),32768)
        im.putpixel((0,0),32768)
        im.putpixel((0,1024),33792)
        self.assertEqual(script.bilinear(im,0,0),32768)
        self.assertEqual(script.bilinear(im,0,16),33792)


if __name__=="__main__":
    unittest.main()
