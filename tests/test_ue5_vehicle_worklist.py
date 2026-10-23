"""Preserve later sourcing evidence while validating the original requests."""
import copy,importlib.util,json,shutil,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('worklist',ROOT/'scripts/vehicle-requirements/audit-requested-vehicles.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class WorklistTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        shutil.copytree(ROOT/'docs/vehicles',self.root/'docs/vehicles')
        self.savedroot=module.ROOT;module.ROOT=self.root
    def tearDown(self):module.ROOT=self.savedroot;self.tmp.cleanup()
    def run_main(self,*args):
        with patch.object(sys,'argv',['audit',*args]):module.main()
    def test_sourcing_and_manual_notes_survive_regeneration(self):
        path=self.root/'docs/vehicles/full-vehicle-worklist.json';before=json.loads(path.read_text())
        before['requests'][0]['reviewNote']='Artist confirmation retained'
        path.write_text(json.dumps(before))
        md=self.root/'docs/vehicles/FULL_VEHICLE_WORKLIST.md';md.write_text(md.read_text()+'\nManual artist evidence retained.\n')
        self.run_main('--check');self.run_main();after=json.loads(path.read_text())
        for key in ['sourcingPolicy','sourcingSources','supplementarySourcing','recentSearchDecisions','sourcingSummary','environmentSourcingIndex']:
            self.assertEqual(before[key],after[key])
        self.assertEqual(after['requests'][0]['reviewNote'],'Artist confirmation retained')
        self.assertIn('Manual artist evidence retained.',md.read_text());self.run_main('--check')
    def test_missing_request_and_changed_original_label_are_rejected(self):
        path=self.root/'docs/vehicles/full-vehicle-worklist.json';before=json.loads(path.read_text())
        bad=copy.deepcopy(before);bad['requests'].pop();path.write_text(json.dumps(bad))
        with self.assertRaises(RuntimeError):self.run_main('--check')
        bad=copy.deepcopy(before);bad['requests'][0]['requestedLabel']='Different vehicle';path.write_text(json.dumps(bad))
        with self.assertRaises(RuntimeError):self.run_main('--check')
if __name__=='__main__':unittest.main()
