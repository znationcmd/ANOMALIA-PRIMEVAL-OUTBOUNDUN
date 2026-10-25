"""Author an isolated physics proving ground using the real installed skeletal vehicle."""
import json,os,traceback
from pathlib import Path
import unreal
OUT=Path(os.environ['ANOMALIA_CHAOS_OUTPUT'])
PACKAGE='/Game/Maps/ANOMALIA_ChaosRoadReview_v1'
OWNER='ANOMALIA_ChaosRoadReview_v1'
report=dict(state='FAILED',sourceCommit=os.environ.get('GITHUB_SHA'),productionMapModified=False)
try:
    source=json.loads((OUT/'template-source.json').read_text())
    mesh=unreal.load_asset(source['meshPackage']);animation=unreal.load_class(None,source['animationClass'])
    tire=unreal.load_asset(source['tirePackage'])
    if not mesh or not animation or not tire:raise RuntimeError('Real template rig, animation or tires missing')
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(PACKAGE):
        if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(PACKAGE):raise RuntimeError('Cannot reopen owned review')
        existing=actors.get_all_level_actors()
        if not any(OWNER in [str(t) for t in a.tags] for a in existing):raise RuntimeError('Unowned review map preserved')
        for a in existing:actors.destroy_actor(a)
    else:unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    def spawn(cls,location):
        a=actors.spawn_actor_from_class(cls,unreal.Vector(*location))
        a.tags=[unreal.Name(OWNER)];return a
    car=spawn(unreal.AnomaliaChaosRoadVehicle,(0,0,100))
    car.set_actor_label('Actual_Chaos_Offroad_Review')
    car.set_editor_property('road_mesh',mesh);car.set_editor_property('road_animation',animation)
    chassis=car.get_editor_property('chassis');chassis.set_skeletal_mesh(mesh)
    bones=[]
    for i in range(chassis.get_num_bones()):
        name=chassis.get_bone_name(i)
        t=chassis.get_bone_transform(name,unreal.RelativeTransformSpace.RTS_COMPONENT)
        pos=t.translation
        bones.append(dict(name=str(name),positionCm=[pos.x,pos.y,pos.z]))
    report['bones']=bones
    candidates=[b for b in bones if 'wheel' in b['name'].lower() and not any(x in b['name'].lower() for x in ('susp','brake','steer','hub'))]
    if len(candidates)!=4:raise RuntimeError('Four unambiguous wheel bones required; see recorded actual skeleton')
    by_x=sorted(candidates,key=lambda b:b['positionCm'][0],reverse=True)
    front=sorted(by_x[:2],key=lambda b:b['positionCm'][1]);rear=sorted(by_x[2:],key=lambda b:b['positionCm'][1])
    if min(x['positionCm'][0] for x in front)-max(x['positionCm'][0] for x in rear)<100:raise RuntimeError('Wheel axles are not longitudinally separated')
    selected=front+rear
    bounds=tire.get_bounds();radius=max(bounds.box_extent.x,bounds.box_extent.z)
    if radius<10 or radius>100:raise RuntimeError('Measured real tire radius is outside supported road bounds')
    car.set_editor_property('wheel_bones',[unreal.Name(b['name']) for b in selected])
    car.set_editor_property('wheel_radius_cm',radius)
    if not car.has_valid_road_rig():raise RuntimeError('Native skeletal/animation/Physics Asset contract rejected the installed rig')
    # A plain proving surface is a test fixture, never a substitute for production scenery.
    ground=spawn(unreal.StaticMeshActor,(0,0,-50))
    ground.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
    ground.set_actor_scale3d(unreal.Vector(500,500,1))
    ground.static_mesh_component.set_collision_profile_name('BlockAll')
    spawn(unreal.PlayerStart,(0,-350,200))
    spawn(unreal.AnomaliaChaosRoadProbe,(0,0,300))
    sun=spawn(unreal.DirectionalLight,(0,0,1000));sun.set_actor_rotation(unreal.Rotator(pitch=-40,yaw=-30),False)
    spawn(unreal.SkyLight,(0,0,1000));spawn(unreal.SkyAtmosphere,(0,0,0))
    if not unreal.EditorLoadingAndSavingUtils.save_map(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(),PACKAGE):raise RuntimeError('Review map save failed')
    report.update(state='REAL_SKELETAL_CHAOS_REVIEW_MAP_SAVED_NOT_DRIVEN',map=PACKAGE,
        mesh=mesh.get_path_name(),animationClass=animation.get_path_name(),wheelBones=selected,wheelRadiusCm=radius,
        gameplayTested=False,productionPlacementAllowed=False)
except Exception as e:
    report['error']=str(e);unreal.log_error(traceback.format_exc())
finally:(OUT/'rig-import-report.json').write_text(json.dumps(report,indent=2)+'\n')
