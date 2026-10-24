"""Back up the owned world, author plants, then verify in a fresh native process."""
import argparse,json,os,subprocess
from pathlib import Path
from world_snapshot import snapshot,INHABITED_PATHS

def main():
    p=argparse.ArgumentParser();p.add_argument('--engine-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--house-audit',type=Path,required=True);a=p.parse_args()
    root=Path(__file__).resolve().parents[2];out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    report=dict(state='FAILED',sourceCommit=os.environ.get('GITHUB_SHA'),mapPackage='/Game/Maps/ANOMALIA_Inhabited_v2',phases=[])
    try:
        backup=snapshot(root/'unreal',out/'backup',INHABITED_PATHS)
        backup['mapPackage']=report['mapPackage']
        report['backup']=backup;(out/'backup-report.json').write_text(json.dumps(backup,indent=2))
        for phase in ('create','audit'):
            native=out/(phase+'.json')
            if native.exists():raise RuntimeError('Fresh output directory required')
            env=dict(os.environ,ANOMALIA_URBAN_REPORT=str(native),ANOMALIA_URBAN_MODE=phase,ANOMALIA_URBAN_HOUSE_AUDIT=str(a.house_audit.resolve()),ANOMALIA_URBAN_BACKUP_REPORT=str(out/'backup-report.json'))
            command=[str(a.engine_root/'Engine/Binaries/Win64/UnrealEditor-Cmd.exe'),str(root/'unreal/AnomaliaPrimeval.uproject'),'-NullRHI','-unattended','-nopause','-nosound','-ExecutePythonScript='+str(root/'unreal/Scripts/author_urban_greenery.py'),'-abslog='+str(out/(phase+'.engine.log'))]
            with (out/(phase+'.process.log')).open('w',encoding='utf-8') as stream:
                run=subprocess.run(command,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=1200,check=False)
            proof=json.loads(native.read_text()) if native.exists() else {}
            report['phases'].append(dict(phase=phase,exitCode=run.returncode,native=proof))
            allowed={'URBAN_PLANTS_SAVED_REQUIRES_REOPEN','SAVED_URBAN_PLANTS_VERIFIED'} if phase=='create' else {'SAVED_URBAN_PLANTS_VERIFIED'}
            if run.returncode or proof.get('state') not in allowed:raise RuntimeError('Plant authoring/reopen failed in '+phase)
            if proof.get('sourceCommit')!=report['sourceCommit'] or proof.get('counts',{}).get('island_tree_02',0)<600:raise RuntimeError('Incomplete planting evidence')
        if report['phases'][0]['native']['planSha256']!=report['phases'][1]['native']['planSha256']:raise RuntimeError('Saved planting plan changed')
        report.update(state='URBAN_PLANTS_SAVED_AND_INDEPENDENTLY_VERIFIED',counts=proof['counts'],verifiedInstances=proof['verifiedInstances'],clusters=proof['clusters'])
    except Exception as error:report['error']=str(error)
    finally:
        (out/'process-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ('phases','backup')},indent=2))
    return 0 if report['state']=='URBAN_PLANTS_SAVED_AND_INDEPENDENTLY_VERIFIED' else 1

if __name__=='__main__':raise SystemExit(main())
