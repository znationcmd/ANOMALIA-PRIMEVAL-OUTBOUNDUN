import pathlib,importlib.util,unittest
spec=importlib.util.spec_from_file_location('mainmap',str(pathlib.Path(__file__).resolve().parents[1]/'scripts/ue5/prepare-actual-main-map-sm5-check.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class MainMapRoutingTests(unittest.TestCase):
 def test_menu_boot_does_not_substitute_a_test_world_for_skarvik(self):
  source='{TEXT("archipelago-v2"), TEXT("SKARVIK"), TEXT("/Game/Maps/ANOMALIA_Archipelago_v2")}'
  r=m.select_main('[/Script/EngineSettings.GameMapsSettings]\nGameDefaultMap=/Game/Maps/ANOMALIA_Playable_v1',source)
  self.assertEqual(r['mainMap'],'/Game/Maps/ANOMALIA_Archipelago_v2')
 def test_explicit_installed_skarvik_default_is_preserved(self):
  r=m.select_main('[/Script/EngineSettings.GameMapsSettings]\nGameDefaultMap=/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1','')
  self.assertEqual(r['mainMap'],'/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1')
 def test_unresolved_main_route_never_falls_back_to_staging(self):
  with self.assertRaises(ValueError):m.select_main('[/Script/EngineSettings.GameMapsSettings]\nGameDefaultMap=/Engine/Maps/Entry','')
 def test_invalid_route_is_rejected(self):
  with self.assertRaises(ValueError):m.select_main('[/Script/EngineSettings.GameMapsSettings]\nGameDefaultMap=/Game/../SKARVIK','')
if __name__=='__main__':unittest.main()
