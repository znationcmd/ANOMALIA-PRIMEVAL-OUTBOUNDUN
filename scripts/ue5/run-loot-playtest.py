"""Create a separate real map and exercise Interact, inventory UI and persistence in PIE."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import uuid

p = argparse.ArgumentParser()
p.add_argument('--engine-root', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
root = Path(__file__).resolve().parents[2]
out = (a.output / ('loot-pie-' + uuid.uuid4().hex)).resolve()
out.mkdir(parents=True)
report = dict(state='FAILED', sourceCommit=os.environ.get('GITHUB_SHA'), mode='Play In Editor',
              renderingValidated=False, multiplayerTested=False, automationReport=str(out))
editor = a.engine_root / 'Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
base = [str(editor), str(root / 'unreal/AnomaliaZPrigimalia.uproject'), '-unattended', '-nopause', '-nosound', '-NullRHI']
try:
    create = base + [f'-ExecutePythonScript={root / "unreal/Scripts/create_loot_review.py"}', f'-abslog={out / "create.engine.log"}']
    with (out / 'create.process.log').open('w', encoding='utf-8') as log:
        result = subprocess.run(create, stdout=log, stderr=subprocess.STDOUT, timeout=180, check=False)
    report['createExitCode'] = result.returncode
    if result.returncode or not (root / 'unreal/Content/Maps/ANOMALIA_LootReview_v1.umap').is_file():
        raise RuntimeError('Actual loot review map creation failed')
    command = base + [f'-AnomaliaAutomationServerId=loot-pie-{uuid.uuid4().hex}',
                      '-ExecCmds=Automation RunTests Anomalia.Loot.PIE; Quit',
                      f'-ReportExportPath={out}', f'-abslog={out / "pie.engine.log"}']
    with (out / 'pie.process.log').open('w', encoding='utf-8') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=240, check=False)
    report['pieExitCode'] = result.returncode
    tests = json.loads((out / 'index.json').read_text(encoding='utf-8-sig')).get('tests', [])
    if result.returncode or len(tests) != 1 or tests[0].get('fullTestPath') != 'Anomalia.Loot.PIE' or tests[0].get('state') != 'Success':
        raise RuntimeError('Actual loot PIE input/UI/persistence test missing or failed')
    report.update(state='TESTED_IN_EDITOR_HEADLESS', checks=['real_native_pickup', 'Interact_key', 'inventory_transfer', 'profile_reload', 'inventory_key', 'native_UMG_open_close', 'physical_RP_note_pickup', 'bank_UMG_deposit', 'bank_UMG_withdrawal', 'native_vitals_HUD', 'native_warning_recovery', 'thirty_second_server_sleep', 'touch_interact_relay', 'gamepad_inventory_binding', 'safe_zone_roots', 'inventory_close_restores_input'])
except Exception as error:
    report['error'] = str(error)
finally:
    (out / 'loot-pie-report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
raise SystemExit(0 if report['state'] == 'TESTED_IN_EDITOR_HEADLESS' else 1)
