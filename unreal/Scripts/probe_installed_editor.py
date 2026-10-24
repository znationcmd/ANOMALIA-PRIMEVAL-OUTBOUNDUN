"""Read-only validation of the copied development project, never starts gameplay."""
import json,os
from pathlib import Path
import unreal
report=dict(state='FAILED',headless=True,graphicalLaunchTested=False)
try:
 package=os.environ.get('ANOMALIA_CAPTURE_MAP','/Game/Maps/ANOMALIA_Archipelago_v2')
 if package not in ('/Game/Maps/ANOMALIA_Archipelago_v2','/Game/Maps/ANOMALIA_Inhabited_v2'):raise RuntimeError('Unknown installed map')
 if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(package):raise RuntimeError('Installed map cannot open')
 wp=unreal.AnomaliaWorldImportLibrary
 snapshot=json.loads(wp.get_archipelago_actor_descriptors())
 if snapshot.get('state')!='COPIED_DESCRIPTOR_VALUES':raise RuntimeError('Copied actor descriptors unavailable')
 desc=snapshot['actors']
 if not wp.set_archipelago_actors_loaded([d['guid'] for d in desc if d['nativeClass'] in ('/Script/Landscape.Landscape','/Script/Landscape.LandscapeStreamingProxy')],True):raise RuntimeError('Copied Landscape streaming refused')
 native=json.loads(unreal.AnomaliaWorldImportLibrary.refresh_archipelago_render_resources(False))
 if native.get('componentCount')!=576 or native.get('landscapesLayerMergeRequested')!=0:raise RuntimeError('Copied Landscape incomplete')
 if max(c['boundsMaxZCm'] for c in native['components'])<100000:raise RuntimeError('Copied map lost its relief')
 actual=Path(unreal.Paths.project_saved_dir()).resolve();expected=Path(os.environ['ANOMALIA_EXPECTED_SAVED']).resolve()
 if str(actual).casefold()!=str(expected).casefold():raise RuntimeError('Shared Saved directory mismatch')
 # Unreal returns an engine-relative Content path on Windows. Enumerating its
 # entire imported-art tree hits MAX_PATH in deep asset directories even though
 # the requested map already opened. Inspect the actual Maps directory only.
 content=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir()))
 map_dir=content/'Maps'
 if not (map_dir/(package.rsplit('/',1)[1]+'.umap')).is_file():raise RuntimeError('Requested installed map file missing')
 maps=[p.relative_to(content).as_posix() for p in map_dir.rglob('*.umap')]
 report.update(state='COPIED_EDITOR_PROJECT_OPENED_HEADLESS',mapPackage=package,maps=maps,mapsScope='Content/Maps',partitionActorCount=len(desc),projectDir=str(Path(unreal.Paths.project_dir()).resolve()),savedDir=str(actual),landscapeComponents=576,forcedLayerMerges=0)
except Exception as error:
 report['error']=str(error)
finally:
 Path(os.environ['ANOMALIA_PC_UPDATE_REPORT']).write_text(json.dumps(report,indent=2)+'\n')
 unreal.log(json.dumps(report))
