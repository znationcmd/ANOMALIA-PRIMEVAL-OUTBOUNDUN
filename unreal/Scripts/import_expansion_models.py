"""Non-destructive import of original prototype families and a separate review level.
Runtime vehicles bind to existing authorized catalogue IDs. This is not a drive test.
"""
import hashlib
import json
import os
from pathlib import Path
import uuid
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
GROUP=os.environ.get('ANOMALIA_ASSET_GROUP','Expansion1')
if GROUP not in ['Expansion1','Metro1','NamedVehicles1','Military1','Military2']:raise RuntimeError('Unsupported import group')
BASE=ROOT/'SourceAssets'/GROUP
MAPS={'Expansion1':'Expansion','Metro1':'Metro','NamedVehicles1':'NamedVehicles','Military1':'Military','Military2':'MilitaryExtra'}
TAG='AnomaliaExpansionSHA' if GROUP=='Expansion1' else 'Anomalia'+GROUP+'SHA'
OUT=Path(os.environ['ANOMALIA_EXPANSION_REPORT'])
report=dict(state='FAILED',sourceCommit=os.environ.get('GITHUB_SHA','manual'),models=[],drivingTested=False,walkingTested=False,multiplayerTested=False)
try:
    spec=json.loads((BASE/'manifest.json').read_text())
    tools=unreal.AssetToolsHelpers.get_asset_tools();loaded={}
    for item in spec['models']:
        source=BASE/item['file'];dest=item['objectPath']
        if source.resolve().parent!=BASE or hashlib.sha256(source.read_bytes()).hexdigest()!=item['sha256']:
            raise RuntimeError('Source identity mismatch: '+item['id'])
        mesh=unreal.EditorAssetLibrary.load_asset(dest) if unreal.EditorAssetLibrary.does_asset_exist(dest) else None
        if mesh:
            if not isinstance(mesh,unreal.StaticMesh) or unreal.EditorAssetLibrary.get_metadata_tag(mesh,TAG)!=item['sha256']:
                raise RuntimeError('Unrelated existing mesh preserved: '+dest)
        else:
            staging='/Game/Anomalia/OriginalImports/'+GROUP+'_'+item['id']+'_'+uuid.uuid4().hex
            task=unreal.AssetImportTask();task.filename=str(source);task.destination_path=staging;task.automated=True;task.replace_existing=False;task.save=True;task.async_=False
            tools.import_asset_tasks([task]);task.get_objects()
            meshes=[unreal.EditorAssetLibrary.load_asset(p) for p in unreal.EditorAssetLibrary.list_assets(staging,recursive=True,include_folder=False)]
            meshes=[m for m in meshes if isinstance(m,unreal.StaticMesh)]
            if len(meshes)!=1:raise RuntimeError('Expected one assembled mesh: '+item['id'])
            mesh=unreal.EditorAssetLibrary.duplicate_asset(meshes[0].get_path_name(),dest)
            if not mesh:raise RuntimeError('Cannot save canonical mesh: '+dest)
            unreal.EditorAssetLibrary.set_metadata_tag(mesh,TAG,item['sha256'])
            body=mesh.get_editor_property('body_setup')
            if not body:raise RuntimeError('Missing BodySetup')
            body.set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
            if not unreal.EditorAssetLibrary.save_loaded_asset(mesh,only_if_is_dirty=False):raise RuntimeError('Mesh save failed')
        bounds=mesh.get_bounds();dims=[bounds.box_extent.x*2,bounds.box_extent.y*2,bounds.box_extent.z*2]
        expected=[item['dimensionsMetresYUp'][i]*100 for i in [0,2,1]]
        if any(abs(a-b)>3 for a,b in zip(dims,expected)):raise RuntimeError('Scale/axis mismatch: '+item['id']+' '+str(dims))
        materials=mesh.get_editor_property('static_materials')
        if not materials or any(not v.material_interface for v in materials):raise RuntimeError('Missing material: '+item['id'])
        loaded[item['id']]=mesh
        report['models'].append(dict(id=item['id'],kind=item['kind'],objectPath=mesh.get_path_name(),dimensionsCm=dims,materials=len(materials),nativePresentationBound=False))
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    vehicle=unreal.load_class(None,'/Script/AnomaliaPrimeval.AnomaliaVehiclePawn')
    for item in report['models']:
        if item['kind']!='vehicle':continue
        probe=actors.spawn_actor_from_class(vehicle,unreal.Vector(0,0,500),transient=True)
        try:
            if not probe.configure_vehicle(unreal.Name(item['id'])) or probe.get_editor_property('body').get_editor_property('static_mesh')!=loaded[item['id']]:
                raise RuntimeError('Native binding failed: '+item['id'])
            item['nativePresentationBound']=True
        finally:actors.destroy_actor(probe)
    level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    package='/Game/Maps/ANOMALIA_'+MAPS[GROUP]+'Review_v1'
    existing=unreal.EditorAssetLibrary.does_asset_exist(package)
    if existing:
        if not level.load_level(package):raise RuntimeError('Cannot open existing review map')
        if not any(a.get_actor_label()=='ANOMALIA_'+GROUP+'_OwnershipMarker' for a in actors.get_all_level_actors()):raise RuntimeError('Unowned review map preserved')
    else:
        if not level.new_level(package):raise RuntimeError('Cannot create separate review map')
        def place(name,cls,pos):
            a=actors.spawn_actor_from_class(cls,unreal.Vector(*pos));a.set_actor_label(name);a.tags=[unreal.Name('ANOMALIA_'+GROUP)];return a
        place('ANOMALIA_'+GROUP+'_OwnershipMarker',unreal.Actor,(0,0,0))
        floor=place('ANOMALIA_'+GROUP+'_Ground',unreal.StaticMeshActor,(0,0,-40))
        component=floor.get_component_by_class(unreal.StaticMeshComponent)
        component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'));floor.set_actor_scale3d(unreal.Vector(700,700,.4));component.set_collision_profile_name('BlockAll')
        # Large naval models have their own remote display berths. No overlap with roads/housing.
        positions={};ordinary=[m for m in spec['models'] if m['kind']!='building' and m['id'] not in ['carrier','warship','submarine']]
        for i,item in enumerate(ordinary):positions[item['id']]=((i%6)*2200-5500,(i//6)*2200-7000)
        if GROUP in ['NamedVehicles1','Military1','Military2']:
            # Independent review bays scale to source bounds, including large ships.
            gap=max(max(m['dimensionsMetresYUp'][0],m['dimensionsMetresYUp'][2]) for m in spec['models'])*100+2000
            positions={m['id']:((i%6)*gap,(i//6)*gap) for i,m in enumerate(spec['models'])}
        positions.update(carrier=(-14000,13000),warship=(0,13000),submarine=(10000,13000))
        buildings=[m for m in spec['models'] if m['kind']=='building']
        for i,item in enumerate(buildings):positions[item['id']]=((i%3)*3500-3500,(i//3)*3500+3500)
        for item in spec['models']:
            mesh=loaded[item['id']];bounds=mesh.get_bounds();x,y=positions[item['id']]
            # Place actual bottom on the ground rather than burying boat hulls or pool basins.
            z=-20-(bounds.origin.z-bounds.box_extent.z)
            a=place('ANOMALIA_'+GROUP+'_'+item['id'],unreal.StaticMeshActor,(x,y,z))
            c=a.get_component_by_class(unreal.StaticMeshComponent);c.set_static_mesh(mesh);c.set_collision_profile_name('BlockAll')
        light=place('ANOMALIA_'+GROUP+'_Sun',unreal.DirectionalLight,(0,0,3000));light.set_actor_rotation(unreal.Rotator(pitch=-50,yaw=-35,roll=0),False)
        place('ANOMALIA_'+GROUP+'_Sky',unreal.SkyAtmosphere,(0,0,0));place('ANOMALIA_'+GROUP+'_Ambient',unreal.SkyLight,(0,0,1500))
        place('ANOMALIA_'+GROUP+'_PlayerStart',unreal.PlayerStart,(0,-10000,120))
        if not level.save_current_level():raise RuntimeError('Cannot save review map')
    report.update(state=('IMPORTED_33_ORIGINAL_PROTOTYPES_NOT_PLAYTESTED' if GROUP=='Expansion1' else 'IMPORTED_MODELS_NOT_PLAYTESTED'),group=GROUP,reviewMap=package,existingReviewMapPreserved=existing)
except Exception as error:
    report['error']=str(error);raise
finally:
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2)+'\n');unreal.log(json.dumps(report))
