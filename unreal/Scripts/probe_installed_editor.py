"""Read-only validation of the copied development project, never starts gameplay."""
import json,os
from pathlib import Path
import unreal
report=dict(state='FAILED',headless=True,graphicalLaunchTested=False)
try:
 package=os.environ.get('ANOMALIA_CAPTURE_MAP','/Game/Maps/ANOMALIA_Archipelago_v2')
 if package not in ('/Game/Maps/ANOMALIA_Archipelago_v2','/Game/Maps/ANOMALIA_Inhabited_v2'):raise RuntimeError('Unknown installed map')
 if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(package):raise RuntimeError('Installed map cannot open')
 desc=unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or []
 unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in desc if d.native_class.get_path_name() in ('/Script/Landscape.Landscape','/Script/Landscape.LandscapeStreamingProxy')])
 native=json.loads(unreal.AnomaliaWorldImportLibrary.refresh_archipelago_render_resources(False))
 if native.get('componentCount')!=576 or native.get('landscapesLayerMergeRequested')!=0:raise RuntimeError('Copied Landscape incomplete')
 if max(c['boundsMaxZCm'] for c in native['components'])<100000:raise RuntimeError('Copied map lost its relief')
 actual=Path(unreal.Paths.project_saved_dir()).resolve();expected=Path(os.environ['ANOMALIA_EXPECTED_SAVED']).resolve()
 if str(actual).casefold()!=str(expected).casefold():raise RuntimeError('Shared Saved directory mismatch')
 maps=[p.relative_to(Path(unreal.Paths.project_content_dir())).as_posix() for p in Path(unreal.Paths.project_content_dir()).rglob('*.umap')]
 report.update(state='COPIED_EDITOR_PROJECT_OPENED_HEADLESS',mapPackage=package,maps=maps,partitionActorCount=len(desc),projectDir=str(Path(unreal.Paths.project_dir()).resolve()),savedDir=str(actual),landscapeComponents=576,forcedLayerMerges=0)
except Exception as error:
 report['error']=str(error)
finally:
 Path(os.environ['ANOMALIA_PC_UPDATE_REPORT']).write_text(json.dumps(report,indent=2)+'\n')
 unreal.log(json.dumps(report))
