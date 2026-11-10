"""Non-destructive RACCONIA road staging checks (fixture uses original schema)."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
FILE=ROOT/"scripts/ue5/worldgen/audit_racconia_road_access.py"
spec=importlib.util.spec_from_file_location("racconia_road_audit",FILE)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def fixture(path:Path):
    sites=[{"id":f"AZS_{i:02}","name":f"Test Site {i}",
            "x_km":6+i*.1,"y_km":8+i*.03,
            "ground_elevation_m":100.} for i in range(1,30)]
    roads=[]
    for i in range(1,34):
        typ="liaison_maritime" if i>28 else ("route_principale" if i<5 else "chemin")
        x=6+i*.1
        roads.append({"id":f"R{i:03}","type":typ,"from":"A","to":"B",
                      "points_km":[[x,8],[x+.1,8.1]],
                      "points_xyz_m":[[x,8,100.],[x+.1,8.1,101.]]})
    doc={"map":"RACCONIA-VARKOVIA","landscapeWidthKm":16,"landscapeHeightKm":16,
         "heightmapResolution":1025,"origin":"southwest km","sites":sites,"roads":roads}
    with zipfile.ZipFile(path,"w") as z:
        z.writestr(mod.SOURCE,json.dumps(doc))
        z.writestr(mod.HEIGHT,b"\x89PNG"+b"0"*12_000)
        z.writestr(mod.LAND,b"mask")
    return doc


class ExistingWorldAuditTests(unittest.TestCase):
    def test_validate_export_and_preserve_29_sites_33_roads(self):
        with tempfile.TemporaryDirectory() as td:
            kit=Path(td)/"original.zip"
            original=fixture(kit)
            prev=kit.read_bytes()
            data=mod.load_kit(kit)
            report=mod.stage(kit,Path(td)/"new-output")
            self.assertEqual(report["siteCount"],29)
            self.assertEqual(report["roadCount"],33)
            self.assertEqual(report["maritimeCount"],5)
            self.assertEqual(report["landRoadCount"],28)
            self.assertFalse(report["nativeRoadsBuilt"])
            self.assertFalse(report["gameplayReady"])
            self.assertEqual(len(report["siteAccess"]),29)
            self.assertEqual(len(report["routes"]),33)
            self.assertEqual(prev,kit.read_bytes())
            self.assertEqual(len((Path(td)/"new-output/racconia-29-sites-ue5.csv").read_text(
                encoding="utf-8-sig").splitlines()),30)
            self.assertEqual(len((Path(td)/"new-output/racconia-33-routes-ue5.csv").read_text(
                encoding="utf-8-sig").splitlines()),67)
            self.assertEqual(report["siteAccess"][20]["state"],
                             "WATER_SITE_FERRY_OR_BOAT_REVIEW_ONLY")
            with self.assertRaises(FileExistsError):
                mod.stage(kit,Path(td)/"new-output")

    def test_duplicate_site_and_wrong_count_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            kit=Path(td)/"original.zip"
            source=fixture(kit)
            source["sites"][2]["id"]=source["sites"][1]["id"]
            with zipfile.ZipFile(Path(td)/"bad.zip","w") as z:
                z.writestr(mod.SOURCE,json.dumps(source))
                z.writestr(mod.HEIGHT,b"0"*12000)
                z.writestr(mod.LAND,b"m")
            with self.assertRaisesRegex(ValueError,"Duplicate"):
                mod.load_kit(Path(td)/"bad.zip")

    def test_exact_existing_racconia_xy_transform_is_not_skarvik(self):
        self.assertEqual(mod._coords(8,8),(0,0))
        self.assertEqual(mod._coords(9,10),(100000,200000))


if __name__=="__main__":
    unittest.main()
