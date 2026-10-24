"""Obtain an actual native exit code instead of a PowerShell detached-process handle."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--engine-root',type=Path,required=True);p.add_argument('--project',type=Path,required=True);p.add_argument('--saved',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--map',default='/Game/Maps/ANOMALIA_Archipelago_v2',choices=['/Game/Maps/ANOMALIA_Archipelago_v2','/Game/Maps/ANOMALIA_Inhabited_v2']);a=p.parse_args()
 out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
 native=out/'pc-editor-open-probe.json'
 env=dict(os.environ,ANOMALIA_EXPECTED_SAVED=str(a.saved.resolve()),ANOMALIA_PC_UPDATE_REPORT=str(native),ANOMALIA_CAPTURE_MAP=a.map)
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
  gpu=out/'pc-installed-graphics';gpu.mkdir(exist_ok=False)
  gpu_env=dict(os.environ,ANOMALIA_VISUAL_OUTPUT=str(gpu),ANOMALIA_RENDER_PHASE='verify',ANOMALIA_CAPTURE_MAP=a.map)
  gpu_command=[str(a.engine_root/'Engine/Binaries/Win64/UnrealEditor-Cmd.exe'),str(a.project.resolve()),'-d3d11','-sm5','-RenderOffscreen','-unattended','-nopause','-nosound','-ResX=1280','-ResY=720',f'-ExecutePythonScript={a.project.parent/"Scripts/capture_real_world.py"}',f'-abslog={gpu/"editor-render.log"}']
  report['graphicalCommand']=gpu_command
  with (gpu/'process.log').open('w',encoding='utf-8') as log:
   rendered=subprocess.run(gpu_command,env=gpu_env,stdout=log,stderr=subprocess.STDOUT,timeout=900,check=False)
  report['graphicalExitCode']=rendered.returncode
  visual=json.loads((gpu/'visual-report.json').read_text()) if (gpu/'visual-report.json').is_file() else {}
  if rendered.returncode!=0 or visual.get('state')!='REAL_VIEWPORT_CAPTURES_CREATED_NOT_VISUALLY_REVIEWED' or len(visual.get('screenshots',[]))!=5:raise RuntimeError('Installed project GPU verification failed')
  if visual.get('renderPhase')!='verify' or visual.get('renderResourceRefresh',{}).get('landscapesLayerMergeRequested')!=0:raise RuntimeError('Installed GPU probe must be read-only')
  if 'LogD3D11RHI' not in (gpu/'editor-render.log').read_text(encoding='utf-8',errors='replace'):raise RuntimeError('Installed project lacks actual D3D11 evidence')
  for shot in visual['screenshots']:
   name=shot['file']
   if Path(name).name!=name:raise RuntimeError('Invalid screenshot path')
   image=gpu/name
   if not image.is_file() or image.stat().st_size!=shot['bytes'] or hashlib.sha256(image.read_bytes()).hexdigest()!=shot['sha256']:raise RuntimeError('Installed screenshot integrity failed')
  report.update(state='COPIED_EDITOR_PROJECT_GPU_VERIFIED',graphicalLaunchTested=True,graphicalReport=str(gpu/'visual-report.json'))
 except Exception as error:report['error']=str(error)
 finally:
  (out/'pc-editor-open-process.json').write_text(json.dumps(report,indent=2)+'\n')
  print(json.dumps({k:v for k,v in report.items() if k not in ('command','nativeReport')},indent=2))
 return 0 if report['state']=='COPIED_EDITOR_PROJECT_GPU_VERIFIED' else 1

if __name__=='__main__':raise SystemExit(main())
