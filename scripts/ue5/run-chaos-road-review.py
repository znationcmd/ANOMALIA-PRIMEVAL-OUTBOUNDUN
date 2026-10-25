"""Compile separately, then require native rig import and observable actual Chaos driving."""
import argparse,json,os,subprocess,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def main():
    p=argparse.ArgumentParser();p.add_argument('--engine-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy();env['ANOMALIA_CHAOS_OUTPUT']=str(out)
    project=ROOT/'unreal/AnomaliaPrimeval.uproject'
    exe=args.engine_root/'Engine/Binaries/Win64/UnrealEditor.exe'
    def run(name,arguments,timeout):
        with (out/(name+'-process.log')).open('w',encoding='utf-8') as log:
            result=subprocess.run([str(exe),str(project),*arguments,'-unattended','-nopause','-nosound','-nosplash',
                '-abslog='+str(out/(name+'.log'))],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=timeout,check=False)
        if result.returncode:raise RuntimeError(name+' Unreal process failed: '+str(result.returncode))
    run('rig-import',['-ExecutePythonScript='+str(ROOT/'unreal/Scripts/create_chaos_road_review.py'),'-NullRHI'],900)
    report=json.loads((out/'rig-import-report.json').read_text(encoding='utf-8-sig'))
    if report['state']!='REAL_SKELETAL_CHAOS_REVIEW_MAP_SAVED_NOT_DRIVEN' or report['sourceCommit']!=env.get('GITHUB_SHA'):
        raise RuntimeError('Native real rig import not verified: '+str(report.get('error')))
    scope='chaos-smoke-'+uuid.uuid4().hex
    run('drive',[report['map']+'?AnomaliaServerId='+scope,'-game','-d3d11','-sm5','-windowed','-ResX=1280','-ResY=720',
        '-AnomaliaChaosProbe='+str(out/'drive-report.json')],900)
    drive=json.loads((out/'drive-report.json').read_text(encoding='utf-8-sig'))
    if drive['state']!='CHAOS_ROAD_PHYSICS_DRIVE_PASSED' or len(drive['physicsSamples'])<30:
        raise RuntimeError('Actual Chaos driving failed: '+str(drive.get('error')))
    (out/'review-report.json').write_text(json.dumps(dict(state='CHAOS_EDITOR_GAME_PHYSICAL_DRIVE_VERIFIED',
        sourceCommit=env.get('GITHUB_SHA'),profileScope=scope,packagedGameTested=False,
        installed=False,multiplayerTested=False,productionMapModified=False),indent=2)+'\n')

if __name__=='__main__':main()
