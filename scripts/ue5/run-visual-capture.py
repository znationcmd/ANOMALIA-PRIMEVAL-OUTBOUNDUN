"""Real GPU repair/save + independent reopen. NullRHI cannot satisfy this check."""
import argparse,json,os,subprocess
from pathlib import Path
from world_snapshot import snapshot,sha256


def main():
 p=argparse.ArgumentParser();p.add_argument('--engine-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 root=Path(__file__).resolve().parents[2];base=a.output.resolve()/'real-graphics';base.mkdir(parents=True,exist_ok=True)
 marker=root/'unreal/Saved/AnomaliaMigration/render-repair-v1.json'
 result=dict(state='FAILED',headless=False,sourceCommit=os.environ.get('GITHUB_SHA','manual'),phases=[])
 def capture(phase,backup=None):
  out=base/phase;out.mkdir(exist_ok=False)
  env=dict(os.environ,ANOMALIA_VISUAL_OUTPUT=str(out),ANOMALIA_RENDER_PHASE=phase)
  if backup:env['ANOMALIA_RENDER_BACKUP']=backup['archive']
  command=[str(a.engine_root/'Engine/Binaries/Win64/UnrealEditor-Cmd.exe'),str(root/'unreal/AnomaliaPrimeval.uproject'),'-d3d11','-sm5','-RenderOffscreen','-unattended','-nopause','-nosound','-ResX=1280','-ResY=720',f'-ExecutePythonScript={root/"unreal/Scripts/capture_real_world.py"}',f'-abslog={out/"editor-render.log"}']
  status=dict(phase=phase,command=command);result['phases'].append(status)
  with (out/'process.log').open('w',encoding='utf-8') as log:
   run=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=900,check=False)
  status['exitCode']=run.returncode
  report=out/'visual-report.json';native=json.loads(report.read_text()) if report.is_file() else {}
  status['nativeReport']=native
  if run.returncode or native.get('state')!='REAL_VIEWPORT_CAPTURES_CREATED_NOT_VISUALLY_REVIEWED' or len(native.get('screenshots',[]))!=5:raise RuntimeError('Real GPU capture failed/incomplete in '+phase)
  if native.get('renderPhase')!=phase:raise RuntimeError('Capture phase mismatch')
  if 'LogD3D11RHI' not in (out/'editor-render.log').read_text(encoding='utf-8',errors='replace'):raise RuntimeError('No D3D11 RHI evidence')
  for shot in native['screenshots']:
   name=shot['file']
   if Path(name).name!=name:raise RuntimeError('Screenshot filename is not local')
   file=out/name
   if not file.is_file() or file.stat().st_size!=shot['bytes'] or sha256(file)!=shot['sha256']:raise RuntimeError('Screenshot checksum mismatch')
  if phase=='repair' and not native.get('savedPackages'):raise RuntimeError('No scoped packages saved')
  if phase=='verify' and native.get('renderResourceRefresh',{}).get('landscapesLayerMergeRequested')!=0:raise RuntimeError('Reopen test must not force a layer rebuild')
  return native
 try:
  if not marker.exists():
   backup=snapshot(root/'unreal',base/'backup');result['backup']=backup
   (base/'backup-report.json').write_text(json.dumps(backup,indent=2)+'\n')
   capture('repair',backup)
  else:
   prior=json.loads(marker.read_text())
   if prior.get('state')!='REOPENED_GPU_CAPTURES_AWAITING_REVIEW':raise RuntimeError('Unrecognized repair marker preserved')
   result['priorRepair']=prior
  capture('verify')
  result['state']='REOPENED_GPU_CAPTURES_AWAITING_REVIEW'
  # Existing markers are historical records, never overwritten by subsequent runs.
  if not marker.exists():
   marker.parent.mkdir(parents=True,exist_ok=True)
   with marker.open('x',encoding='utf-8') as f:json.dump(dict(state=result['state'],sourceCommit=result['sourceCommit'],backup=result['backup'],report=str(base/'capture-process-report.json')),f,indent=2)
 except Exception as error:result['error']=str(error)
 finally:
  (base/'capture-process-report.json').write_text(json.dumps(result,indent=2)+'\n')
  print(json.dumps({k:v for k,v in result.items() if k not in ('phases','backup','priorRepair')},indent=2))
 return 0 if result['state']=='REOPENED_GPU_CAPTURES_AWAITING_REVIEW' else 1

if __name__=='__main__':raise SystemExit(main())
