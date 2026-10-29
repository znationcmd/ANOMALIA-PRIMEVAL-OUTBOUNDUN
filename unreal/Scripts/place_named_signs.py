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
    native=unreal.load_class(None,'/Script/AnomaliaZPrigimalia.AnomaliaZPrigimaliaPlaceSign')
    if not native: raise RuntimeError('Compile native sign actor before placement')
    level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level.load_level(package): raise RuntimeError('Cannot open validated population map')
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    descriptors=unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or []
    terrain_guids=[]
    for descriptor in descriptors:
        cls=descriptor.get_editor_property('native_class')
        if cls and cls.get_path_name() in ['/Script/Landscape.Landscape','/Script/Landscape.LandscapeStreamingProxy']:
            terrain_guids.append(descriptor.get_editor_property('guid'))
    unreal.WorldPartitionBlueprintLibrary.load_actors(terrain_guids)
    report['loadedTerrainDescriptors']=len(terrain_guids)
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
    used=[a.get_actor_location() for a in existing.values() if a.get_class()==native]
    for item in proposals:
        label='ANOMALIA_Sign_'+item['signId']
        if label in existing:
            old=existing[label]
            if old.get_class()!=native or OWNER not in old.tags: raise RuntimeError('Unowned sign actor preserved: '+label)
            if str(old.get_editor_property('place_id'))!=item['id']: raise RuntimeError('Existing sign identity conflict')
            # Repair an empty label from an earlier authoring pass without replacing authored text.
            for field in ['front_text','back_text']:
                label_component=old.get_editor_property(field)
                if not str(label_component.get_editor_property('text')):
                    label_component.set_text(old.get_editor_property('place_name'))
            report['placements'].append(dict(**item,existing=True));continue
        actor=None; chosen=None
        for candidate in identity.sign_candidates(item,plan['buildings']):
            e,n=candidate['east']*100,-candidate['north']*100
            if any((e-p.x)**2+(n-p.y)**2<500**2 for p in used): continue
            if any(abs(candidate['east']-b['east'])<b['width']/2+4 and abs(candidate['north']-b['north'])<b['depth']/2+4 for b in plan['buildings']): continue
            expected_z=unreal.AnomaliaZPrigimaliaWorldImportLibrary.inhabited_archipelago_height(candidate['east'],candidate['north'])*100
            attempt=actors.spawn_actor_from_class(native,unreal.Vector(e,n,expected_z),unreal.Rotator(0,item['yaw'],0))
            if not attempt: raise RuntimeError('Cannot spawn original native sign')
            if attempt.snap_to_ground(expected_z):
                actor=attempt;chosen=candidate;break
            actors.destroy_actor(attempt)
        if not actor:
            report['rejected'].append(dict(id=item['signId'],reason='NO_DRY_CLEAR_CORRIDOR_IN_SAME_TOWN'));continue
        actor.set_actor_label(label);actor.tags=[OWNER]
        actor.set_editor_property('is_spatially_loaded',False)
        actor.set_editor_property('place_id',unreal.Name(item['id']))
        actor.set_editor_property('place_name',unreal.Text(item['name']))
        board=actor.get_editor_property('board');board.set_static_mesh(mesh)
        if size.x>size.y: board.set_relative_rotation(unreal.Rotator(0,90,0),False,True)
        # Explicitly populate the actual scene text after setting the saved place properties.
        for field in ['front_text','back_text']:
            text=actor.get_editor_property(field)
            text.set_text(unreal.Text(item['name']))
            text.set_world_size(min(22,380/max(1,len(item['name']))))
        used.append(actor.get_actor_location())
        report['placements'].append(dict(**item,existing=False,actualEast=chosen['east'],actualNorth=chosen['north']))
    if not level.save_all_dirty_levels(): raise RuntimeError('Cannot save named signage')
    if not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True): raise RuntimeError('Cannot save external sign actors')
    report['state']='NAMED_SIGNS_SAVED_NOT_PLAYTESTED' if not report['rejected'] else 'PARTIAL_NAMED_SIGNS_SAVED_NOT_PLAYTESTED'
except Exception as error:
    report['error']=str(error)
    raise
finally:
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
