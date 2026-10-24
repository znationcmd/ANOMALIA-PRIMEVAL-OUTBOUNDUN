"""Replace owned generated exteriors after a complete preflight and immutable backup.
Artist edits, rejected parcels, terrain and player saves are preserved.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
PACKAGE='/Game/Maps/ANOMALIA_Inhabited_v2'
OWNER=unreal.Name('ANOMALIA_Inhabited_v1')
UPGRADE=unreal.Name('ANOMALIA_ResidentialUpgrade_v1')
OUT=Path(os.environ['ANOMALIA_RESIDENTIAL_UPGRADE_REPORT'])
report=dict(state='FAILED',mapPackage=PACKAGE,sourceCommit=os.environ.get('GITHUB_SHA'),
            terrainModified=False,playerSavesModified=False,actorsDeleted=0,
            exteriorOnly=True,fullMapComplete=False,photorealismApproved=False,replaced=0)

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,file)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result

def xyz(v):return [v.x,v.y,v.z]

def close(a,b,tolerance=.5):return max(abs(x-y) for x,y in zip(a,b))<=tolerance

def digest(file):
    h=hashlib.sha256()
    with file.open('rb') as stream:
        for data in iter(lambda:stream.read(1024*1024),b''):h.update(data)
    return h.hexdigest()

try:
    backup=json.loads(Path(os.environ['ANOMALIA_RESIDENTIAL_BACKUP_REPORT']).read_text())
    if backup.get('mapPackage')!=PACKAGE or not Path(backup['archive']).is_file() or digest(Path(backup['archive']))!=backup['sha256']:
        raise RuntimeError('Complete verified pre-authoring world archive required')
    ground=module('residential_ground',ROOT/'Scripts/archipelago_population.py')
    layout=module('residential_layout',ROOT/'Scripts/residential_replacement.py')
    candidates=[]
    for path in (ROOT/'Saved/TransportCity').glob('run-*/populated-world.json'):
        try:
            receipt=json.loads(path.read_text())
            if receipt.get('state')=='POPULATED_WORLD_CREATED_NOT_PLAYTESTED' and receipt.get('mapPackage')==PACKAGE:
                candidates.append((path.stat().st_mtime,path))
        except (ValueError,OSError):continue
    if not candidates:raise RuntimeError('Owned original population receipt required')
    receipt=max(candidates)[1]
    plan=json.loads((receipt.parent/'population-plan.json').read_text())
    items={'ANOMALIA_Inhabited1_'+item['id']:item for item in plan['buildings']}
    if plan.get('mapPackage')!=PACKAGE or len(items)!=4760:raise RuntimeError('Complete matching 4,760-house plan required')
    source=ROOT/'SourceAssets/ResidentialPhotogrammetryPrepared_v1'
    manifest=json.loads((source/'manifest.json').read_text());models={m['id']:m for m in manifest['models']}
    meshes={};bounds={}
    for ident in layout.MODELS:
        item=models[ident];file=(source/item['file']).resolve()
        if not file.is_relative_to(source) or digest(file)!=item['sha256']:raise RuntimeError('Prepared scan checksum mismatch: '+ident)
        mesh=unreal.load_asset(item['objectPath'])
        if not isinstance(mesh,unreal.StaticMesh) or unreal.EditorAssetLibrary.get_metadata_tag(mesh,'AnomaliaWorldFeatureSha256')!=item['sha256']:
            raise RuntimeError('Verified imported scanned house required: '+ident)
        materials=mesh.get_editor_property('static_materials')
        if not materials or any(not slot.material_interface for slot in materials):raise RuntimeError('Scanned house material missing')
        meshes[ident]=mesh;b=mesh.get_bounds();bounds[ident]=(xyz(b.origin),xyz(b.box_extent))
    base=json.loads((ROOT/'SourceAssets/RealismValidation_v2/manifest.json').read_text())
    original=next(m for m in base['models'] if m['id']=='detached_house')
    old_mesh=unreal.load_asset(original['objectPath']+'_r2')
    if not old_mesh or unreal.EditorAssetLibrary.get_metadata_tag(old_mesh,'AnomaliaRealismSha256')!=original['sha256']:
        raise RuntimeError('Known original generated-house mesh required')
    level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);wp=unreal.AnomaliaWorldImportLibrary
    if not level.load_level(PACKAGE):raise RuntimeError('Existing populated world did not open')
    snapshot=json.loads(wp.get_archipelago_actor_descriptors())
    if snapshot.get('state')!='COPIED_DESCRIPTOR_VALUES':raise RuntimeError('Owned descriptor snapshot unavailable')
    descriptors=[d for d in snapshot['actors'] if d['label'] in items]
    if len(descriptors)!=len(items) or len({d['label'] for d in descriptors})!=len(items):raise RuntimeError('Owned house descriptors missing or ambiguous')
    descriptors.sort(key=lambda d:d['label'])
    initially_loaded={a.get_actor_label() for a in actors.get_all_level_actors()}
    def height(east,north):
        # Do not retain UE 5.8 bound native callables in cached Python closures.
        return unreal.AnomaliaWorldImportLibrary.inhabited_archipelago_height(east,north)
    surface=ground.sampled_surface(height)
    records={};stats={'already':0,'replace':0,'artist-edit':0,'expanded-footprint-relief':0,'wet-or-high':0}
    def batch(start):
        desc=descriptors[start:start+64];labels={d['label'] for d in desc}
        if not wp.set_archipelago_actors_loaded([d['guid'] for d in desc],True):raise RuntimeError('Owned house streaming request refused')
        loaded={a.get_actor_label():a for a in actors.get_all_level_actors() if a.get_actor_label() in labels}
        if set(loaded)!=labels:raise RuntimeError('Saved house batch did not fully load')
        return loaded,[d['guid'] for d in desc if d['label'] not in initially_loaded]
    def unchanged(actor,mesh,location,scale,yaw):
        return (OWNER in actor.tags and isinstance(actor,unreal.StaticMeshActor) and
                actor.static_mesh_component.get_editor_property('static_mesh')==mesh and
                close(xyz(actor.get_actor_location()),location) and close(xyz(actor.get_actor_scale3d()),scale,.0001) and
                abs((actor.get_actor_rotation().yaw-yaw+180)%360-180)<.01 and
                not any(actor.static_mesh_component.get_editor_property('override_materials')))
    # Preflight every actor and expanded footprint before changing any package.
    for start in range(0,len(descriptors),64):
        loaded,unload=batch(start)
        try:
            for label,actor in loaded.items():
                item=items[label];ident=layout.model_for(item['id'])
                target=layout.placement(item,*bounds[ident],surface,ground.ground_envelope)
                status=target.get('rejected')
                if not status:
                    scale=[target['scale']]*3
                    if UPGRADE in actor.tags and unchanged(actor,meshes[ident],target['locationCm'],scale,target['yaw']):status='already'
                    elif unchanged(actor,old_mesh,[item['east']*100,-item['north']*100,item['z']*100],[1.,1.,1.],item['yaw']):status='replace'
                    else:status='artist-edit'
                stats[status]+=1
                records[label]=dict(status=status,target=target,oldMesh=actor.static_mesh_component.get_editor_property('static_mesh').get_path_name() if isinstance(actor,unreal.StaticMeshActor) and actor.static_mesh_component.get_editor_property('static_mesh') else None,
                                    oldLocationCm=xyz(actor.get_actor_location()),oldScale=xyz(actor.get_actor_scale3d()),oldYaw=actor.get_actor_rotation().yaw,oldTags=[str(t) for t in actor.tags])
        finally:
            loaded.clear();actor=None
            if not wp.set_archipelago_actors_loaded(unload,False):raise RuntimeError('Owned house unload refused')
    report['preflight']=stats
    if stats['already']+stats['replace']<4000:raise RuntimeError('Insufficient unchanged owned houses; preserve world for inspection')
    rollback=OUT.with_name('residential-transform-rollback.json')
    with rollback.open('x',encoding='utf-8') as stream:json.dump(dict(mapPackage=PACKAGE,backup=backup,actors=records),stream,indent=2)
    report['rollback']=str(rollback)
    for start in range(0,len(descriptors),64):
        loaded,unload=batch(start);packages={}
        try:
            for label,actor in loaded.items():
                record=records[label]
                if record['status']!='replace':continue
                if not unchanged(actor,old_mesh,record['oldLocationCm'],record['oldScale'],record['oldYaw']):raise RuntimeError('House changed after preflight; preserved: '+label)
                target=record['target'];mesh=meshes[target['model']]
                actor.static_mesh_component.set_static_mesh(mesh)
                actor.static_mesh_component.set_collision_profile_name('BlockAll')
                actor.set_actor_scale3d(unreal.Vector(*([target['scale']]*3)))
                actor.set_actor_rotation(unreal.Rotator(yaw=target['yaw']),False)
                actor.set_actor_location(unreal.Vector(*target['locationCm']),False,False)
                actor.tags=list(actor.tags)+[UPGRADE]
                if not unchanged(actor,mesh,target['locationCm'],[target['scale']]*3,target['yaw']):raise RuntimeError('New scanned-house transform did not apply')
                package=actor.get_outermost();name=package.get_name()
                if name!=PACKAGE and not name.startswith('/Game/__ExternalActors__/Maps/ANOMALIA_Inhabited_v2/'):
                    raise RuntimeError('Refusing to save an unrelated package: '+name)
                packages[name]=package
            if packages and not unreal.EditorLoadingAndSavingUtils.save_packages(list(packages.values()),False):raise RuntimeError('Scanned house packages did not save')
            report['replaced']+=sum(records[label]['status']=='replace' for label in loaded)
        finally:
            loaded.clear();actor=None;package=None;packages.clear()
            if not wp.set_archipelago_actors_loaded(unload,False):raise RuntimeError('Owned house unload refused')
        unreal.log('Residential exterior upgrade saved: '+str(report['replaced']))
    report.update(state='OWNED_RESIDENTIAL_EXTERIORS_SAVED_REQUIRES_GPU_REVIEW',upgradedTotal=stats['already']+report['replaced'],originalsRetained=4760-stats['already']-report['replaced'])
except Exception as error:
    report['error']=str(error);raise
finally:
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2)+'\n')
