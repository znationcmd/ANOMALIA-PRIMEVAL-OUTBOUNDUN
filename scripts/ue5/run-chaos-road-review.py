"""Compile separately, then require native rig import and observable actual Chaos driving."""
import argparse,json,os,subprocess,uuid,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def main():
    p=argparse.ArgumentParser();p.add_argument('--engine-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--record-driving',action='store_true',help='Opt-in continuous viewport recording; can significantly slow rendering')
    p.add_argument('--sedan',action='store_true',help='Use the separately imported original sedan art and authored wheel hubs')
    args=p.parse_args()
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy();env['ANOMALIA_CHAOS_OUTPUT']=str(out)
    env['ANOMALIA_CHAOS_USE_SEDAN']='1' if args.sedan else '0'
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
    # Continuous GPU readback + PNG compression stalls this validation host.
    # Run the unchanged physical acceptance gates without that observer overhead.
    # Phase/final screenshots are still captured by the probe. Recording is an
    # explicit additional run, not a condition for proving actual wheel physics.
    capture=['-AnomaliaRecordDriving'] if args.record_driving else []
    run('drive',[report['map']+'?AnomaliaServerId='+scope,'-game','-d3d11','-sm5','-windowed','-ResX=1280','-ResY=720',
        '-AnomaliaChaosProbe='+str(out/'drive-report.json'),*capture],900)
    drive=json.loads((out/'drive-report.json').read_text(encoding='utf-8-sig'))
    if drive['state']!='CHAOS_ROAD_PHYSICS_DRIVE_PASSED' or len(drive['physicsSamples'])<30:
        raise RuntimeError('Actual Chaos driving failed: '+str(drive.get('error')))
    required={
        'moving_vehicle_refuses_exit_and_keeps_original_driver',
        'server_fuel_consumption_reaches_zero_and_cuts_Chaos_throttle',
        'empty_tank_cannot_accelerate_under_full_driver_input',
        'server_refuel_rejects_invalid_amounts_and_restores_fuel',
        'refuel_restores_physical_acceleration_and_fuel_consumption',
        'safe_exit_restores_same_survivor',
    }
    if drive.get('buildCommit')!=env.get('GITHUB_SHA') or not required.issubset(drive.get('checks',[])):
        raise RuntimeError('Current native build must pass depletion/refuel and driver safety checks')
    video=None;video_error=None
    encoder=shutil.which('ffmpeg')
    if encoder and drive.get('recordedViewportFrames',0)>=10:
        result=subprocess.run([encoder,'-y','-framerate','5','-i',str(out/'frames/frame-%05d.png'),
            '-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',str(out/'actual-chaos-driving.mp4')],
            stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=120,check=False)
        if result.returncode==0:video=str(out/'actual-chaos-driving.mp4')
        else:video_error='Installed video encoder failed; actual viewport frames retained'
    else:video_error=('Continuous recording disabled for physics acceptance; actual phase screenshots retained' if not args.record_driving
        else 'No installed ffmpeg encoder or insufficient actual viewport frames')
    (out/'review-report.json').write_text(json.dumps(dict(state='CHAOS_EDITOR_GAME_PHYSICAL_DRIVE_VERIFIED',
        video=video,videoError=video_error,
        sourceCommit=env.get('GITHUB_SHA'),profileScope=scope,packagedGameTested=False,
        installed=False,multiplayerTested=False,productionMapModified=False,
        originalSedanArt=args.sedan,entryAnimationTested=False,openingDoorsTested=False),indent=2)+'\n')

if __name__=='__main__':main()
