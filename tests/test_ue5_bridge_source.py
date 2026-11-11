"""Validate the real bridge asset, with geometry and reused image bytes rather than labels."""
import base64,hashlib,json,re,struct,unittest
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
class BridgeSourceTests(unittest.TestCase):
 def test_real_geometry_scale_and_materials(self):
  p=ROOT/'unreal/SourceAssets/Infrastructure/Bridge/bridge50m.glb';b=p.read_bytes();meta=json.loads(p.with_name('manifest.json').read_text())
  self.assertEqual(hashlib.sha256(b).hexdigest(),meta['sha256']);self.assertEqual(struct.unpack_from('<III',b),(0x46546c67,2,len(b)))
  size=struct.unpack_from('<I',b,12)[0];d=json.loads(b[20:20+size]);data=b[28+size:]
  self.assertEqual(len(d['meshes']),1);self.assertEqual(len(d['meshes'][0]['primitives']),3)
  bounds=[]
  for primitive in d['meshes'][0]['primitives']:
   for semantic in ['POSITION','NORMAL']:
    a=d['accessors'][primitive['attributes'][semantic]];v=d['bufferViews'][a['bufferView']]
    arr=np.frombuffer(data,dtype='<f4',count=a['count']*3,offset=v.get('byteOffset',0)).reshape(-1,3)
    self.assertTrue(np.isfinite(arr).all())
    if semantic=='POSITION':bounds.append(arr)
    else:self.assertTrue(np.allclose(np.linalg.norm(arr,axis=1),1,atol=.0001))
  dimensions=np.ptp(np.concatenate(bounds),axis=0)
  self.assertAlmostEqual(dimensions[0],50.11,places=3);self.assertAlmostEqual(dimensions[2],11,places=3);self.assertGreater(dimensions[1],3)
  for image in d['images']:
   v=d['bufferViews'][image['bufferView']];raw=data[v['byteOffset']:v['byteOffset']+v['byteLength']]
   original=(ROOT/'src/textures'/f"{image['name']}.js").read_text()
   self.assertEqual(raw,base64.b64decode(re.search(r'base64,([^";]+)',original).group(1)))
if __name__=='__main__':unittest.main()
