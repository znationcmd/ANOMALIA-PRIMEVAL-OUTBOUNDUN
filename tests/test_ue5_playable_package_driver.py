"""Packaging orchestration regressions, without claiming a real Unreal build."""
import json
import os
from pathlib import Path
import runpy
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

DRIVER = Path(__file__).resolve().parents[1] / 'scripts/ue5/package-playable-windows.py'


class PlayablePackageDriverTests(unittest.TestCase):
    def rejected_scene(self, receipt):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            # A valid old result must not satisfy the next invocation.
            (root / 'scene-old.json').write_text(json.dumps(dict(
                state='PLAYABLE_LOOK_V2_SAVED', sourceCommit='test-source', dynamicLights=True)))
            commands = []

            def invoke(command, **kwargs):
                commands.append(command)
                if receipt is not None:
                    Path(os.environ['ANOMALIA_PLAYABLE_ZONE_REPORT']).write_text(json.dumps(receipt))
                return SimpleNamespace(returncode=0)

            args = [str(DRIVER), '--engine-root', str(root / 'engine'), '--output', str(root)]
            with patch.dict(os.environ, {'GITHUB_SHA': 'test-source'}), \
                    patch('sys.argv', args), patch('subprocess.run', side_effect=invoke):
                with self.assertRaises(SystemExit) as stopped:
                    runpy.run_path(str(DRIVER), run_name='__main__')
            self.assertEqual(stopped.exception.code, 1)
            self.assertEqual(len(commands), 1, 'Never package an old map after failed scene verification')
            report = json.loads((root / 'package-report.json').read_text())
            self.assertEqual(report['state'], 'FAILED')
            self.assertNotIn('packageExitCode', report)
            self.assertNotIn('native', report)

    def test_zero_editor_exit_and_old_receipt_do_not_prove_scene_was_updated(self):
        self.rejected_scene(None)

    def test_wrong_source_or_unapplied_lights_block_packaging(self):
        for commit, lights in [('old-source', True), ('test-source', False)]:
            with self.subTest(commit=commit, lights=lights):
                self.rejected_scene(dict(state='PLAYABLE_LOOK_V2_SAVED', sourceCommit=commit,
                                         dynamicLights=lights))


if __name__ == '__main__':
    unittest.main()
