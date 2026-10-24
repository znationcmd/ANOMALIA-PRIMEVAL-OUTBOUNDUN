"""Execute import and actual GPU review; never equate model placement with gameplay."""
import argparse
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--engine-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    project = ROOT / 'unreal/AnomaliaPrimeval.uproject'
    env = os.environ.copy()
    env['ANOMALIA_INTERACTIVE_IMPORT_REPORT'] = str(output / 'import-report.json')
    env['ANOMALIA_VISUAL_OUTPUT'] = str(output / 'graphics')
    phases = [
        ('import', 'UnrealEditor-Cmd.exe', 'import_interactive_realism_review.py', ['-NullRHI'], 900),
        ('graphics', 'UnrealEditor.exe', 'capture_interactive_realism_review.py', ['-d3d11', '-sm5', '-windowed', '-ResX=1280', '-ResY=720'], 900)
    ]
    report = dict(state='FAILED', sourceCommit=env.get('GITHUB_SHA'), gameplayTested=False, phases=[])
    try:
        for name, exe, script, flags, timeout in phases:
            command = [str(args.engine_root / 'Engine/Binaries/Win64' / exe), str(project),
                       '-ExecutePythonScript=' + str(ROOT / 'unreal/Scripts' / script),
                       '-unattended', '-nopause', '-nosound', '-nosplash',
                       '-abslog=' + str(output / (name + '.log')), *flags]
            with (output / (name + '-process.log')).open('w', encoding='utf-8') as log:
                result = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=timeout, check=False)
            report['phases'].append(dict(phase=name, exitCode=result.returncode))
            if result.returncode:
                raise RuntimeError(name + ' process failed')
            if name == 'import':
                data = json.loads((output / 'import-report.json').read_text(encoding='utf-8-sig'))
                if data['state'] != 'REAL_MODELS_IMPORTED_REVIEW_SAVED_GAMEPLAY_UNVALIDATED' or len(data['models']) != 3 or data['sourceCommit'] != env.get('GITHUB_SHA'):
                    raise RuntimeError('Fresh native model import report required')
            else:
                data = json.loads((output / 'graphics/visual-report.json').read_text(encoding='utf-8-sig'))
                if data['state'] != 'REAL_VIEWPORT_CAPTURES_CREATED_NOT_VISUALLY_REVIEWED' or len(data['screenshots']) != 6 or data['sourceCommit'] != env.get('GITHUB_SHA'):
                    raise RuntimeError('Six fresh actual Unreal captures required')
        report['state'] = 'REAL_MODELS_NATIVE_IMPORTED_GPU_CAPTURED_NOT_GAMEPLAY_APPROVED'
    except Exception as error:
        report['error'] = str(error)
        raise
    finally:
        (output / 'process-report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
