"""Regress actual Windows path failure without needing an Unreal installation."""
from pathlib import Path
import hashlib
import importlib.util
import json
import struct
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('short_import',ROOT/'unreal/Scripts/short_import_source.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def glb(doc, binary=b'\x00\x01\x02\x03'):
    text=json.dumps(doc).encode();text+=b' '*(-len(text)%4)
    body=struct.pack('<II',len(text),module.JSON_CHUNK)+text+struct.pack('<II',len(binary),0x004E4942)+binary
    return struct.pack('<III',0x46546C67,2,12+len(body))+body


class ShortImportTests(unittest.TestCase):
    def test_geometry_binary_indices_and_copyright_survive_short_name_copy(self):
        doc={'asset':{'version':'2.0','copyright':'Artist CC BY 4.0 credit'},
             'nodes':[{'name':'very_long_artist_name'*10,'mesh':0,'translation':[1,2,3]}],
             'meshes':[{'name':'long_model_name','primitives':[{'attributes':{'POSITION':0},'material':0}]}],
             'materials':[{'name':'long_material_name','extras':{'credit':'Artist'}}],
             'buffers':[{'byteLength':4}], 'bufferViews':[{'buffer':0,'byteOffset':0,'byteLength':4}]}
        original=glb(doc)
        shortened=module.normalized_glb(original)
        size=struct.unpack_from('<I',shortened,12)[0];actual=json.loads(shortened[20:20+size])
        self.assertEqual(actual['asset'],doc['asset'])
        self.assertEqual(actual['nodes'][0]['translation'],[1,2,3])
        self.assertEqual(actual['meshes'][0]['primitives'],doc['meshes'][0]['primitives'])
        self.assertEqual(actual['bufferViews'],doc['bufferViews'])
        self.assertEqual(actual['materials'][0]['extras'],doc['materials'][0]['extras'])
        self.assertEqual(shortened[-12:],original[-12:])
        self.assertEqual(actual['nodes'][0]['name'],'n0')
        self.assertEqual(struct.unpack_from('<I',shortened,8)[0],len(shortened))

    def test_original_and_modified_user_copy_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'artist_original_very_long_filename.glb'
            original=glb({'asset':{'version':'2.0'},'nodes':[{'name':'long_name'}]})
            source.write_bytes(original);sha=hashlib.sha256(original).hexdigest()
            path,proof=module.prepare_short_import(root,source,sha)
            self.assertEqual(path.name,'m.glb')
            self.assertEqual(source.read_bytes(),original)
            self.assertFalse(proof['geometryChanged'])
            self.assertEqual(module.prepare_short_import(root,source,sha)[0],path)
            path.write_bytes(b'user edit')
            with self.assertRaisesRegex(ValueError,'preserved'):
                module.prepare_short_import(root,source,sha)
            self.assertEqual(path.read_bytes(),b'user edit')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):
                module.prepare_short_import(root,source,'0'*64)

    def test_repaired_import_uses_new_namespace_without_changing_existing_paths(self):
        old='/Game/Anomalia/NamedVehicles1/SM_audi_a3'
        self.assertEqual(module.canonical_destination('NamedVehicles1',old),'/Game/Anomalia/NamedVehicles2/SM_audi_a3')
        self.assertEqual(module.canonical_destination('Metro1',old),old)
        self.assertEqual(module.review_version('NamedVehicles1'),'v2')
        self.assertEqual(module.review_version('Military2'),'v1')

    def test_external_dependencies_and_truncated_files_are_rejected(self):
        with self.assertRaises(ValueError):
            module.normalized_glb(glb({'asset':{'version':'2.0'},'images':[{'uri':'artist.png'}]}))
        with self.assertRaises(ValueError):
            module.normalized_glb(glb({'asset':{'version':'2.0'}})[:-1])


if __name__=='__main__':unittest.main()
