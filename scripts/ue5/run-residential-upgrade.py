"""Back up the existing populated world, then author only its owned house exteriors."""
import argparse
import json
import os
from pathlib import Path
import subprocess
from world_snapshot import snapshot,INHABITED_PATHS

def main():
    p=argparse.ArgumentParser();p.add_argument('--engine-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    root=Path(__file__).resolve().parents[2];out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    report=dict(state='FAILED',sourceCommit=os.environ.get('GITHUB_SHA'),mapPackage='/Game/Maps/ANOMALIA_Inhabited_v2')
    try:
        backup=snapshot(root/'unreal',out/'backup',INHABITED_PATHS);backup['mapPackage']=report['mapPackage']
        backup_file=out/'backup-report.json';backup_file.write_text(json.dumps(backup,indent=2)+'\n')
        native=out/'residential-upgrade.json'
        if native.exists():raise RuntimeError('Use a fresh output directory; existing evidence preserved')
        env=dict(os.environ,ANOMALIA_RESIDENTIAL_BACKUP_REPORT=str(backup_file),ANOMALIA_RESIDENTIAL_UPGRADE_REPORT=str(native),ANOMALIA_EDITOR_TASK=str(root/'unreal/Scripts/apply_residential_replacements.py'))
        command=[str(a.engine_root/'Engine/Binaries/Win64/UnrealEditor-Cmd.exe'),str(root/'unreal/AnomaliaZPrigimalia.uproject'),'-NullRHI','-unattended','-nopause','-nosound','-ExecutePythonScript='+str(root/'scripts/world-features/run-editor-task.py'),'-abslog='+str(out/'residential-upgrade.engine.log')]
        with (out/'process.log').open('w',encoding='utf-8') as stream:
            run=subprocess.run(command,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=1800,check=False)
        result=json.loads(native.read_text()) if native.is_file() else {}
        report.update(exitCode=run.returncode,native=result,backup=backup_file.as_posix())
        if run.returncode or result.get('state')!='OWNED_RESIDENTIAL_EXTERIORS_SAVED_REQUIRES_GPU_REVIEW' or result.get('upgradedTotal',0)<4000:raise RuntimeError('Native residential upgrade failed; original package archive retained')
        report['state']='RESIDENTIAL_UPGRADE_SAVED_NOT_RENDERED'
    except Exception as error:report['error']=str(error)
    finally:
        (out/'process-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    return 0 if report['state']=='RESIDENTIAL_UPGRADE_SAVED_NOT_RENDERED' else 1

if __name__=='__main__':raise SystemExit(main())
