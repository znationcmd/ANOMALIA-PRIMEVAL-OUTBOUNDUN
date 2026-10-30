"""Cook a real Windows test build, then launch its executable with an isolated GPU smoke test."""
import argparse,json,os,subprocess,uuid,shutil,tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
MAP='/Game/Maps/ANOMALIA_Playable_v1'
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--engine-root',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--progress-art',action='store_true')
a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
report=dict(state='FAILED',sourceCommit=os.environ.get('GITHUB_SHA'),packagedGame=True,consoleMobileTested=False)
project=ROOT/'unreal/AnomaliaZPrigimalia.uproject'
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
    run([editor,project,'-NullRHI','-unattended','-nopause','-nosound',
         '-ExecutePythonScript='+str(ROOT/'unreal/Scripts/import_game_branding.py'),
         '-abslog='+str(out/'branding-import.log')],'branding-import',300)
    progress_flags=['-AnomaliaZPrigimaliaProgressArt'] if a.progress_art else []
    visual_receipt=out/('realism-scene-'+uuid.uuid4().hex+'.json')
    os.environ['ANOMALIA_REALISM_SCENE_REPORT']=str(visual_receipt)
    run([editor,project,'-unattended','-nopause','-nosound','-NullRHI','-stdout','-FullStdOutLogOutput',
         '-abslog='+str(out/'create-realism-editor.log'),
         '-ExecutePythonScript='+str(ROOT/'unreal/Scripts/create_realism_validation.py')],'create-realism',900)
    visual_scene=json.loads(visual_receipt.read_text(encoding='utf-8'))
    if visual_scene.get('state')!='REALISM_VALIDATION_MAP_SAVED_NOT_PLAYTESTED' or visual_scene.get('sourceCommit')!=os.environ.get('GITHUB_SHA') or len(visual_scene.get('models',[]))!=8:
        raise RuntimeError('Fresh imported-art scene receipt missing or invalid')
    report['visualScene']=visual_scene
    visual_map='/Game/Maps/ANOMALIA_VisualValidation_v1'
    if a.progress_art:
        os.environ['ANOMALIA_PROGRESS_ART_REPORT']=str(out/'progress-art.json')
        os.environ['ANOMALIA_EDITOR_TASK']=str(ROOT/'scripts/world-features/apply-playable-progress-art.py')
        run([editor,project,'-unattended','-nopause','-nosound','-NullRHI',
             '-ExecutePythonScript='+str(ROOT/'scripts/world-features/run-editor-task.py'),
             '-abslog='+str(out/'progress-art.log')],'progress-art',900)
        progress=json.loads((out/'progress-art.json').read_text())
        if progress.get('state')!='PROGRESS_ART_SAVED_REQUIRES_PACKAGED_GAME_TEST' or progress.get('trees')!=20 or len(progress.get('houses',[]))!=2 or progress.get('rocks')!=24 or progress.get('groundFoliage')!=24 or progress.get('hiddenBackgroundPrototypes')!=12 or not progress.get('terrain') or not progress.get('road') or progress.get('forestTrees')!=32 or progress.get('forestGrass')!=96:
            raise RuntimeError('Fresh complete playable art report required')
        report['progressArt']=progress
    # Exercise the actual playable map before cooking. This catches interaction
    # failures in its real collision layout without waiting for a packaged build.
    interaction_probe=out/'editor-playable-smoke.json'
    run([editor,project,MAP+'?AnomaliaZPrigimaliaServerId=playable-smoke-'+uuid.uuid4().hex,'-game','-windowed','-ResX=1280','-ResY=720',
         '-d3d11','-sm5','-unattended','-nosound','-AnomaliaZPrigimaliaPlayableProbe='+str(interaction_probe),
         '-abslog='+str(out/'editor-playable-engine.log'),*progress_flags],'editor-playable',180)
    interaction=json.loads(interaction_probe.read_text(encoding='utf-8-sig'))
    report['editorPlayable']=interaction
    if interaction.get('state')!='PACKAGED_GAME_SMOKE_PASSED':
        raise RuntimeError('Playable-map interaction preflight failed: '+interaction.get('error','missing checks'))
    editor_review=out/'editor-visual/review.json';editor_review.parent.mkdir()
    run([editor,project,visual_map+'?AnomaliaZPrigimaliaServerId=visual-smoke-'+uuid.uuid4().hex,'-game','-windowed','-ResX=1280','-ResY=720',
         '-d3d11','-sm5','-unattended','-nosound','-AnomaliaZPrigimaliaVisualReview='+str(editor_review),'-abslog='+str(out/'editor-visual.log')],'editor-visual',300)
    if json.loads(editor_review.read_text(encoding='utf-8-sig')).get('state')!='PACKAGED_VISUAL_REVIEW_PASSED':
        raise RuntimeError('Imported-art scene failed in actual Editor game renderer')
    # Execute outside the deeply nested repository/evidence path. UE gameplay
    # writes server/map-scoped JSON plus atomic temporary suffixes under Saved.
    archive=Path(tempfile.mkdtemp(prefix='anomalia-win-',dir=os.environ.get('RUNNER_TEMP'))).resolve()
    uat=a.engine_root/'Engine/Build/BatchFiles/RunUAT.bat'
    run([os.environ.get('COMSPEC','cmd.exe'),'/d','/c',uat,'BuildCookRun','-project='+str(project),'-noP4','-unattended','-utf8output','-platform=Win64','-clientconfig=Development','-build','-cook','-stage','-pak','-archive','-archivedirectory='+str(archive),'-map='+MAP+'+'+visual_map,'-prereqs'],'package',5400)
    executables=list(archive.glob('Windows/AnomaliaZPrigimalia.exe'))
    if len(executables)!=1:raise RuntimeError('Unique actual packaged executable not found')
    exe=executables[0];probe=out/'packaged-smoke.json'
    shutil.copyfile(ROOT/'unreal/Build/Windows/Application.ico',archive/'Windows/Anomalia.ico')
    scope='playable-smoke-'+uuid.uuid4().hex
    run([exe,MAP+'?AnomaliaZPrigimaliaServerId='+scope,'-windowed','-ResX=1280','-ResY=720','-d3d11','-sm5','-unattended','-nosound','-nopause','-AnomaliaZPrigimaliaPlayableProbe='+str(probe),'-abslog='+str(out/'packaged-engine.log'),*progress_flags],'packaged-run',180)
    native=json.loads(probe.read_text(encoding='utf-8-sig'))
    required={'native_inventory_tobacco_use_has_risk_and_returns_waste','native_inventory_food_use_consumes_one_and_restores_hunger','native_playable_look_v2_cooked_materials_and_lights','main_menu_play_button','explicit_local_profile_save','native_world_HUD_and_three_vehicle_meshes','keyboard_character_movement','walk_through_house_doorway','world_pickup_into_native_inventory','native_inventory_open_close','three_vehicle_enter_accelerate_steer_exit'}
    if native.get('state')!='PACKAGED_GAME_SMOKE_PASSED' or not required.issubset(native.get('checks',[])) or native.get('buildCommit')!=os.environ.get('GITHUB_SHA') or 'visible_executable_build_identity' not in native.get('checks',[]):
        raise RuntimeError('Actual packaged gameplay smoke failed: '+native.get('error','missing checks'))
    if 'user_branding_intro_animates_and_reveals_main_menu' not in native.get('checks',[]):raise RuntimeError('Cooked user branding and startup animation did not pass')
    if a.progress_art and not {'validated_progress_houses_and_twenty_real_trees','validated_progress_real_rocks_and_ground_foliage','validated_playable_pbr_landscape_and_forest'}.issubset(native.get('checks',[])):
        raise RuntimeError('Cooked progress art was not verified by the executable')
    image=probe.with_suffix('.png')
    if not image.is_file() or image.stat().st_size<10000:raise RuntimeError('Fresh packaged GPU screenshot missing')
    resume=out/'packaged-resume.json'
    run([exe,MAP+'?AnomaliaZPrigimaliaServerId='+scope,'-windowed','-ResX=1280','-ResY=720','-d3d11','-sm5','-unattended','-nosound','-AnomaliaZPrigimaliaPlayableProbe='+str(resume),'-AnomaliaZPrigimaliaPlayableResume'],'packaged-resume',90)
    resumed=json.loads(resume.read_text(encoding='utf-8-sig'))
    if resumed.get('state')!='PACKAGED_GAME_SMOKE_PASSED' or not {'restarted_executable_restored_inventory_and_character_position','restarted_executable_restored_item_effects'}.issubset(resumed.get('checks',[])):
        raise RuntimeError('Actual executable restart did not restore character and inventory')
    report['resume']=resumed
    visual_probe=out/'packaged-visual/review.json';visual_probe.parent.mkdir()
    run([exe,visual_map+'?AnomaliaZPrigimaliaServerId=visual-smoke-'+uuid.uuid4().hex,'-windowed','-ResX=1280','-ResY=720','-d3d11','-sm5','-unattended','-nosound',
         '-AnomaliaZPrigimaliaVisualReview='+str(visual_probe),'-abslog='+str(out/'packaged-visual-engine.log')],'packaged-visual',300)
    visual=json.loads(visual_probe.read_text(encoding='utf-8-sig'))
    if visual.get('state')!='PACKAGED_VISUAL_REVIEW_PASSED' or len(visual.get('screenshots',[]))!=8 or not visual.get('dayAndNightCaptured'):
        raise RuntimeError('Real Windows visual review failed: '+visual.get('error','missing screenshots'))
    if any(not Path(p).is_file() or Path(p).stat().st_size<10000 for p in visual['screenshots']):raise RuntimeError('Missing actual Windows visual capture')
    report['visualReview']=visual
    if a.progress_art:
        notices=archive/'Windows/ThirdPartyNotices';notices.mkdir(parents=True,exist_ok=True)
        for group in ('RealismValidation_v2','ResidentialPhotogrammetryPrepared_v1','PlayableLandscape_v2'):
            source=ROOT/'unreal/SourceAssets'/group/'CREDITS.md'
            destination=notices/(group+'-CREDITS.md')
            # Extended-length paths are needed on Windows even if UE accepts its own paths.
            def copy_path(path):
                full=str(path.resolve())
                if os.name!='nt' or full.startswith('\\\\?\\'):return full
                return '\\\\?\\UNC\\'+full[2:] if full.startswith('\\\\') else '\\\\?\\'+full
            shutil.copyfile(copy_path(source),copy_path(destination))
            if source.read_bytes()!=Path(copy_path(destination)).read_bytes():raise RuntimeError('Packaged attribution copy mismatch')
    report.update(state='PACKAGED_WINDOWS_SMOKE_PASSED',executable=str(exe),native=native,screenshot=str(image),archive=str(archive/'Windows'),limitations=['provisional_original_art','prototype_ground_vehicle_physics','drop_UI_not_implemented','item_specific_weapon_crafting_and_medical_systems_incomplete'])
except Exception as error: report['error']=str(error)
finally:
    (out/'package-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
raise SystemExit(0 if report['state']=='PACKAGED_WINDOWS_SMOKE_PASSED' else 1)

