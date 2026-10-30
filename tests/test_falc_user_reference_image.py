"""Offline photo-driven F.A.L.C terrain tests; reference photo is not uploaded to GitHub."""
from pathlib import Path
import os,sys,tempfile,unittest
import cv2
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/ue5"))
from falc_from_reference_image import build,sha256

class FalcUserImageTest(unittest.TestCase):
    def verify(self,ref:Path,tmp:Path):
        out=tmp/"FALC"
        p=build(ref,out)
        self.assertEqual(p["mapId"],"falc-v1")
        self.assertEqual(p["totalKm2"],702.25)
        self.assertEqual(p["unrealPackage"],"/Game/Maps/PRIGIMALIA_FALC")
        self.assertEqual(p["referenceImageSha256"],sha256(ref))
        self.assertFalse(p["drazoviaReadOrModified"])
        self.assertFalse(p["realAltitudeDEM"])
        self.assertFalse(p["nativeUmapBuilt"])
        self.assertEqual(len(p["tiles"]),4)
        r=lambda x,y:np.fromfile(out/f"FALC_x{x:02d}_y{y:02d}.r16",dtype="<u2").reshape(1009,1009)
        a,b,c,d=r(0,0),r(1,0),r(0,1),r(1,1)
        self.assertTrue(np.array_equal(a[:,-1],b[:,0]))
        self.assertTrue(np.array_equal(c[:,-1],d[:,0]))
        self.assertTrue(np.array_equal(a[-1,:],c[0,:]))
        self.assertTrue(np.array_equal(b[-1,:],d[0,:]))
        self.assertEqual((out/"FALC_26_5KM_MASTER_2017.r16").stat().st_size,2017**2*2)
        with self.assertRaises(FileExistsError):build(ref,out)

    def test_offline_mock_reference(self):
        with tempfile.TemporaryDirectory() as dirname:
            tmp=Path(dirname)
            img=np.full((620,620,3),(86,53,8),dtype=np.uint8)
            cv2.ellipse(img,(310,310),(225,200),0,0,360,(65,103,95),-1)
            cv2.circle(img,(555,555),40,(65,103,95),-1)
            ref=tmp/"photo.jpg"
            cv2.imwrite(str(ref),img)
            self.verify(ref,tmp)

    def test_actual_user_photo_if_available(self):
        path=os.environ.get("FALC_REFERENCE_IMAGE","")
        if not path or not Path(path).is_file():
            self.skipTest("Exact user photo not stored in public GitHub")
        with tempfile.TemporaryDirectory() as dirname:
            self.verify(Path(path),Path(dirname))

if __name__=="__main__":unittest.main()
