"""Append real original sign meshes at validated settlement entrances. Never erase existing actors."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=Path(os.environ.get('ANOMALIA_SIGN_REPORT',str(ROOT/'Saved/ReactiveValidation/place-signs.json')))
report=dict(state='FAILED',sourceCommit=os.environ.get('GITHUB_SHA','manual'),placements=[],rejected=[],playtested=False)
OWNER=unreal.Name('ANOMALIA_NamedSigns_v1')
try:
    spec=importlib.util.spec_from_file_location('place_identity',ROOT/'Scripts/place_identity.py')
    identity=importlib.util.module_from_spec(spec);spec.loader.exec_module(identity)
    matches=[]
    for receipt in (ROOT/'Saved/TransportCity').glob('run-*/populated-world.json'):
        try:
            data=json.loads(receipt.read_text())
            plan_file=receipt.with_name('population-plan.json')
            if data.get('state')=='POPULATED_WORLD_CREATED_NOT_PLAYTESTED' and plan_file.is_file():
                plan=json.loads(plan_file.read_text())
                if plan.get('mapPackage')==data.get('mapPackage') and len(plan.get('buildings',[]))==data.get('houses'):
                    matches.append((receipt.stat().st_mtime,plan))
        except (OSError,ValueError): continue
    if not matches: raise RuntimeError('Validated populated world and matching settlement plan required')
    _,plan=max(matches,key=lambda p:p[0]);package=plan['mapPackage'];report['mapPackage']=package
    if package not in ['/Game/Maps/ANOMALIA_Inhabited_v1','/Game/Maps/ANOMALIA_Inhabited_v2']:
        raise RuntimeError('Unsupported population map; existing project preserved')
    proposals=identity.settlement_signs(plan)
    source=ROOT/'SourceAssets/OriginalSigns_v1/sign.glb'
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    native=unreal.load_class(None,'/Script/AnomaliaPrimeval.AnomaliaPlaceSign')
    if not native: raise RuntimeError('Compile native sign actor before placement')
    level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level.load_level(package): raise RuntimeError('Cannot open validated population map')
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    imported='/Game/Anomalia/Infrastructure/OriginalSigns_v1'
    manifest=ROOT/'Saved/ReactiveValidation/sign-import.json'
    if manifest.exists():
        old=json.loads(manifest.read_text())
        if old['sha256']!=digest: raise RuntimeError('Changed sign source; previous art preserved')
        mesh=unreal.load_asset(old['mesh'])
        if not isinstance(mesh,unreal.StaticMesh): raise RuntimeError('Previously imported sign mesh missing')
    else:
        if unreal.EditorAssetLibrary.does_directory_exist(imported): raise RuntimeError('Unowned import namespace preserved')
        task=unreal.AssetImportTask();task.filename=str(source);task.destination_path=imported
        task.automated=True;task.replace_existing=False;task.save=True
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);task.get_objects()
        meshes=[unreal.load_asset(p) for p in unreal.EditorAssetLibrary.list_assets(imported,recursive=True,include_folder=False)]
        meshes=[m for m in meshes if isinstance(m,unreal.StaticMesh)]
        if len(meshes)!=1: raise RuntimeError('Expected exactly one original sign mesh')
        mesh=meshes[0]
        manifest.parent.mkdir(parents=True,exist_ok=True)
        manifest.write_text(json.dumps(dict(sha256=digest,mesh=mesh.get_path_name()),indent=2)+'\n')
    bounds=mesh.get_bounds();size=bounds.box_extent*2
    if not (270<max(size.x,size.y)<290 and 230<size.z<235): raise RuntimeError('Imported sign is not full scale')
    existing={a.get_actor_label():a for a in actors.get_all_level_actors()}
    for item in proposals:
        label='ANOMALIA_Sign_'+item['signId']
        if label in existing:
            old=existing[label]
            if old.get_class()!=native or OWNER not in old.tags: raise RuntimeError('Unowned sign actor preserved: '+label)
            if str(old.get_editor_property('place_id'))!=item['id']: raise RuntimeError('Existing sign identity conflict')
            report['placements'].append(dict(**item,existing=True));continue
        e,n=item['east']*100,item['north']*100
        if any(abs(item['east']-b['east'])<b['width']/2+4 and abs(item['north']-b['north'])<b['depth']/2+4 for b in plan['buildings']):
            report['rejected'].append(dict(id=item['signId'],reason='BUILDING_CLEARANCE'));continue
        expected_z=unreal.AnomaliaWorldImportLibrary.inhabited_archipelago_height(item['east'],item['north'])*100
        actor=actors.spawn_actor_from_class(native,unreal.Vector(e,n,expected_z),unreal.Rotator(0,item['yaw'],0))
        if not actor: raise RuntimeError('Cannot spawn original native sign')
        if not actor.snap_to_ground(expected_z):
            actors.destroy_actor(actor)
            report['rejected'].append(dict(id=item['signId'],reason='NO_MATCHING_LOADED_DRY_GROUND'));continue
        actor.set_actor_label(label);actor.tags=[OWNER]
        actor.set_editor_property('place_id',unreal.Name(item['id']))
        actor.set_editor_property('place_name',unreal.Text(item['name']))
        board=actor.get_editor_property('board');board.set_static_mesh(mesh)
        if size.x>size.y: board.set_relative_rotation(unreal.Rotator(0,90,0),False,True)
        # Plate orientation is independent of the native text facing.
        report['placements'].append(dict(**item,existing=False))
    if not level.save_all_dirty_levels(): raise RuntimeError('Cannot save named signage')
    if not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True): raise RuntimeError('Cannot save external sign actors')
    report['state']='NAMED_SIGNS_SAVED_NOT_PLAYTESTED'
except Exception as error:
    report['error']=str(error)
    raise
finally:
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
