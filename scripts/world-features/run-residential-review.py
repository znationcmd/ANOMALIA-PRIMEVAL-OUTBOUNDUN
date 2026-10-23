"""Run a genuine GPU render of the four imported residential candidates."""
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
    output = args.output.resolve(); output.mkdir(parents=True, exist_ok=False)
    report = dict(state='FAILED', sourceCommit=os.environ.get('GITHUB_SHA'), fullWorldValidated=False)
    try:
        scope = 'visual-smoke-residential-' + os.environ.get('GITHUB_RUN_ID', 'manual')
        review = output / 'review.json'
        command = [str(args.engine_root / 'Engine/Binaries/Win64/UnrealEditor-Cmd.exe'),
                   str(ROOT / 'unreal/AnomaliaPrimeval.uproject'),
                   '/Game/Maps/ANOMALIA_ResidentialPhotogrammetryReview_v1?AnomaliaServerId=' + scope,
                   '-game', '-windowed', '-ResX=1280', '-ResY=720', '-d3d11', '-sm5',
                   '-unattended', '-nosound', '-AnomaliaResidentialReview',
                   '-AnomaliaVisualReview=' + str(review), '-abslog=' + str(output / 'renderer.log')]
        with (output / 'process.log').open('wb') as log:
            result = subprocess.run(command, timeout=300, stdout=log, stderr=subprocess.STDOUT)
        native = json.loads(review.read_text(encoding='utf-8-sig'))
        images = [Path(p).resolve() for p in native.get('screenshots', [])]
        if result.returncode != 0 or native.get('state') != 'PACKAGED_VISUAL_REVIEW_PASSED' or len(images) != 16:
            raise RuntimeError('Residential GPU review failed: ' + native.get('error', 'incomplete captures'))
        if any(not p.is_relative_to(output) or not p.is_file() or p.stat().st_size < 10000 for p in images):
            raise RuntimeError('Fresh render images required in current evidence directory')
        if len(native.get('loadedMeshPaths', [])) != 4 or not native.get('dayAndNightCaptured'):
            raise RuntimeError('Four native models and both lighting states required')
        report.update(state='RESIDENTIAL_GPU_CAPTURES_READY_FOR_VISUAL_INSPECTION',
                      images=[p.name for p in images], nativeReview=native)
    except Exception as error:
        report['error'] = str(error); raise
    finally:
        (output / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
if __name__ == '__main__':
    main()
