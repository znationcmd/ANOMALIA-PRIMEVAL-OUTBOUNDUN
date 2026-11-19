import hashlib,importlib.util,json,pathlib,struct,tempfile,unittest,zipfile

ROOT=pathlib.Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("prepare68",ROOT/"scripts/ue5/prepare-container-security-68.py")
MODULE=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(MODULE)
PACK=ROOT/"unreal/SourceAssets/ContainerSecurity68/Original.zip"

class OriginalContainerPackTests(unittest.TestCase):
    def test_verified_pack_and_twelve_geometry_preserving_material_conversions(self):
        blob=PACK.read_bytes()
        self.assertEqual(hashlib.sha256(blob).hexdigest(),MODULE.PACK_SHA)
        material_names=set()
        with zipfile.ZipFile(PACK) as z:
            for kind,stem in (("Keys","ContainerKey"),("Locks","ContainerLock")):
                for color in MODULE.COLORS:
                    with self.subTest(kind=kind,color=color):
                        name=stem+"_"+color
                        original=z.read("Models/"+kind+"/"+name+".glb")
                        prepared,checks=MODULE.prepare(original,name)
                        self.assertTrue(checks["geometryBinaryUnchanged"])
                        self.assertEqual(checks["preparedMeshes"],1)
                        self.assertEqual(checks["primitives"],12)
                        source_chunks=dict(MODULE.chunks(original));out_chunks=dict(MODULE.chunks(prepared))
                        self.assertEqual(source_chunks[0x004e4942],out_chunks[0x004e4942])
                        source=json.loads(source_chunks[0x4e4f534a]);out=json.loads(out_chunks[0x4e4f534a])
                        self.assertEqual(len(out["nodes"]),1)
                        self.assertEqual(out["scenes"],[{"nodes":[0]}])
                        source_primitives=[p for m in source["meshes"] for p in m["primitives"]]
                        for before,after in zip(source_primitives,out["meshes"][0]["primitives"]):
                            self.assertEqual(before["indices"],after["indices"])
                            for key,index in before["attributes"].items():
                                if key!="COLOR_0":self.assertEqual(after["attributes"][key],index)
                            if "COLOR_0" in before["attributes"]:
                                rgba=MODULE.color_value(source,source_chunks[0x004e4942],before["attributes"]["COLOR_0"])
                                self.assertEqual(out["materials"][after["material"]]["pbrMetallicRoughness"]["baseColorFactor"],rgba)
                                self.assertNotIn("COLOR_0",after["attributes"])
                        for material in out["materials"]:
                            self.assertNotIn(material["name"],material_names)
                            material_names.add(material["name"])
        self.assertEqual(PACK.read_bytes(),blob)

    def test_animated_or_transformed_source_is_preserved_instead_of_silently_collapsed(self):
        with zipfile.ZipFile(PACK) as z:blob=z.read("Models/Keys/ContainerKey_Blue.glb")
        parts=MODULE.chunks(blob);g=json.loads(parts[0][1]);g["nodes"][0]["translation"]=[1,2,3]
        payload=json.dumps(g).encode();payload+=b" "*((-len(payload))%4)
        body=b"".join(struct.pack("<II",len(v),k)+v for k,v in [(parts[0][0],payload)]+parts[1:])
        transformed=struct.pack("<III",0x46546c67,2,len(body)+12)+body
        with self.assertRaisesRegex(ValueError,"Transforms"):
            MODULE.prepare(transformed,"DoNotFlatten")

if __name__=="__main__":unittest.main()
