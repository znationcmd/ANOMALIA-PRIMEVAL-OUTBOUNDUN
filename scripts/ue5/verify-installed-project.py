"""Obtain an actual native exit code instead of a PowerShell detached-process handle."""
import argparse,json,os,subprocess
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--engine-root',type=Path,required=True);p.add_argument('--project',type=Path,required=True);p.add_argument('--saved',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
 native=out/'pc-editor-open-probe.json'
 env=dict(os.environ,ANOMALIA_EXPECTED_SAVED=str(a.saved.resolve()),ANOMALIA_PC_UPDATE_REPORT=str(native))
 command=[str(a.engine_root/'Engine/Binaries/Win64/UnrealEditor-Cmd.exe'),str(a.project.resolve()),'-NullRHI','-unattended','-nopause','-nosound',f'-ExecutePythonScript={a.project.parent/"Scripts/probe_installed_editor.py"}',f'-abslog={out/"pc-editor-open.engine.log"}']
 report=dict(state='FAILED',headless=True,graphicalLaunchTested=False,command=command)
 try:
  if native.exists():raise RuntimeError('Existing probe preserved; use a fresh validation directory')
  with (out/'pc-editor-open.process.log').open('w',encoding='utf-8') as log:
   run=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180,check=False)
  report['exitCode']=run.returncode
  proof=json.loads(native.read_text()) if native.is_file() else {}
  report['nativeReport']=proof
  if run.returncode!=0 or proof.get('state')!='COPIED_EDITOR_PROJECT_OPENED_HEADLESS':raise RuntimeError('Copied project native exit/report failed')
  report['state']='COPIED_EDITOR_PROJECT_OPENED_HEADLESS'
 except Exception as error:report['error']=str(error)
 finally:
  (out/'pc-editor-open-process.json').write_text(json.dumps(report,indent=2)+'\n')
  print(json.dumps({k:v for k,v in report.items() if k not in ('command','nativeReport')},indent=2))
 return 0 if report['state']=='COPIED_EDITOR_PROJECT_OPENED_HEADLESS' else 1

if __name__=='__main__':raise SystemExit(main())
