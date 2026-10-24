"""Launch a fresh native read-only audit; require clean editor shutdown and proof."""
import argparse,json,os,subprocess
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--engine-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    root=Path(__file__).resolve().parents[2];out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    evidence=out/'residential-audit.json';report=dict(state='FAILED',sourceCommit=os.environ.get('GITHUB_SHA'))
    try:
        if evidence.exists():raise RuntimeError('Fresh evidence directory required')
        env=dict(os.environ,ANOMALIA_RESIDENTIAL_AUDIT_REPORT=str(evidence))
        command=[str(a.engine_root/'Engine/Binaries/Win64/UnrealEditor-Cmd.exe'),str(root/'unreal/AnomaliaPrimeval.uproject'),'-NullRHI','-unattended','-nopause','-nosound','-ExecutePythonScript='+str(root/'unreal/Scripts/audit_residential_native.py'),'-abslog='+str(out/'residential-audit.engine.log')]
        with (out/'process.log').open('w',encoding='utf-8') as stream:
            run=subprocess.run(command,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=1800,check=False)
        native=json.loads(evidence.read_text()) if evidence.is_file() else {}
        report.update(exitCode=run.returncode,native=native)
        if run.returncode or native.get('state')!='SAVED_RESIDENTIAL_NATIVE_AUDIT_PASSED':raise RuntimeError('Native house audit or clean process shutdown failed')
        if native.get('sourceCommit')!=report['sourceCommit'] or native.get('mapPackage')!='/Game/Maps/ANOMALIA_Inhabited_v2':raise RuntimeError('Audit provenance mismatch')
        if native.get('counts',{}).get('upgraded',0)<4000 or sum(native['counts'].values())!=4760:raise RuntimeError('Incomplete saved-house audit')
        report['state']='RESIDENTIAL_AUDIT_AND_CLEAN_SHUTDOWN_PASSED'
    except Exception as error:report['error']=str(error)
    finally:
        (out/'process-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
    return 0 if report['state']=='RESIDENTIAL_AUDIT_AND_CLEAN_SHUTDOWN_PASSED' else 1

if __name__=='__main__':raise SystemExit(main())
