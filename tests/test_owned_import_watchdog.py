import importlib.util,unittest,copy
spec=importlib.util.spec_from_file_location('watchdog',str(__import__('pathlib').Path(__file__).resolve().parents[1]/'scripts/ue5/run-owned-model-import-with-watchdog.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class WatchdogReceiptTests(unittest.TestCase):
 def fixture(self):
  manifest={'imports':[{'sha256':'done','source':'done.glb','preparedSHA256':'p1','family':'one'},{'sha256':'pending','source':'pending.fbx','preparedSHA256':'p2','family':'two'}]}
  report={'sources':[{'sha256':'done','state':'RESUMED_IMPORTED_SAVED_RELOADED_NOT_GAMEPLAY_ACCEPTED','assets':[{'path':'existing real mesh'}]}],'errors':[]}
  active={'state':'IMPORTING_SOURCE','sha256':'pending','preparedSHA256':'p2','destination':'owned/partial'}
  return manifest,report,active
 def test_timeout_preserves_completed_assets_and_identifies_only_stalled_source(self):
  manifest,report,active=self.fixture();original=copy.deepcopy(report['sources']);out=m.retain_timeout(manifest,report,active)
  self.assertEqual(out['sources'],original);self.assertEqual(out['completedSourceCount'],1);self.assertEqual(out['failedSourceCount'],1);self.assertEqual(out['errors'][0]['sha256'],'pending');self.assertFalse(out['errors'][0]['originalDeleted']);self.assertFalse(out['gameplayAccepted'])
 def test_unknown_or_changed_source_is_not_marked_failed(self):
  manifest,report,active=self.fixture()
  with self.assertRaises(ValueError):m.retain_timeout(manifest,report,None)
  active['preparedSHA256']='changed'
  with self.assertRaises(ValueError):m.retain_timeout(manifest,report,active)
  self.assertEqual(report['errors'],[])
 def test_completed_source_is_never_reclassified_as_failed(self):
  manifest,report,active=self.fixture();active.update(sha256='done',preparedSHA256='p1');m.retain_timeout(manifest,report,active);self.assertEqual(report['errors'],[])
 def test_empty_pending_set_and_known_failures_remain_distinct(self):
  manifest,report,active=self.fixture();report['errors']=[{'sha256':'pending'}];done,failed,pending=m.pending_status(manifest,report);self.assertEqual(done,{'done'});self.assertEqual(failed,{'pending'});self.assertFalse(pending)
if __name__=='__main__':unittest.main()
