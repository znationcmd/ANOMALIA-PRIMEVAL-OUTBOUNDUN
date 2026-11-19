import importlib.util,pathlib,tempfile,zipfile,json,struct,unittest,urllib.parse
spec=importlib.util.spec_from_file_location('repair',str(pathlib.Path(__file__).resolve().parents[1]/'scripts/ue5/repair-conflicting-model-archive-paths.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class RepairTests(unittest.TestCase):
 def archive(self,root,entries):
  source=root/'source.zip'
  with zipfile.ZipFile(source,'w') as z:
   for name,data in entries:z.writestr(name,data)
  r=m.Repair(source,root/'output',0);r.extract();return r
 def test_case_collisions_and_colon_texture_references(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);g={'asset':{'version':'2.0'},'images':[{'uri':'textures/Main3:color.png'},{'uri':'textures/color.png'},{'uri':'textures/Color.png'}]}
   r=self.archive(root,[('model.gltf',json.dumps(g)),('textures/Main3:color.png',b'colon'),('textures/color.png',b'lower'),('textures/Color.png',b'upper')])
   models,errors=r.models();self.assertEqual(errors,[]);out=pathlib.Path(models[0]['prepared']);result=json.loads(out.read_text())
   self.assertEqual([(out.parent/urllib.parse.unquote(i['uri'])).read_bytes() for i in result['images']],[b'colon',b'lower',b'upper'])
   self.assertTrue((root/'source.zip').is_file())
 def test_different_duplicate_names_remain_ambiguous(self):
  with tempfile.TemporaryDirectory() as d:
   r=self.archive(pathlib.Path(d),[('model.gltf',json.dumps({'images':[{'uri':'texture.png'}]})),('texture.png',b'first'),('texture.png',b'other')])
   models,errors=r.models();self.assertFalse(models);self.assertIn('Ambiguous',errors[0]['reason'])
   self.assertEqual(len(list((r.root/'Files').rglob('src_texture.png'))),2)
 def test_identical_bytes_have_one_retained_file(self):
  with tempfile.TemporaryDirectory() as d:
   r=self.archive(pathlib.Path(d),[('one.png',b'same'),('two.png',b'same')]);self.assertEqual(r.rows[0]['path'],r.rows[1]['path'])
 def test_obj_material_and_texture_references(self):
  with tempfile.TemporaryDirectory() as d:
   r=self.archive(pathlib.Path(d),[('source/model.obj','mtllib material.mtl\nv 0 0 0\n'),('source/material.mtl','newmtl paint\nmap_Kd ../textures/a:b.png\n'),('textures/a:b.png',b'pixels')]);models,errors=r.models();self.assertFalse(errors)
   obj=pathlib.Path(models[0]['prepared']);mtl=obj.parent/obj.read_text().splitlines()[0].split(' ',1)[1];texture=mtl.parent/mtl.read_text().splitlines()[1].split(' ',1)[1]
   self.assertEqual(texture.read_bytes(),b'pixels')
 def test_glb_binary_chunk_preserved(self):
  with tempfile.TemporaryDirectory() as d:
   payload=json.dumps({'asset':{'version':'2.0'},'buffers':[{'byteLength':4}]}).encode();payload+=b' '*((-len(payload))%4);binary=b'ABCD'
   body=struct.pack('<II',len(payload),0x4e4f534a)+payload+struct.pack('<II',4,0x004e4942)+binary;blob=struct.pack('<III',0x46546c67,2,len(body)+12)+body
   r=self.archive(pathlib.Path(d),[('mesh.glb',blob)]);models,errors=r.models();self.assertFalse(errors);self.assertEqual(pathlib.Path(models[0]['prepared']).read_bytes()[-4:],binary)
 def test_traversal_and_network_dependency_rejected(self):
  with self.assertRaises(ValueError):m.safe_member('../outside.png')
  with tempfile.TemporaryDirectory() as d:
   r=self.archive(pathlib.Path(d),[('model.gltf',json.dumps({'images':[{'uri':'https://example.com/private.png'}]}))]);models,errors=r.models();self.assertFalse(models);self.assertIn('External dependency',errors[0]['reason'])

if __name__=='__main__':unittest.main()
