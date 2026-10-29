"""Generate/import prototypes and require fresh native reports plus real GPU files."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess


def main():
    p=argparse.ArgumentParser();p.add_argument('--group',choices=['Expansion1','Metro1','NamedVehicles1','Military1','Military2'],default='Expansion1');p.add_argument('--engine-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    root=Path(__file__).resolve().parents[2];out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    report=dict(state='FAILED',sourceCommit=os.environ.get('GITHUB_SHA','manual'),phases=[],drivingTested=False,multiplayerTested=False)
    try:
        group=args.group;prefix={'Expansion1':'expansion','Metro1':'metro','NamedVehicles1':'named-vehicles','Military1':'military','Military2':'military-extra'}[group]
        module_spec=importlib.util.spec_from_file_location('expansion',root/('scripts/ue5/generate-metro.py' if group=='Metro1' else 'scripts/ue5/generate-assets-expansion.py'))
        module=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(module)
        manifest=module.generate(root/'unreal/SourceAssets'/group) if group in ['Expansion1','Metro1'] else json.loads((root/'unreal/SourceAssets'/group/'manifest.json').read_text())
        import_report=out/(prefix+'-import.json');visual=out/(prefix+'-views')
        if import_report.exists() or visual.exists():raise RuntimeError('Existing evidence preserved; use a fresh run directory')
        editor=args.engine_root/'Engine/Binaries/Win64/UnrealEditor-Cmd.exe';project=root/'unreal/AnomaliaZPrigimalia.uproject'
        for phase,script,flags in [('import','import_expansion_models.py',['-NullRHI']),('gpu','capture_expansion_models.py',['-d3d11','-sm5','-RenderOffscreen','-ResX=1280','-ResY=720'])]:
            env=dict(os.environ,ANOMALIA_ASSET_GROUP=group,ANOMALIA_EXPANSION_REPORT=str(import_report),ANOMALIA_EXPANSION_VISUAL=str(visual))
            command=[str(editor),str(project),'-unattended','-nopause','-nosound',*flags,f'-ExecutePythonScript={root/"unreal/Scripts"/script}',f'-abslog={out/(prefix+"-"+phase+".engine.log")}']
            with (out/(prefix+'-'+phase+'.process.log')).open('w',encoding='utf-8') as log:
                run=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=900,check=False)
            report['phases'].append(dict(phase=phase,exitCode=run.returncode))
            if run.returncode:raise RuntimeError('Native '+phase+' failed')
            if phase=='import':
                imported=json.loads(import_report.read_text())
                if imported.get('sourceCommit')!=report['sourceCommit'] or imported.get('state')!=('IMPORTED_33_ORIGINAL_PROTOTYPES_NOT_PLAYTESTED' if group=='Expansion1' else 'IMPORTED_MODELS_NOT_PLAYTESTED'):raise RuntimeError('Import incomplete: '+str(imported.get('error')))
                expected={m['id'] for m in manifest['models']}
                if {m['id'] for m in imported['models']}!=expected or len(imported['models'])!=len(expected):raise RuntimeError('Missing imported prototype')
                if any(not m['nativePresentationBound'] for m in imported['models'] if m['kind']=='vehicle'):raise RuntimeError('Native catalogue binding failed')
        gpu=json.loads((visual/'report.json').read_text())
        if gpu.get('state')!='REAL_GPU_CAPTURES_CREATED_NOT_VISUALLY_REVIEWED' or gpu.get('sourceCommit')!=report['sourceCommit']:raise RuntimeError('GPU capture failed: '+str(gpu.get('error')))
        if {m['model'] for m in gpu['screenshots']}!=expected or len(gpu['screenshots'])!=len(expected):raise RuntimeError('Missing GPU view')
        if 'LogD3D11RHI' not in (out/(prefix+'-gpu.engine.log')).read_text(encoding='utf-8',errors='replace'):raise RuntimeError('No actual D3D11 RHI')
        for shot in gpu['screenshots']:
            if Path(shot['file']).name!=shot['file']:raise RuntimeError('Invalid capture path')
            image=visual/shot['file']
            if not image.is_file() or image.stat().st_size!=shot['bytes'] or hashlib.sha256(image.read_bytes()).hexdigest()!=shot['sha256']:raise RuntimeError('Capture integrity failed')
        report.update(state=('IMPORTED_33_PROTOTYPES_GPU_CAPTURED_AWAITING_REVIEW' if group=='Expansion1' else 'IMPORTED_MODELS_GPU_CAPTURED_AWAITING_REVIEW'),group=group,modelCount=len(expected))
    except Exception as error:report['error']=str(error)
    finally:
        (out/(prefix+'-validation.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
    return 0 if report['state'] in ['IMPORTED_33_PROTOTYPES_GPU_CAPTURED_AWAITING_REVIEW','IMPORTED_MODELS_GPU_CAPTURED_AWAITING_REVIEW'] else 1


if __name__=='__main__':raise SystemExit(main())
