"""Add real licensed plants to clear parcels; reopen separately to verify saves."""
import hashlib,importlib.util,json,math,os
from pathlib import Path
import unreal

PACKAGE='/Game/Maps/ANOMALIA_Inhabited_v2'
OWNER='ANOMALIA_UrbanGreenery_v1'

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def digest(file):
    h=hashlib.sha256()
    with file.open('rb') as stream:
        for part in iter(lambda:stream.read(1048576),b''):h.update(part)
    return h.hexdigest()

def mesh_info(mesh,model):
    bounds=mesh.get_bounds()
    return dict(origin=[bounds.origin.x,bounds.origin.y,bounds.origin.z],extent=[bounds.box_extent.x,bounds.box_extent.y,bounds.box_extent.z],sourceSha=model['sha256'])

def verify_clusters(plan,loaded,meshes,plan_sha):
    expected={g['label']:g for g in plan['clusters']}
    if set(expected)!=set(loaded):raise RuntimeError('Planting cluster identities do not match')
    verified=0
    for label,group in expected.items():
        actor=loaded[label];tags={str(t) for t in actor.tags}
        if OWNER not in tags or 'ANOMALIA_GreeneryPlan_'+plan_sha[:16] not in tags:raise RuntimeError('Cluster ownership mismatch')
        component=actor.get_editor_property('instances');model=group['instances'][0]['model']
        if component.get_editor_property('static_mesh')!=meshes[model]:raise RuntimeError('Vegetation mesh changed')
        if component.get_instance_count()!=len(group['instances']):raise RuntimeError('Instance count changed')
        if any(component.get_editor_property('override_materials')):raise RuntimeError('Vegetation materials changed')
        for index,item in enumerate(group['instances']):
            transform=component.get_instance_transform(index,world_space=True)
            position=transform.translation;scale=transform.scale3d;yaw=transform.rotation.rotator().yaw
            if max(abs(a-b) for a,b in zip((position.x,position.y,position.z),item['locationCm']))>.6:raise RuntimeError('Saved plant position mismatch')
            if max(abs(s-item['scale']) for s in (scale.x,scale.y,scale.z))>.0001 or abs((yaw-item['yaw']+180)%360-180)>.02:raise RuntimeError('Saved plant orientation/scale mismatch')
            verified+=1
    return verified

