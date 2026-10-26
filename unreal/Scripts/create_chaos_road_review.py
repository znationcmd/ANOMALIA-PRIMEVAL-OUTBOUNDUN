"""Author an isolated physics proving ground using the real installed skeletal vehicle."""
import json,os,traceback
from pathlib import Path
import unreal
OUT=Path(os.environ['ANOMALIA_CHAOS_OUTPUT'])
SEDAN=os.environ.get('ANOMALIA_CHAOS_USE_SEDAN')=='1'
OWNER='ANOMALIA_SedanDriveReview_v1' if SEDAN else 'ANOMALIA_ChaosRoadReview_v2'
PACKAGE='/Game/Maps/'+OWNER
report=dict(state='FAILED',sourceCommit=os.environ.get('GITHUB_SHA'),productionMapModified=False)
try:
    source=json.loads((OUT/'template-source.json').read_text())
    mesh=unreal.load_asset(source['meshPackage']);animation=unreal.load_class(None,source['animationClass'])
    tire=unreal.load_asset(source['tirePackage']);body_art=unreal.load_asset(source['bodyPackage'])
    glass_art=unreal.load_asset(source['glassPackage']) if source.get('glassPackage') else None
    if not mesh or not animation or not tire or not body_art:raise RuntimeError('Real template rig, animation or tires missing')
    sedan=None;sedan_parts={}
    if SEDAN:
        sedan=json.loads((Path(unreal.Paths.project_dir()).resolve()/'SourceAssets/NativeDemoSedan_v3/manifest.json').read_text())
        for part in sedan['models']:
            asset=unreal.load_asset(part['objectPath'])
            if not isinstance(asset,unreal.StaticMesh) or unreal.EditorAssetLibrary.get_metadata_tag(asset,'AnomaliaNativeSedanSha256')!=part['sha256']:
                raise RuntimeError('Source-verified native sedan part required: '+part['id'])
            sedan_parts[part['id']]=asset
        body_art=sedan_parts['body'];tire=sedan_parts['wheel_fl'];glass_art=None
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(PACKAGE):
        if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(PACKAGE):raise RuntimeError('Cannot reopen owned review')
        existing=actors.get_all_level_actors()
        if not any(OWNER in [str(t) for t in a.tags] for a in existing):raise RuntimeError('Unowned review map preserved')
        # Retain every existing actor. Same identities below are updated in place.
    else:unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    def spawn(cls,location):
        label=OWNER+'_'+cls.static_class().get_name()
        for a in actors.get_all_level_actors():
            if a.get_actor_label()==label:
                if unreal.Name(OWNER) not in a.tags or a.get_class()!=cls.static_class():raise RuntimeError('Artist review actor preserved: '+label)
                a.set_actor_location(unreal.Vector(*location),False,False)
                a.set_actor_rotation(unreal.Rotator(),False);return a
        a=actors.spawn_actor_from_class(cls,unreal.Vector(*location))
        a.set_actor_label(label);a.tags=[unreal.Name(OWNER)];return a
    car=spawn(unreal.AnomaliaChaosRoadVehicle,(0,0,100))
    # This licensed template is a physics fixture, not the requested final sedan.
    car.set_editor_property('road_mesh',mesh);car.set_editor_property('road_animation',animation)
    car.set_editor_property('road_body_mesh',body_art);car.set_editor_property('road_wheel_mesh',tire)
    car.set_editor_property('road_glass_mesh',glass_art)
    if SEDAN:
        car.set_editor_property('driver_door_mesh',sedan_parts['door_driver'])
        car.set_editor_property('driver_door_pivot_cm',unreal.Vector(*sedan['panels'][0]['pivotCm']))
        car.get_editor_property('driver_door').set_editor_property('open_angle_degrees',sedan['panels'][0]['openAngleDegrees'])
        car.set_editor_property('road_wheel_meshes',[sedan_parts[k] for k in ('wheel_fl','wheel_fr','wheel_rl','wheel_rr')])
        car.set_editor_property('road_wheel_hub_targets_cm',[unreal.Vector(*hub) for hub in sedan['wheelHubsCm']])
    chassis=car.get_editor_property('chassis');chassis.set_skeletal_mesh(mesh)
    bones=[]
    for i in range(chassis.get_num_bones()):
        name=chassis.get_bone_name(i)
        t=chassis.get_bone_transform(name,unreal.RelativeTransformSpace.RTS_COMPONENT)
        pos=t.translation
        bones.append(dict(name=str(name),positionCm=[pos.x,pos.y,pos.z]))
    report['bones']=bones
    physics=mesh.get_editor_property('physics_asset')
    report['physicsBodies']=[]
    try:physics_bodies=physics.get_editor_property('skeletal_body_setups')
    except Exception as error:
        physics_bodies=[];report['physicsBodyReadError']=str(error)
    for body in physics_bodies:
        info=dict(bone=str(body.get_editor_property('bone_name')))
        for prop in ('physics_type','collision_reponse','default_instance'):
            try:info[prop]=str(body.get_editor_property(prop))
            except Exception:pass
        try:
            geometry=body.get_editor_property('agg_geom')
            info['boxes']=[dict(center=str(b.center),size=[b.x,b.y,b.z]) for b in geometry.box_elems]
            info['spheres']=[dict(center=str(b.center),radius=b.radius) for b in geometry.sphere_elems]
        except Exception as error:info['geometryReadError']=str(error)
        report['physicsBodies'].append(info)
    # Inspect the installed vendor Blueprint configuration; never alter it.
    report['referenceTemplate']=source.get('referenceTemplate','OffroadCar')
    report['templateBlueprints']=[]
    for path in unreal.EditorAssetLibrary.list_assets('/Game/Vehicles/'+source.get('referenceTemplate','OffroadCar'),recursive=True,include_folder=False):
        blueprint=unreal.load_asset(path)
        if not isinstance(blueprint,unreal.Blueprint):continue
        generated=unreal.EditorAssetLibrary.load_blueprint_class(path)
        if not generated:continue
        cdo=unreal.get_default_object(generated)
        try:components=cdo.get_components_by_class(unreal.ChaosWheeledVehicleMovementComponent)
        except Exception:continue
        for movement in components:
            config=dict(path=path,wheels=[])
            for setup in movement.get_editor_property('wheel_setups'):
                wc=unreal.get_default_object(setup.wheel_class)
                wheel=dict(bone=str(setup.bone_name),offset=str(setup.additional_offset))
                for prop in ('wheel_radius','wheel_width','suspension_max_raise','suspension_max_drop','spring_rate','spring_preload','suspension_axis','sweep_shape','sweep_type'):
                    try:wheel[prop]=str(wc.get_editor_property(prop))
                    except Exception:pass
                config['wheels'].append(wheel)
            report['templateBlueprints'].append(config)

    # Native inspection confirms separate physical and visual wheel hierarchies.
    # Chaos must drive PhysWheel; the template Control Rig animates VisWheel.
    physics_bones={'PhysWheel_FL','PhysWheel_FR','PhysWheel_BL','PhysWheel_BR'}
    candidates=[b for b in bones if b['name'] in physics_bones]
    if len(candidates)!=4:
        import re
        candidates=[b for b in bones if re.fullmatch(r'wheel[_-]?(FL|FR|RL|RR|BL|BR)',b['name'],re.IGNORECASE)]
    if len(candidates)!=4:
        candidates=[b for b in bones if re.fullmatch(r'Phys_?Wheel[_-]?(FL|FR|RL|RR|BL|BR)',b['name'],re.IGNORECASE)]
    if len(candidates)!=4:raise RuntimeError('Four unambiguous wheel bones required; see recorded actual skeleton')
    by_x=sorted(candidates,key=lambda b:b['positionCm'][0],reverse=True)
    front=sorted(by_x[:2],key=lambda b:b['positionCm'][1]);rear=sorted(by_x[2:],key=lambda b:b['positionCm'][1])
    if min(x['positionCm'][0] for x in front)-max(x['positionCm'][0] for x in rear)<100:raise RuntimeError('Wheel axles are not longitudinally separated')
    selected=front+rear
    bounds=tire.get_bounds();radius=max(bounds.box_extent.x,bounds.box_extent.y,bounds.box_extent.z)
    if radius<10 or radius>100:raise RuntimeError('Measured real tire radius is outside supported road bounds')
    car.set_editor_property('wheel_bones',[unreal.Name(b['name']) for b in selected])
    car.set_editor_property('wheel_radius_cm',radius)
    if not car.has_valid_road_rig():raise RuntimeError('Native skeletal/animation/Physics Asset contract rejected the installed rig')
    # A plain proving surface is a test fixture, never a substitute for production scenery.
    ground=spawn(unreal.StaticMeshActor,(0,0,-50))
    ground.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
    # The extended repeated driving/exit sequence needs a longer proving surface.
    # This remains a plain engineering fixture, not the production 1 km2 zone.
    ground.set_actor_scale3d(unreal.Vector(2000,2000,1))
    ground.static_mesh_component.set_collision_profile_name('BlockAll')
    spawn(unreal.PlayerStart,(0,-350,200))
    spawn(unreal.AnomaliaChaosRoadProbe,(0,0,300))
    sun=spawn(unreal.DirectionalLight,(0,0,1000));sun.set_actor_rotation(unreal.Rotator(pitch=-40,yaw=-30),False)
    spawn(unreal.SkyLight,(0,0,1000));spawn(unreal.SkyAtmosphere,(0,0,0))
    if not unreal.EditorLoadingAndSavingUtils.save_map(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(),PACKAGE):raise RuntimeError('Review map save failed')
    report.update(state='REAL_SKELETAL_CHAOS_REVIEW_MAP_SAVED_NOT_DRIVEN',map=PACKAGE,
        mesh=mesh.get_path_name(),animationClass=animation.get_path_name(),wheelBones=selected,wheelRadiusCm=radius,
        gameplayTested=False,productionPlacementAllowed=False)
    report['originalSedanArt']=SEDAN
    if SEDAN:
        report['sedanSource']=sedan['source'];report['sedanWheelHubsCm']=sedan['wheelHubsCm']
        report['openingDoorsTested']=False;report['entryAnimationTested']=False
except Exception as e:
    report['error']=str(e);unreal.log_error(traceback.format_exc())
finally:(OUT/'rig-import-report.json').write_text(json.dumps(report,indent=2)+'\n')
