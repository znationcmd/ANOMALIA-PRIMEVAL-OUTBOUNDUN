"""Run the existing real playable-map controls before spending time on a cook."""
import argparse,json,os,subprocess,uuid
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--engine-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--progress-art',action='store_true');a=p.parse_args()
    root=Path(__file__).resolve().parents[2];out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    proof=out/'smoke.json'
    if proof.exists():raise RuntimeError('Fresh interaction output required')
    report=dict(state='FAILED',sourceCommit=os.environ.get('GITHUB_SHA'),packagedGameTested=False,fullMapComplete=False)
    try:
        # Read only the installed vendor's template folders, never user documents
        # or private engine source. A ready vehicle rig may already be available.
        templates=[]
        for folder in ('FeaturePacks','Templates'):
            base=a.engine_root/folder
            if not base.is_dir():continue
            for file in base.rglob('*'):
                if file.is_file() and 'vehicle' in str(file.relative_to(a.engine_root)).lower() and file.suffix.lower() in ('.upack','.zip','.uasset'):
                    templates.append(dict(path=str(file.relative_to(a.engine_root)),bytes=file.stat().st_size))
        report['installedVehicleTemplateFiles']=templates[:60]
        command=[str(a.engine_root/'Engine/Binaries/Win64/UnrealEditor-Cmd.exe'),str(root/'unreal/AnomaliaZPrigimalia.uproject'),
            '/Game/Maps/ANOMALIA_Playable_v1?AnomaliaServerId=playable-smoke-'+uuid.uuid4().hex,
            '-game','-windowed','-ResX=1280','-ResY=720','-d3d11','-sm5','-unattended','-nosound',
            '-AnomaliaPlayableProbe='+str(proof),'-abslog='+str(out/'engine.log')]
        if a.progress_art: command.append('-AnomaliaProgressArt')
        with (out/'process.log').open('w',encoding='utf-8') as stream:
            run=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,timeout=180,check=False)
        report['exitCode']=run.returncode
        data=json.loads(proof.read_text(encoding='utf-8-sig')) if proof.exists() else {}
        report['native']=data
        if run.returncode or data.get('state')!='PACKAGED_GAME_SMOKE_PASSED' or 'three_vehicle_enter_accelerate_steer_exit' not in data.get('checks',[]):
            raise RuntimeError(data.get('error','Missing successful real playable-map controls'))
        report['state']='EDITOR_GAME_PLAYABLE_INTERACTIONS_PASSED'
    except Exception as error:report['error']=str(error)
    finally:
        (out/'process-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
    return 0 if report['state']=='EDITOR_GAME_PLAYABLE_INTERACTIONS_PASSED' else 1

if __name__=='__main__':raise SystemExit(main())
