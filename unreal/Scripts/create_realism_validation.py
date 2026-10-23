"""Import pinned PBR art and build a separate review map. No existing map or save is changed."""
import hashlib,json,math,os,uuid
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
BASE=ROOT/'SourceAssets/RealismValidation_v2'
PACKAGE='/Game/Maps/ANOMALIA_VisualValidation_v1'
OWNER='ANOMALIA_VisualValidation_v1_Owner'
OUTPUT=Path(os.environ['ANOMALIA_REALISM_SCENE_REPORT'])
report=dict(state='FAILED',sourceCommit=os.environ.get('GITHUB_SHA'),map=PACKAGE,models=[])
try:
    manifest=json.loads((BASE/'manifest.json').read_text())
    tools=unreal.AssetToolsHelpers.get_asset_tools();meshes={}
    mesh_editor=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    if not mesh_editor:raise RuntimeError('Full Editor StaticMeshEditorSubsystem required; commandlets cannot generate these LODs')
    for item in manifest['models']:
        # Preserve the first commandlet attempt's unsaved/partial canonical asset.
        source=BASE/item['file'];destination=item['objectPath']+'_r2'
        if not source.resolve().is_relative_to(BASE) or hashlib.sha256(source.read_bytes()).hexdigest()!=item['sha256']:raise RuntimeError('Prepared art integrity failed')
        if unreal.EditorAssetLibrary.does_asset_exist(destination):
            mesh=unreal.load_asset(destination)
            if not isinstance(mesh,unreal.StaticMesh) or unreal.EditorAssetLibrary.get_metadata_tag(mesh,'AnomaliaRealismSha256')!=item['sha256']:raise RuntimeError('Existing artist asset preserved: '+destination)
        else:
            task=unreal.AssetImportTask();task.filename=str(source);task.destination_path='/Game/Anomalia/VisualValidation_v1/Imports_r2/'+item['id']
            task.automated=True;task.replace_existing=False;task.save=True;task.async_=False
            tools.import_asset_tasks([task]);task.get_objects()
            imported=[unreal.load_asset(p)for p in unreal.EditorAssetLibrary.list_assets(task.destination_path,recursive=True,include_folder=False)]
            candidates=[a for a in imported if isinstance(a,unreal.StaticMesh)]
            if len(candidates)!=1:raise RuntimeError('Expected one baked mesh: '+item['id']+' '+str(len(candidates)))
            mesh=unreal.EditorAssetLibrary.duplicate_asset(candidates[0].get_path_name(),destination)
            if not mesh:raise RuntimeError('Cannot create canonical review mesh')
            unreal.EditorAssetLibrary.set_metadata_tag(mesh,'AnomaliaRealismSha256',item['sha256'])
            unreal.EditorAssetLibrary.set_metadata_tag(mesh,'AnomaliaAttribution',item['author']+' / '+item['license']+' / '+item['source'])
            if item['triangles']>20000 and item['id'] not in ('forest_ground_04','detached_house'):
                options=unreal.StaticMeshReductionOptions()
                options.auto_compute_lod_screen_size=False
                options.reduction_settings=[unreal.StaticMeshReductionSettings(percent_triangles=p,screen_size=s)
                    for p,s in [(1.,1.),(.35,.5),(.12,.25),(.04,.1)]]
                mesh_editor.set_lods(mesh,options)
                if mesh_editor.get_lod_count(mesh)<4:raise RuntimeError('Distance LOD generation failed')
            if item['id'] in ('detached_house','forest_ground_04','asphalt_02'):
                body=mesh.get_editor_property('body_setup')
                if not body:raise RuntimeError('Missing structural collision body')
                body.set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
            if not unreal.EditorAssetLibrary.save_loaded_asset(mesh,only_if_is_dirty=False):raise RuntimeError('Review mesh did not save')
        materials=mesh.get_editor_property('static_materials')
        if not materials or any(not x.material_interface for x in materials):raise RuntimeError('Missing PBR materials: '+item['id'])
        meshes[item['id']]=mesh
        bounds=mesh.get_bounds();dims=[bounds.box_extent.x*2,bounds.box_extent.y*2,bounds.box_extent.z*2]
        report['models'].append(dict(id=item['id'],objectPath=mesh.get_path_name(),materials=len(materials),dimensionsCm=dims,triangles=item['triangles'],license=item['license'],lodCount=mesh_editor.get_lod_count(mesh)))
    level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(PACKAGE):
        if not level.load_level(PACKAGE):raise RuntimeError('Cannot load existing review map')
        if not any(a.get_actor_label()==OWNER for a in actors.get_all_level_actors()):raise RuntimeError('Unowned review map preserved')
    else:
        if not level.new_level(PACKAGE):raise RuntimeError('Cannot create isolated review map')
    def spawn(cls,name,pos):
        for existing in actors.get_all_level_actors():
            if existing.get_actor_label()==name:
                if unreal.Name(OWNER)not in existing.tags or not isinstance(existing,cls):raise RuntimeError('Unowned or mismatched review actor preserved: '+name)
                return existing
        a=actors.spawn_actor_from_class(cls,unreal.Vector(*pos));a.set_actor_label(name);a.tags=[unreal.Name(OWNER),unreal.Name(name)];return a
    spawn(unreal.Actor,OWNER,(0,0,0))
    if not level.save_current_level():raise RuntimeError('Cannot persist review map ownership before assembly')
    def mesh(name,ident,pos,collide=False,scale=1.,yaw=0.):
        a=spawn(unreal.StaticMeshActor,name,pos);c=a.static_mesh_component;c.set_static_mesh(meshes[ident])
        c.set_collision_profile_name('BlockAll' if collide else 'NoCollision')
        a.set_actor_scale3d(unreal.Vector(scale,scale,scale));a.set_actor_rotation(unreal.Rotator(yaw=yaw),False);return a
    mesh('ReviewTerrain','forest_ground_04',(0,0,0),True)
    mesh('ReviewRoad','asphalt_02',(0,-1500,4),True)
    mesh('ReviewHouse','detached_house',(0,1200,0),True,yaw=90)
    for i in range(18):
        side=-1 if i%2 else 1;x=-7200+(i//2)*1700;y=side*(4200+(i%3)*450)
        # No engine sphere/cone vegetation. Real branches, bark, masked leaves.
        mesh('ReviewTree_'+str(i),'island_tree_02',(x,y,-15),scale=.9+(i%4)*.13,yaw=i*137.5)
    for i in range(24):
        x=-7000+(i%8)*1900;y=3300+(i//8)*700
        mesh('ReviewGrass_'+str(i),'grass_medium_01',(x,y,2),scale=1.1,yaw=i*37)
    for i,pos in enumerate([(-4000,3000,0),(4500,4500,0),(-5500,-4200,0)]):mesh('ReviewRock_'+str(i),'rock_moss_set_01',pos,yaw=i*73)
    cls=unreal.load_class(None,'/Script/AnomaliaPrimeval.AnomaliaVehiclePawn')
    car=spawn(cls,'ReviewDriveableCar',(1600,-1500,160));car.set_editor_property('presentation_mesh_override',meshes['concept_car'])
    if not car.configure_vehicle(unreal.Name('car')) or car.body.get_editor_property('static_mesh')!=meshes['concept_car']:raise RuntimeError('Detailed car not bound to real vehicle systems')
    truck=spawn(cls,'ReviewDriveableTruck',(-1800,-1500,160));truck.set_editor_property('presentation_mesh_override',meshes['box_truck'])
    if not truck.configure_vehicle(unreal.Name('transport_truck')) or truck.body.get_editor_property('static_mesh')!=meshes['box_truck']:raise RuntimeError('Detailed truck not bound to real vehicle systems')
    spawn(unreal.PlayerStart,'ReviewStart',(0,-600,120))
    sun=spawn(unreal.DirectionalLight,'ReviewSun',(0,0,3000));sun.set_actor_rotation(unreal.Rotator(pitch=-28,yaw=-45),False)
    sun.light_component.set_mobility(unreal.ComponentMobility.MOVABLE);sun.light_component.set_editor_property('intensity',3.)
    sun.light_component.set_editor_property('atmosphere_sun_light',True)
    sun.light_component.set_editor_property('light_source_angle',1.)
    spawn(unreal.SkyAtmosphere,'ReviewAtmosphere',(0,0,0))
    sky=spawn(unreal.SkyLight,'ReviewSky',(0,0,500));sky.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    sky.light_component.set_editor_property('real_time_capture',True);sky.light_component.set_editor_property('intensity',.8)
    for i,pos in enumerate([(0,400,260),(-2800,-1800,450),(2800,-1800,450)]):
        lamp=spawn(unreal.PointLight,'ReviewNightLamp_'+str(i),pos)
        lamp.tags=[unreal.Name(OWNER),unreal.Name('ReviewNightLight')]
        lamp.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
        lamp.light_component.set_editor_property('intensity',1600.)
        lamp.light_component.set_editor_property('attenuation_radius',1800.)
        lamp.light_component.set_visibility(False)
    fog=spawn(unreal.ExponentialHeightFog,'ReviewFog',(0,0,-300))
    post=spawn(unreal.PostProcessVolume,'ReviewExposure',(0,0,0));post.set_editor_property('unbound',True)
    settings=post.get_editor_property('settings')
    settings.set_editor_property('override_auto_exposure_min_brightness',True);settings.set_editor_property('auto_exposure_min_brightness',.8)
    settings.set_editor_property('override_auto_exposure_max_brightness',True);settings.set_editor_property('auto_exposure_max_brightness',1.2)
    settings.set_editor_property('override_auto_exposure_bias',True);settings.set_editor_property('auto_exposure_bias',0.)
    post.set_editor_property('settings',settings)
    shots=[('ReviewCamera_Overview',(-2600,-3700,1100),(0,1000,200)),('ReviewCamera_Car',(2050,-2050,240),(1600,-1500,70)),('ReviewCamera_House',(-1800,-600,380),(0,1200,350)),('ReviewCamera_Truck',(-2600,-2300,400),(-1800,-1500,160))]
    for name,pos,target in shots:
        cam=spawn(unreal.CameraActor,name,pos);cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*pos),unreal.Vector(*target)),False)
        cam.camera_component.set_editor_property('field_of_view',65.)
    if not level.save_current_level():raise RuntimeError('Review map did not save')
    report['state']='REALISM_VALIDATION_MAP_SAVED_NOT_PLAYTESTED'
    report['ownedActorCount']=sum(unreal.Name(OWNER)in a.tags for a in actors.get_all_level_actors())
except Exception as error:
    report['error']=str(error);raise
finally:
    OUTPUT.parent.mkdir(parents=True,exist_ok=True);OUTPUT.write_text(json.dumps(report,indent=2)+'\n')
