"""Add native navigable sea to the existing archipelago; preserve all authored actors.
The native water actor supplies buoyancy/depth bounds, not waves or swimming.
Run after create_archipelago_world.py with the project compiled.
"""
import json
import os
from pathlib import Path
import uuid
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
PACKAGE='/Game/Maps/ANOMALIA_Archipelago_v2'
LABEL='ANOMALIA_Archipelago_NavigableSea_v1'
TAG=unreal.Name('ANOMALIA_TransportInfrastructure_v1')
OUT=Path(os.environ.get('ANOMALIA_SEA_REPORT',str(ROOT/'Saved/BuildValidation'/('navigable-sea-'+uuid.uuid4().hex+'.json'))))
report=dict(state='FAILED',sourceCommit=os.environ.get('GITHUB_SHA','manual'),mapPackage=PACKAGE,playtested=False,waveSimulation=False,cityComplete=False)
try:
    level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not unreal.EditorAssetLibrary.does_asset_exist(PACKAGE):raise RuntimeError('Create the archipelago before configuring transport')
    if not level.load_level(PACKAGE):raise RuntimeError('Could not load archipelago')
    present={a.get_actor_label():a for a in actors.get_all_level_actors()}
    if 'ANOMALIA_OriginalArchipelago_48km' not in present:raise RuntimeError('Expected original landscape missing; map preserved')
    cls=unreal.load_class(None,'/Script/AnomaliaZPrigimalia.AnomaliaZPrigimaliaNavigableWater')
    if not cls:raise RuntimeError('Native water class not loaded')
    if LABEL in present:
        sea=present[LABEL]
        if sea.get_class()!=cls or TAG not in sea.tags:raise RuntimeError('Unowned sea actor preserved')
        # Authored edits remain intact; an unchanged rerun does not save anything.
        report.update(state='EXISTING_NAVIGABLE_SEA_PRESERVED_NOT_PLAYTESTED',surfaceOffsetCm=sea.get_editor_property('surface_offset'))
    else:
        # 48 km square, flat sea level zero. Terrain collisions provide the actual seabed.
        # The lower bound lies below the deepest generated seabed (about -440 m).
        sea=actors.spawn_actor_from_class(cls,unreal.Vector(0,0,-30000))
        if not sea:raise RuntimeError('Could not create native sea region')
        sea.set_actor_label(LABEL);sea.tags=[TAG]
        sea.set_editor_property('surface_offset',30000)
        sea.get_editor_property('bounds').set_box_extent(unreal.Vector(2400000,2400000,30400),False)
        # One global region must remain loaded while World Partition streams coastal tiles.
        sea.set_editor_property('is_spatially_loaded',False)
        if not level.save_all_dirty_levels():raise RuntimeError('Could not save navigable sea')
        if not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):raise RuntimeError('Could not save external sea actor')
        report.update(state='NAVIGABLE_SEA_CREATED_NOT_PLAYTESTED',widthMeters=48000,depthMeters=48000,surfaceMeters=0,alwaysLoaded=True)
except Exception as error:
    report['error']=str(error)
    raise
finally:
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    unreal.log('ANOMALIA_SEA_REPORT='+str(OUT))
