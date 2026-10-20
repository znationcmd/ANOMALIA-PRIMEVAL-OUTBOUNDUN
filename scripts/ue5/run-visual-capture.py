"""Run a real graphical UE editor. A successful NullRHI run cannot satisfy this check."""
import argparse,json,os,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--engine-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[2];out=a.output.resolve()/'real-graphics';out.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,ANOMALIA_VISUAL_OUTPUT=str(out));report=out/'visual-report.json'
command=[str(a.engine_root/'Engine/Binaries/Win64/UnrealEditor-Cmd.exe'),str(root/'unreal/AnomaliaPrimeval.uproject'),'-d3d11','-sm5','-RenderOffscreen','-unattended','-nopause','-nosound','-ResX=1280','-ResY=720',f'-ExecutePythonScript={root/"unreal/Scripts/capture_real_world.py"}',f'-abslog={out/"editor-render.log"}']
result=dict(state='FAILED',headless=False,command=command)
try:
 with (out/'process.log').open('w',encoding='utf-8') as log:
  run=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=900,check=False)
 result['exitCode']=run.returncode
 native=json.loads(report.read_text()) if report.is_file() else {}
 text=(out/'editor-render.log').read_text(encoding='utf-8',errors='replace')
 if run.returncode or native.get('state')!='REAL_VIEWPORT_CAPTURES_CREATED_NOT_VISUALLY_REVIEWED' or len(native.get('screenshots',[]))!=5:raise RuntimeError('Real GPU capture failed or incomplete; inspect native logs')
 if 'LogD3D11RHI' not in text:raise RuntimeError('No native D3D11 RHI evidence')
 result.update(state='REAL_GPU_CAPTURES_AWAITING_REVIEW',nativeReport=native)
except Exception as error:result['error']=str(error)
finally:
 (out/'capture-process-report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
raise SystemExit(0 if result['state']=='REAL_GPU_CAPTURES_AWAITING_REVIEW' else 1)
