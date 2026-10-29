"""Append an original segmented viaduct to the already validated world. Never replace existing actors."""
import hashlib,json,math,os,uuid
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve();BASE=ROOT/'SourceAssets/Infrastructure/Bridge'
REPORT=Path(os.environ.get('ANOMALIA_BRIDGE_REPORT',str(ROOT/'Saved/BuildValidation'/('bridge-'+uuid.uuid4().hex+'.json'))))
MARKER=ROOT/'Saved/AnomaliaZPrigimaliaMigration/detroit-bridge-v1.json'
TAG='ANOMALIA_DetroitBridge_v1';PACKAGE='/Game/Maps/ANOMALIA_Archipelago_v2'
result=dict(state='FAILED',sourceCommit=os.environ.get('GITHUB_SHA','manual'),mapPackage=PACKAGE,renderingValidated=False,walkTested=False,vehicleDriveTested=False)
try:
    spec=json.loads((BASE/'manifest.json').read_text());source=BASE/'bridge50m.glb'
    if hashlib.sha256(source.read_bytes()).hexdigest()!=spec['sha256']:raise RuntimeError('Bridge source checksum mismatch')
    if MARKER.exists():
        prior=json.loads(MARKER.read_text())
        if prior.get('sourceSha256')!=spec['sha256'] or prior.get('state')!='PLACED_NOT_PLAYTESTED':raise RuntimeError('Existing placement marker differs; not replaced')
        result.update(prior);result['state']='EXISTING_PLACEMENTS_PRESERVED';result['sourceCommit']=os.environ.get('GITHUB_SHA','manual')
    else:
        destination='/Game/Anomalia/Infrastructure/Bridge/SM_Bridge50m'
        asset=unreal.EditorAssetLibrary.load_asset(destination) if unreal.EditorAssetLibrary.does_asset_exist(destination) else None
        if asset:
            if not isinstance(asset,unreal.StaticMesh) or unreal.EditorAssetLibrary.get_metadata_tag(asset,'AnomaliaZPrigimaliaBridgeSourceSHA256')!=spec['sha256']:raise RuntimeError('Unowned bridge asset preserved')
        else:
            tools=unreal.AssetToolsHelpers.get_asset_tools();staging='/Game/Anomalia/Infrastructure/Bridge/Imports/Span_'+uuid.uuid4().hex
            task=unreal.AssetImportTask();task.filename=str(source);task.destination_path=staging;task.automated=True;task.replace_existing=False;task.save=True;task.async_=False
            tools.import_asset_tasks([task]);task.get_objects()
            meshes=[unreal.EditorAssetLibrary.load_asset(p) for p in unreal.EditorAssetLibrary.list_assets(staging,recursive=True,include_folder=False)]
            meshes=[m for m in meshes if isinstance(m,unreal.StaticMesh)]
            if len(meshes)!=1:raise RuntimeError('Expected one complete bridge mesh')
            asset=unreal.EditorAssetLibrary.duplicate_asset(meshes[0].get_path_name(),destination)
            if not asset:raise RuntimeError('Bridge asset duplication failed')
            unreal.EditorAssetLibrary.set_metadata_tag(asset,'AnomaliaZPrigimaliaBridgeSourceSHA256',spec['sha256'])
        bounds=asset.get_bounds()
        if abs(bounds.box_extent.x*2-5011)>2 or abs(bounds.box_extent.y*2-1100)>2:raise RuntimeError('Bridge scale/axis mismatch')
        body=asset.get_editor_property('body_setup')
        if not body:raise RuntimeError('Bridge mesh lacks physics BodySetup')
        body.set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        if not unreal.EditorAssetLibrary.save_loaded_asset(asset,only_if_is_dirty=False):raise RuntimeError('Bridge physics asset save failed')
        level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        if not level.load_level(PACKAGE):raise RuntimeError('Validated archipelago map could not be loaded')
        actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        if any(unreal.Name(TAG) in a.tags for a in actors.get_all_level_actors()):raise RuntimeError('Existing tagged bridge actors found; no duplicate placement')
        x0,x1,north=13500.,16000.,-9000.
        h0=unreal.AnomaliaZPrigimaliaWorldImportLibrary.archipelago_height(x0,north)+.25
        h1=unreal.AnomaliaZPrigimaliaWorldImportLibrary.archipelago_height(x1,north)+.25
        def height(x):return h0+(h1-h0)*(x-x0)/(x1-x0)
        pitch=math.degrees(math.atan2(h1-h0,x1-x0))
        labels=[];pier_count=0
        def place(name,mesh,position,rotation=None,scale=None):
            actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,position,rotation or unreal.Rotator())
            if not actor:raise RuntimeError('Could not place '+name)
            actor.set_actor_label(name);actor.tags=[unreal.Name(TAG)]
            comp=actor.get_component_by_class(unreal.StaticMeshComponent);comp.set_static_mesh(mesh);comp.set_collision_profile_name('BlockAll')
            if scale:actor.set_actor_scale3d(scale)
            labels.append(name);return actor
        for i in range(50):
            x=x0+(i+.5)*50
            place('ANOMALIA_DetroitBridge_Span_%02d'%i,asset,unreal.Vector(x*100,-north*100,height(x)*100),unreal.Rotator(pitch,0,0),scale=unreal.Vector(1/math.cos(math.radians(pitch)),1,1))
        cylinder=unreal.load_asset('/Engine/BasicShapes/Cylinder')
        concrete=next((m.material_interface for m in asset.get_editor_property('static_materials') if 'concrete' in str(m.material_slot_name).lower()),None)
        for i in range(51):
            x=x0+i*50;bottom=unreal.AnomaliaZPrigimaliaWorldImportLibrary.archipelago_height(x,north)-3;top=height(x)-2.05;length=top-bottom
            if length<1:continue
            for side in [-1,1]:
                a=place('ANOMALIA_DetroitBridge_Pier_%02d_%s'%(i,'L' if side<0 else 'R'),cylinder,unreal.Vector(x*100,-north*100+side*270,(top+bottom)*50),scale=unreal.Vector(3.5,3.5,length))
                if concrete:a.get_component_by_class(unreal.StaticMeshComponent).set_material(0,concrete)
                pier_count+=1
        if not level.save_all_dirty_levels() or not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):raise RuntimeError('Bridge world packages could not be saved')
        result.update(state='PLACED_NOT_PLAYTESTED',sourceSha256=spec['sha256'],spanCount=50,pierCount=pier_count,lengthMeters=2500,widthMeters=11,deckEndpointHeightsMeters=[h0,h1],objectPath=asset.get_path_name(),placementLabels=labels)
        MARKER.parent.mkdir(parents=True,exist_ok=True);MARKER.write_text(json.dumps(result,indent=2)+'\n')
except Exception as exc:
    result['error']=str(exc);raise
finally:
    REPORT.parent.mkdir(parents=True,exist_ok=True);REPORT.write_text(json.dumps(result,indent=2)+'\n');unreal.log('ANOMALIA_BRIDGE_REPORT='+str(REPORT))
