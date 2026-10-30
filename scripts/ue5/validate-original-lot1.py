"""Import plus genuine GPU validation; native nonzero exits always fail."""
import argparse,json,os,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--engine-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[2];out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
editor=a.engine_root/'Engine/Binaries/Win64/UnrealEditor-Cmd.exe';project=root/'unreal/AnomaliaZPrigimalia.uproject'
report=dict(state='FAILED',sourceCommit=os.environ.get('GITHUB_SHA','manual'),phases=[])
try:
 for phase,script,flags in [('import','import_original_lot1.py',['-NullRHI']),('gpu','capture_original_lot1.py',['-d3d11','-sm5','-RenderOffscreen','-ResX=1280','-ResY=720'])]:
  env=dict(os.environ,ANOMALIA_LOT1_REPORT=str(out/'original-lot1-import.json'),ANOMALIA_LOT1_VISUAL=str(out/'original-lot1-views'))
  command=[str(editor),str(project),'-unattended','-nopause','-nosound',*flags,f'-ExecutePythonScript={root/"unreal/Scripts"/script}',f'-abslog={out/("original-lot1-"+phase+".engine.log")}']
  with (out/('original-lot1-'+phase+'.process.log')).open('w',encoding='utf-8') as log:r=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=900,check=False)
  report['phases'].append(dict(phase=phase,exitCode=r.returncode))
  if r.returncode:raise RuntimeError('Native '+phase+' failed')
 imported=json.loads((out/'original-lot1-import.json').read_text());gpu=json.loads((out/'original-lot1-views/report.json').read_text())
 if len(imported.get('models',[]))!=8 or imported['state']!='IMPORTED_AND_REVIEW_LEVEL_CREATED_NOT_PLAYTESTED':raise RuntimeError('Import incomplete')
 if gpu['state']!='REAL_GPU_VIEWS_AND_EDITOR_COLLISION_TRACES_PASSED' or len(gpu['screenshots'])!=8:raise RuntimeError('GPU/collision incomplete')
 if 'LogD3D11RHI' not in (out/'original-lot1-gpu.engine.log').read_text(encoding='utf-8',errors='replace'):raise RuntimeError('No actual RHI')
 report['state']='IMPORTED_GPU_CAPTURED_EDITOR_COLLISIONS_TESTED'
except Exception as error:report['error']=str(error)
finally:
 (out/'original-lot1-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
raise SystemExit(0 if report['state']=='IMPORTED_GPU_CAPTURED_EDITOR_COLLISIONS_TESTED' else 1)
