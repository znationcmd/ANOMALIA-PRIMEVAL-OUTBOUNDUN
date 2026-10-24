"""Exercise actual archive bytes and preservation of server/player data."""
import importlib.util,json,tempfile,unittest,zipfile
from pathlib import Path
SPEC=importlib.util.spec_from_file_location('snapshot',Path(__file__).resolve().parents[1]/'scripts/ue5/world_snapshot.py')
MODULE=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(MODULE)

class SnapshotTests(unittest.TestCase):
 def test_inhabited_backup_preserves_the_other_world_and_all_player_saves(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/'unreal'
   for scope,data in ((MODULE.WORLD_PATHS,b'original'),(MODULE.INHABITED_PATHS,b'populated')):
    m=root/scope[0];m.parent.mkdir(parents=True,exist_ok=True);m.write_bytes(data)
    a=root/scope[1]/'town.uasset';a.parent.mkdir(parents=True);a.write_bytes(data+b'-town')
   result=MODULE.snapshot(root,Path(d)/'backup',MODULE.INHABITED_PATHS)
   with zipfile.ZipFile(result['archive']) as z:
    self.assertEqual(z.read(MODULE.INHABITED_PATHS[0]),b'populated')
    self.assertNotIn(MODULE.WORLD_PATHS[0],z.namelist())
    self.assertEqual(len(json.loads(z.read('snapshot-manifest.json'))),2)
   self.assertEqual((root/MODULE.WORLD_PATHS[0]).read_bytes(),b'original')
   with self.assertRaises(ValueError):MODULE.snapshot(root,Path(d)/'backup',('Saved/Servers',))
 def test_world_archive_is_complete_and_excludes_user_data(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/'unreal';mapfile=root/MODULE.WORLD_PATHS[0];mapfile.parent.mkdir(parents=True);mapfile.write_bytes(b'existing-map')
   actor=root/MODULE.WORLD_PATHS[1]/'0/A/original.uasset';actor.parent.mkdir(parents=True);actor.write_bytes(b'original-actor')
   save=root/'Saved/Servers/server-a/player.json';save.parent.mkdir(parents=True);save.write_bytes(b'private-player')
   result=MODULE.snapshot(root,Path(d)/'backup')
   with zipfile.ZipFile(result['archive']) as z:
    self.assertEqual(z.read(mapfile.relative_to(root).as_posix()),b'existing-map')
    self.assertEqual(z.read(actor.relative_to(root).as_posix()),b'original-actor')
    self.assertFalse(any('Saved' in n for n in z.namelist()))
    self.assertEqual(len(json.loads(z.read('snapshot-manifest.json'))),2)
   mapfile.write_bytes(b'updated-derived-data')
   with zipfile.ZipFile(result['archive']) as z:self.assertEqual(z.read(MODULE.WORLD_PATHS[0]),b'existing-map')
   self.assertEqual(save.read_bytes(),b'private-player')
   next_result=MODULE.snapshot(root,Path(d)/'backup')
   self.assertNotEqual(result['archive'],next_result['archive'])
   self.assertEqual(MODULE.sha256(result['archive']),result['sha256'])
 def test_missing_map_is_refused(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaisesRegex(RuntimeError,'Existing map'):MODULE.snapshot(Path(d)/'absent',Path(d)/'backup')
 def test_symlink_actor_is_refused(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/'unreal';m=root/MODULE.WORLD_PATHS[0];m.parent.mkdir(parents=True);m.write_bytes(b'map')
   actor=root/MODULE.WORLD_PATHS[1]/'linked.uasset';actor.parent.mkdir(parents=True);actor.symlink_to(m)
   with self.assertRaisesRegex(RuntimeError,'Symlink'):MODULE.snapshot(root,Path(d)/'backup')

if __name__=='__main__':unittest.main()
