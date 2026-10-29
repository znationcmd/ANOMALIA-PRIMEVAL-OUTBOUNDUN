"""Capture the existing detailed-art native review through the real game renderer."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--engine-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve(); output.mkdir(parents=True, exist_ok=False)
    review = output / 'review.json'
    report = dict(state='FAILED', sourceCommit=os.environ.get('GITHUB_SHA'),
                  scope='Detailed imported-art review only; not full inhabited-world rendering',
                  fullWorldPhotorealismValidated=False)
    try:
        editor = args.engine_root / 'Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
        scope = 'visual-smoke-' + os.environ.get('GITHUB_RUN_ID', 'manual') + '-' + os.environ.get('GITHUB_RUN_ATTEMPT', '1')
        command = [str(editor), str(ROOT / 'unreal/AnomaliaZPrigimalia.uproject'),
                   '/Game/Maps/ANOMALIA_VisualValidation_v1?AnomaliaServerId=' + scope,
                   '-game', '-windowed', '-ResX=1280', '-ResY=720', '-d3d11', '-sm5',
                   '-unattended', '-nosound', '-AnomaliaVisualReview=' + str(review),
                   '-abslog=' + str(output / 'renderer.log')]
        with (output / 'process.log').open('wb') as log:
            result = subprocess.run(command, timeout=300, stdout=log, stderr=subprocess.STDOUT)
        report['exitCode'] = result.returncode
        if review.exists():
            native = json.loads(review.read_text(encoding='utf-8-sig'))
            report['nativeReview'] = native
            images = []
            for number, source in enumerate(native.get('screenshots', [])):
                source = Path(source)
                if not source.is_absolute(): source = ROOT / 'unreal' / source
                source = source.resolve()
                if not source.is_relative_to(output) or not source.is_file():
                    raise RuntimeError('Review screenshot outside the current evidence folder or missing: ' + str(source))
                destination = output / ('view_' + str(number) + source.suffix)
                shutil.copyfile(source, destination); images.append(destination.name)
            report['capturedImages'] = images
            if result.returncode != 0 or native.get('state') != 'PACKAGED_VISUAL_REVIEW_PASSED' or len(images) != 8:
                raise RuntimeError('Detailed native visual review did not pass: ' + native.get('error', 'missing complete captures'))
        else:
            raise RuntimeError('Fresh renderer review receipt missing')
        report['state'] = 'DETAILED_ART_RENDER_REVIEW_PASSED_NOT_FULL_WORLD'
    except Exception as error:
        report['error'] = str(error)
        raise
    finally:
        (output / 'result.json').write_text(json.dumps(report, indent=2) + '\n')

if __name__ == '__main__':
    main()
