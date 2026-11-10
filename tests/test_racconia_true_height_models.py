"""Run with: python -m unittest discover -s tests -p test_racconia_true_height_models.py"""
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

import numpy as np
from PIL import Image
import trimesh

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/ue5/worldgen/prepare_racconia_ue5_v2.py"
spec=importlib.util.spec_from_file_location("true_racconia_source",SCRIPT)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def sample_source(dest:Path):
    arr=np.full((1025,1025),32768+512,dtype=np.uint16)  # Exactly 100 m.
    stream=io.BytesIO()
    Image.fromarray(arr).save(stream,format="PNG")
    cube=trimesh.creation.box(extents=(4,4,4))
    # Every geometry can be a simple independent model in a synthetic test.
    mesh=cube.scene().export(file_type="glb")
    sites=[]
    for idx in range(29):
        sites.append({
          "id":"AZS_"+str(idx+1).zfill(2),"name":"Existing Site",
          "x_km":8.0+(idx-15)*.01,"y_km":8.0,
          "ground_elevation_m":100.0
        })
    roads=[]
    for idx in range(33):
        roads.append({"id":f"R{idx:03}","type":"liaison_maritime" if idx<5 else "chemin",
          "points_xyz_m":[[7.0,7.0,100.],[9.0,9.0,100.]]})
    payload={"map":"RACCONIA-VARKOVIA","landscapeWidthKm":16,
             "landscapeHeightKm":16,"sites":sites,"roads":roads}
    with zipfile.ZipFile(dest,"w") as z:
        z.writestr(mod.SOURCE,json.dumps(payload,ensure_ascii=False))
        z.writestr(mod.HEIGHT,stream.getvalue())
        z.writestr("Terrain/LandMask_1025.png",b"land")
        for x in mod.SITE_MODELS:
            z.writestr("Models/SM_"+x+"_BLOCKOUT.glb",mesh)


class CorrectedTerrainTests(unittest.TestCase):
    def test_pixel_height_100m_is_100_not_4(self):
        self.assertEqual(mod.decode_metres(32768+512),100)
        self.assertEqual(mod.euclidean_site_km_to_ue_cm(8,8),[0,0])
        self.assertEqual(mod.euclidean_site_km_to_ue_cm(16,0),[800000,-800000])
        src=np.full((1025,1025),33280,dtype=np.uint16)
        out=mod.resample_height(src)
        self.assertEqual(out.shape,(1009,1009))
        self.assertEqual(str(out.dtype),"uint16")
        self.assertEqual(int(out[1000,1000]),33280)

    def test_29_real_geometry_exports_and_native_level_not_claimed(self):
        with tempfile.TemporaryDirectory() as td:
            z=Path(td)/"source.zip"
            out=Path(td)/"new-staging"
            sample_source(z)
            digest=z.read_bytes()
            report=mod.create(z,out)
            self.assertEqual(report["scaleCm"]["z"],2500)
            self.assertEqual(report["modelCount"],29)
            self.assertEqual(report["roadCount"],33)
            self.assertEqual(report["marineRoadCount"],5)
            self.assertEqual(report["originalSiteHeightMaxAbsoluteErrorMetres"],0)
            self.assertTrue(report["noNativeUELevel"])
            self.assertTrue(report["notPlayable"])
            self.assertEqual(len(list((out/"Models_OBJ_UE5_CM").glob("*.obj"))),29)
            self.assertEqual((out/"Terrain/RACCONIA_VARKOVIA_1009x1009.r16").stat().st_size,
                             1009*1009*2)
            self.assertEqual(z.read_bytes(),digest)
            with self.assertRaises(FileExistsError):
                mod.create(z,out)

if __name__=="__main__":
    unittest.main()
