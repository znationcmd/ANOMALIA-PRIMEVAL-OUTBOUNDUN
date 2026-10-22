"""Cook a real Windows test build, then launch its executable with an isolated GPU smoke test."""
import argparse,json,os,subprocess,uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
MAP='/Game/Maps/ANOMALIA_Playable_v1'
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--engine-root',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
report=dict(state='FAILED',sourceCommit=os.environ.get('GITHUB_SHA'),packagedGame=True,consoleMobileTested=False)
project=ROOT/'unreal/AnomaliaPrimeval.uproject'
def run(command,name,timeout):
    with (out/(name+'.log')).open('w',encoding='utf-8') as log:
        r=subprocess.run([str(x) for x in command],stdout=log,stderr=subprocess.STDOUT,timeout=timeout,check=False)
    report[name+'ExitCode']=r.returncode
    if r.returncode:raise RuntimeError(name+' failed; inspect '+str(out/(name+'.log')))
try:
    editor=a.engine_root/'Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
    scene_receipt=out/('scene-'+uuid.uuid4().hex+'.json')
    os.environ['ANOMALIA_PLAYABLE_ZONE_REPORT']=str(scene_receipt)
    run([editor,project,'-unattended','-nopause','-nosound','-NullRHI','-stdout','-FullStdOutLogOutput',
         '-abslog='+str(out/'create-zone-editor.log'),
         '-run=pythonscript','-script='+str(ROOT/'unreal/Scripts/create_playable_zone.py')],'create-zone',300)
    scene=json.loads(scene_receipt.read_text(encoding='utf-8'))
    if scene.get('state')!='PLAYABLE_LOOK_V2_SAVED' or scene.get('sourceCommit')!=os.environ.get('GITHUB_SHA') or not scene.get('dynamicLights'):
        raise RuntimeError('Fresh playable scene update receipt missing or invalid')
    report['scene']=scene
    archive=out/('package-'+uuid.uuid4().hex);archive.mkdir()
    uat=a.engine_root/'Engine/Build/BatchFiles/RunUAT.bat'
    run([os.environ.get('COMSPEC','cmd.exe'),'/d','/c',uat,'BuildCookRun','-project='+str(project),'-noP4','-unattended','-utf8output','-platform=Win64','-clientconfig=Development','-build','-cook','-stage','-pak','-archive','-archivedirectory='+str(archive),'-map='+MAP,'-prereqs'],'package',5400)
    executables=list(archive.glob('Windows/AnomaliaPrimeval.exe'))
    if len(executables)!=1:raise RuntimeError('Unique actual packaged executable not found')
    exe=executables[0];probe=out/'packaged-smoke.json'
    scope='playable-smoke-'+uuid.uuid4().hex
    run([exe,MAP+'?AnomaliaServerId='+scope,'-windowed','-ResX=1280','-ResY=720','-d3d11','-sm5','-unattended','-nosound','-nopause','-AnomaliaPlayableProbe='+str(probe),'-abslog='+str(out/'packaged-engine.log')],'packaged-run',180)
    native=json.loads(probe.read_text(encoding='utf-8-sig'))
    required={'native_inventory_food_use_consumes_one_and_restores_hunger','native_playable_look_v2_cooked_materials_and_lights','main_menu_play_button','explicit_local_profile_save','native_world_HUD_and_three_vehicle_meshes','keyboard_character_movement','walk_through_house_doorway','world_pickup_into_native_inventory','native_inventory_open_close','three_vehicle_enter_accelerate_steer_exit'}
    if native.get('state')!='PACKAGED_GAME_SMOKE_PASSED' or not required.issubset(native.get('checks',[])):
        raise RuntimeError('Actual packaged gameplay smoke failed: '+native.get('error','missing checks'))
    image=probe.with_suffix('.png')
    if not image.is_file() or image.stat().st_size<10000:raise RuntimeError('Fresh packaged GPU screenshot missing')
    resume=out/'packaged-resume.json'
    run([exe,MAP+'?AnomaliaServerId='+scope,'-windowed','-ResX=1280','-ResY=720','-d3d11','-sm5','-unattended','-nosound','-AnomaliaPlayableProbe='+str(resume),'-AnomaliaPlayableResume'],'packaged-resume',90)
    resumed=json.loads(resume.read_text(encoding='utf-8-sig'))
    if resumed.get('state')!='PACKAGED_GAME_SMOKE_PASSED' or 'restarted_executable_restored_inventory_and_character_position' not in resumed.get('checks',[]):
        raise RuntimeError('Actual executable restart did not restore character and inventory')
    report['resume']=resumed
    report.update(state='PACKAGED_WINDOWS_SMOKE_PASSED',executable=str(exe),native=native,screenshot=str(image),archive=str(archive/'Windows'),limitations=['provisional_original_art','prototype_ground_vehicle_physics','no_blood_or_drop_UI_yet','item_specific_weapon_crafting_and_medical_systems_incomplete'])
except Exception as error: report['error']=str(error)
finally:
    (out/'package-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
raise SystemExit(0 if report['state']=='PACKAGED_WINDOWS_SMOKE_PASSED' else 1)