def main():
    root=Path(unreal.Paths.project_dir()).resolve();out=Path(os.environ['ANOMALIA_URBAN_REPORT']);mode=os.environ['ANOMALIA_URBAN_MODE']
    report=dict(state='FAILED',mode=mode,mapPackage=PACKAGE,sourceCommit=os.environ.get('GITHUB_SHA'),terrainModified=False,housesModified=False,streetsModified=False,fullMapComplete=False,photorealismApproved=False,gameplayTested=False,newPlantCollision=False)
    try:
        planning=module('urban_planting',root/'Scripts/urban_greenery.py')
        ground=module('urban_ground',root/'Scripts/archipelago_population.py')
        marker=root/'Saved/UrbanGreenery/v1-ownership.json';plan_file=marker.with_name('v1-plan.json')
        source=root/'SourceAssets/RealismValidation_v2'
        manifest=json.loads((source/'manifest.json').read_text());known={m['id']:m for m in manifest['models']};meshes={};infos={}
        for ident in ('island_tree_02','grass_medium_01'):
            item=known[ident];file=(source/item['file']).resolve()
            if not file.is_relative_to(source) or digest(file)!=item['sha256']:raise RuntimeError('Prepared plant source checksum failed')
            mesh=unreal.load_asset(item['objectPath']+'_r2')
            if not isinstance(mesh,unreal.StaticMesh) or unreal.EditorAssetLibrary.get_metadata_tag(mesh,'AnomaliaZPrigimaliaRealismSha256')!=item['sha256']:raise RuntimeError('Verified imported plant required')
            if not mesh.get_editor_property('static_materials') or any(not slot.material_interface for slot in mesh.get_editor_property('static_materials')):raise RuntimeError('Real plant material missing')
            meshes[ident]=mesh;infos[ident]=mesh_info(mesh,item)
        level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        if not level.load_level(PACKAGE):raise RuntimeError('Existing populated map did not open')
        wp=unreal.AnomaliaZPrigimaliaWorldImportLibrary;actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        snapshot=json.loads(wp.get_archipelago_actor_descriptors())
        if snapshot.get('state')!='COPIED_DESCRIPTOR_VALUES':raise RuntimeError('Copied saved bounds required')
        descriptors=snapshot['actors'];present=[d for d in descriptors if d['label'].startswith(planning.PREFIX)]
        if marker.exists():
            ownership=json.loads(marker.read_text());raw=plan_file.read_bytes()
            if ownership.get('mapPackage')!=PACKAGE or digest(plan_file)!=ownership.get('planSha256'):raise RuntimeError('Owned planting plan checksum failed')
            plan=json.loads(raw);plan_sha=ownership['planSha256']
            if ownership['models']!=infos:raise RuntimeError('Plant source or bounds changed; saved planting preserved')
        else:
            if mode!='create' or present:raise RuntimeError('Existing/unowned partial planting preserved')
            backup=json.loads(Path(os.environ['ANOMALIA_URBAN_BACKUP_REPORT']).read_text())
            if backup.get('mapPackage')!=PACKAGE or not Path(backup['archive']).is_file() or digest(Path(backup['archive']))!=backup['sha256']:raise RuntimeError('Verified pre-authoring map archive required')
            fresh=json.loads(Path(os.environ['ANOMALIA_URBAN_HOUSE_AUDIT']).read_text())
            if fresh.get('state')!='SAVED_RESIDENTIAL_NATIVE_AUDIT_PASSED' or fresh.get('sourceCommit')!=report['sourceCommit']:raise RuntimeError('Fresh saved-house audit required')
            receipts=[]
            for file in (root/'Saved/TransportCity').glob('run-*/populated-world.json'):
                value=json.loads(file.read_text())
                if value.get('state')=='POPULATED_WORLD_CREATED_NOT_PLAYTESTED' and value.get('mapPackage')==PACKAGE:receipts.append((file.stat().st_mtime,file))
            if not receipts:raise RuntimeError('Original population plan required')
            population=json.loads((max(receipts)[1].parent/'population-plan.json').read_text())
            if len(population['buildings'])!=4760 or len(population['settlements'])!=27:raise RuntimeError('Complete matching population plan required')
            def height(east,north):return unreal.AnomaliaZPrigimaliaWorldImportLibrary.inhabited_archipelago_height(east,north)
            plan=planning.plan_greenery(population,descriptors,infos,ground.sampled_surface(height),ground.ground_envelope)
            if plan['counts'].get('island_tree_02',0)<600:raise RuntimeError('Insufficient clear safe planting; no actors authored: '+json.dumps(plan['counts']))
            raw=json.dumps(plan,sort_keys=True,separators=(',',':')).encode();plan_sha=hashlib.sha256(raw).hexdigest()
            out.with_name('proposed-plan.json').write_bytes(raw)
            cluster_class=unreal.load_class(None,'/Script/AnomaliaZPrigimalia.AnomaliaZPrigimaliaSceneryCluster')
            if not cluster_class:raise RuntimeError('Native HISM scenery class missing')
            loaded={};packages={}
            for group in plan['clusters']:
                first=group['instances'][0];cx=math.floor(first['east']/1000);cy=math.floor(first['north']/1000)
                actor=actors.spawn_actor_from_class(cluster_class,unreal.Vector((cx*1000+500)*100,-(cy*1000+500)*100,0))
                if not actor:raise RuntimeError('Planting cluster spawn failed')
                actor.modify();actor.set_actor_label(group['label']);actor.tags=[unreal.Name(OWNER),unreal.Name('ANOMALIA_GreeneryPlan_'+plan_sha[:16])]
                actor.set_editor_property('is_spatially_loaded',True)
                component=actor.get_editor_property('instances');component.modify();component.set_static_mesh(meshes[first['model']])
                end=45000 if first['model']=='island_tree_02' else 14000
                component.set_editor_property('instance_start_cull_distance',end-5000);component.set_editor_property('instance_end_cull_distance',end)
                for item in group['instances']:
                    transform=unreal.Transform(location=unreal.Vector(*item['locationCm']),rotation=unreal.Rotator(yaw=item['yaw']),scale=unreal.Vector(*([item['scale']]*3)))
                    if component.add_instance(transform,world_space=True)<0:raise RuntimeError('Real plant instance failed')
                loaded[group['label']]=actor;package=actor.get_outermost();name=package.get_name()
                if name!=PACKAGE and not name.startswith('/Game/__ExternalActors__/Maps/ANOMALIA_Inhabited_v2/'):raise RuntimeError('Refusing unrelated package save')
                packages[name]=package
            verified=verify_clusters(plan,loaded,meshes,plan_sha)
            if not unreal.EditorLoadingAndSavingUtils.save_packages(list(packages.values()),False):raise RuntimeError('Planting packages did not save')
            marker.parent.mkdir(parents=True,exist_ok=True)
            with plan_file.open('xb') as stream:stream.write(raw)
            with marker.open('x') as stream:json.dump(dict(mapPackage=PACKAGE,planSha256=plan_sha,models=infos,sourceCommit=report['sourceCommit']),stream,indent=2)
            report.update(state='URBAN_PLANTS_SAVED_REQUIRES_REOPEN',verifiedInstances=verified,clusters=len(plan['clusters']),counts=plan['counts'],planSha256=plan_sha)
            return
        # Existing vegetation is inspected without adding, moving or deleting it.
        expected={g['label'] for g in plan['clusters']}
        if len(present)!=len(expected) or {d['label'] for d in present}!=expected:raise RuntimeError('Saved planting descriptors missing or duplicated')
        if not wp.set_archipelago_actors_loaded([d['guid'] for d in present],True):raise RuntimeError('Owned planting streaming refused')
        loaded={a.get_actor_label():a for a in actors.get_all_level_actors() if a.get_actor_label() in expected}
        verified=verify_clusters(plan,loaded,meshes,plan_sha)
        report.update(state='SAVED_URBAN_PLANTS_VERIFIED',verifiedInstances=verified,clusters=len(plan['clusters']),counts=plan['counts'],planSha256=plan_sha,packagesSaved=False)
    except Exception as error:
        report['error']=str(error);raise
    finally:
        out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2))

main()
