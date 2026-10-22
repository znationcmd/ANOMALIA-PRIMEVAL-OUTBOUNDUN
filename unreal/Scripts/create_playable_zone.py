"""Assemble an owned small game map from existing imported art; never alter other maps."""
import json, os
from pathlib import Path
import unreal

PACKAGE='/Game/Maps/ANOMALIA_Playable_v1'
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
marker='ANOMALIA_Playable_v1_Owner'
if unreal.EditorAssetLibrary.does_asset_exist(PACKAGE):
    if not level.load_level(PACKAGE): raise RuntimeError('Cannot load playable map')
    if not any(a.get_actor_label()==marker for a in actors.get_all_level_actors()):
        raise RuntimeError('Unowned playable map preserved')
else:
    meshes={}
    for name,path in {
        'house':'/Game/Anomalia/Buildings/Lot1/SM_coastal_house_v1',
        'villa':'/Game/Anomalia/Buildings/Lot1/SM_beach_villa_pool_v1',
        'garage':'/Game/Anomalia/Buildings/Lot1/SM_garage_v1',
        'car':'/Game/Anomalia/Vehicles/car/SM_car',
        'suv':'/Game/Anomalia/Vehicles/suv/SM_suv',
        'transport_truck':'/Game/Anomalia/Vehicles/transport_truck/SM_transport_truck',
    }.items():
        meshes[name]=unreal.load_asset(path)
        if not isinstance(meshes[name],unreal.StaticMesh): raise RuntimeError('Existing required mesh unavailable: '+path)
    if not level.new_level(PACKAGE): raise RuntimeError('Cannot create isolated playable map')
    def spawn(cls,name,pos):
        a=actors.spawn_actor_from_class(cls,unreal.Vector(*pos));a.set_actor_label(name)
        a.tags=[unreal.Name(name),unreal.Name(marker)];return a
    spawn(unreal.Actor,marker,(0,0,0))
    def mesh(name,asset,pos,scale=(1,1,1)):
        a=spawn(unreal.StaticMeshActor,name,pos);a.static_mesh_component.set_static_mesh(asset)
        a.static_mesh_component.set_collision_profile_name('BlockAll');a.set_actor_scale3d(unreal.Vector(*scale));return a
    cube=unreal.load_asset('/Engine/BasicShapes/Cube')
    mesh('PlayableGround',cube,(0,0,-50),(200,200,1))
    mesh('PlayableRoad',cube,(0,-1500,1),(180,8,.02))
    mesh('PlayableHouse',meshes['house'],(0,1000,0))
    mesh('PlayableGarage',meshes['garage'],(2200,1000,0))
    mesh('PlayableVilla',meshes['villa'],(-3500,3000,0))
    # Provisional vegetation uses original basic shapes; realistic vegetation is still pending.
    for i in range(20):
        x=-7000+(i%10)*1400;y=6500 if i<10 else -6500
        mesh('PlayableTreeTrunk'+str(i),unreal.load_asset('/Engine/BasicShapes/Cylinder'),(x,y,200),(.35,.35,4))
        crown=mesh('PlayableTreeCrown'+str(i),unreal.load_asset('/Engine/BasicShapes/Cone'),(x,y,650),(3,3,7))
        crown.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    spawn(unreal.PlayerStart,'PlayableStart',(0,-400,110))
    light=spawn(unreal.DirectionalLight,'PlayableSun',(0,0,3000));light.set_actor_rotation(unreal.Rotator(pitch=-40,yaw=-35),False)
    spawn(unreal.SkyAtmosphere,'PlayableAtmosphere',(0,0,0))
    sky=spawn(unreal.SkyLight,'PlayableSky',(0,0,500));sky.light_component.set_editor_property('intensity',1.2)
    cls=unreal.load_class(None,'/Script/AnomaliaPrimeval.AnomaliaVehiclePawn')
    for i,name in enumerate(('car','suv','transport_truck')):
        a=spawn(cls,'PlayableVehicle_'+name,(1800+i*1500,-1500,160))
        if not a.configure_vehicle(unreal.Name(name)): raise RuntimeError('Cannot configure '+name)
    bed=spawn(unreal.load_class(None,'/Script/AnomaliaPrimeval.AnomaliaHomesteadStation'),'PlayableBed',(250,1000,50))
    bed.display_mesh.set_static_mesh(cube);bed.display_mesh.set_relative_scale3d(unreal.Vector(1,2,.4))
    if not level.save_current_level(): raise RuntimeError('Cannot save playable map')
unreal.log('ANOMALIA playable zone assembled; packaged execution and art quality still require validation.')
