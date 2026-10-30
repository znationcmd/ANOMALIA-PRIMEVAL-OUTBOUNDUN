"""Assemble an owned small game map from existing imported art; never alter other maps."""
import json, os, math
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
    cls=unreal.load_class(None,'/Script/AnomaliaZPrigimalia.AnomaliaZPrigimaliaVehiclePawn')
    for i,name in enumerate(('car','suv','transport_truck')):
        a=spawn(cls,'PlayableVehicle_'+name,(1800+i*1500,-1500,160))
        if not a.configure_vehicle(unreal.Name(name)): raise RuntimeError('Cannot configure '+name)
    bed=spawn(unreal.load_class(None,'/Script/AnomaliaZPrigimalia.AnomaliaZPrigimaliaHomesteadStation'),'PlayableBed',(250,1000,50))
    bed.display_mesh.set_static_mesh(cube);bed.display_mesh.set_relative_scale3d(unreal.Vector(1,2,.4))
    if not level.save_current_level(): raise RuntimeError('Cannot save playable map')
# Upgrade only our isolated map. Never recreate it: keep gameplay actors, IDs and saves.
owned={a.get_actor_label():a for a in actors.get_all_level_actors() if unreal.Name(marker) in a.tags}
def surface(name,dark,light,roughness,grain):
    folder='/Game/Anomalia/World/PlayableLook_v2'
    name+='_PBR'
    path=folder+'/'+name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        value=unreal.load_asset(path)
        if not isinstance(value,unreal.Material) or unreal.EditorAssetLibrary.get_metadata_tag(value,'AnomaliaZPrigimaliaPlayableSurfaceState')!='SAVED_NOISE_PBR_1':
            raise RuntimeError('Existing unrecognized material preserved: '+path)
        return value  # Preserve any subsequent artist edits.
    value=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,folder,unreal.Material,unreal.MaterialFactoryNew())
    lib=unreal.MaterialEditingLibrary
    def node(cls,**props):
        n=lib.create_material_expression(value,cls)
        for key,item in props.items(): n.set_editor_property(key,item)
        return n
    def link(source,target,pin):
        if not lib.connect_material_expressions(source,'',target,pin):
            raise RuntimeError('Material graph connection failed at '+str(pin)+'; inputs='+str(lib.get_material_expression_input_names(target)))
    pos=node(unreal.MaterialExpressionWorldPosition)
    noise=node(unreal.MaterialExpressionNoise,scale=grain,levels=2,quality=1,output_min=0.,output_max=1.)
    position_pins=[pin for pin in lib.get_material_expression_input_names(noise) if 'position' in pin.lower().replace(' ','')]
    if len(position_pins)!=1: raise RuntimeError('Cannot identify Noise world-position input')
    link(pos,noise,position_pins[0])
    low=node(unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(*dark,1))
    high=node(unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(*light,1))
    mix=node(unreal.MaterialExpressionLinearInterpolate)
    link(low,mix,'A');link(high,mix,'B');link(noise,mix,'Alpha')
    r=node(unreal.MaterialExpressionConstant,r=roughness)
    if not lib.connect_material_property(mix,'',unreal.MaterialProperty.MP_BASE_COLOR): raise RuntimeError('Base colour connection failed')
    if not lib.connect_material_property(r,'',unreal.MaterialProperty.MP_ROUGHNESS): raise RuntimeError('Roughness connection failed')
    lib.recompile_material(value)
    unreal.EditorAssetLibrary.set_metadata_tag(value,'AnomaliaZPrigimaliaPlayableSurfaceState','SAVED_NOISE_PBR_1')
    if not unreal.EditorAssetLibrary.save_loaded_asset(value): raise RuntimeError('Cannot save original material')
    return value

palette={
    'grass':surface('M_Meadow',(.045,.072,.018),(.16,.24,.065),.95,.018),
    'road':surface('M_Asphalt',(.018,.022,.026),(.055,.061,.065),.88,.18),
    'bark':surface('M_Bark',(.055,.026,.012),(.16,.085,.035),.95,.035),
    'leaf':surface('M_Leaf',(.015,.055,.012),(.07,.18,.028),.9,.015),
    'stone':surface('M_Stone',(.12,.13,.115),(.27,.29,.25),.94,.025),
    'walk':surface('M_Pavement',(.25,.24,.21),(.4,.39,.34),.9,.05),
    'paint':surface('M_RoadPaint',(.65,.64,.53),(.78,.77,.66),.82,.12),
}
for name,key in [('PlayableGround','grass'),('PlayableRoad','road')]:
    if name not in owned: raise RuntimeError('Owned base actor missing: '+name)
    owned[name].static_mesh_component.set_material(0,palette[key])

def decor(name,asset,pos,scale,material):
    a=owned.get(name)
    if a is None:
        # Refuse to claim a same-label actor without our ownership tag.
        if any(x.get_actor_label()==name for x in actors.get_all_level_actors()): raise RuntimeError('Unowned decoration preserved: '+name)
        a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*pos))
        a.set_actor_label(name);a.tags=[unreal.Name(marker),unreal.Name('PlayableLook_v2')]
        a.static_mesh_component.set_static_mesh(asset)
        a.set_actor_scale3d(unreal.Vector(*scale))
        a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        a.static_mesh_component.set_material(0,palette[material]);owned[name]=a
    return a

cube=unreal.load_asset('/Engine/BasicShapes/Cube')
sphere=unreal.load_asset('/Engine/BasicShapes/Sphere')
for i in range(20):
    trunk=owned.get('PlayableTreeTrunk'+str(i));crown=owned.get('PlayableTreeCrown'+str(i))
    if not trunk or not crown: raise RuntimeError('Owned tree missing')
    trunk.static_mesh_component.set_material(0,palette['bark'])
    crown.static_mesh_component.set_static_mesh(sphere)
    crown.static_mesh_component.set_material(0,palette['leaf'])
    crown.set_actor_scale3d(unreal.Vector(4.3+(i%3)*.3,4.1,5.2))
    pos=trunk.get_actor_location()
    decor('PlayableLook_v2_Canopy'+str(i),sphere,(pos.x+120,pos.y-70,510),(3.6,3.4,3.9),'leaf')
    decor('PlayableLook_v2_CanopyTip'+str(i),sphere,(pos.x-90,pos.y+60,780),(3.2,3.2,3.6),'leaf')

for side in (-1,1):
    decor('PlayableLook_v2_Pavement'+str(side),cube,(0,-1500+side*475,4),(180,1.4,.08),'walk')
    decor('PlayableLook_v2_RoadEdge'+str(side),cube,(0,-1500+side*370,3),(175,.1,.01),'paint')
for i in range(25):
    decor('PlayableLook_v2_RoadDash'+str(i),cube,(-8400+i*700,-1500,3),(3,.12,.01),'paint')
for i in range(24):
    x=-8200+(i%12)*1460;y=5400 if i<12 else -5500
    decor('PlayableLook_v2_Shrub'+str(i),sphere,(x,y,50),(1.5,1.2,1.1),'leaf')
    decor('PlayableLook_v2_Rock'+str(i),sphere,(x+300,y+150,25),(1.1,.8,.6),'stone')
# Non-colliding background relief outside the walkable 200m zone, not a terrain claim.
for i in range(12):
    angle=i*math.tau/12
    decor('PlayableLook_v2_BackgroundHill'+str(i),sphere,
          (math.cos(angle)*21000,math.sin(angle)*21000,-1800),
          (190+(i%3)*20,180,85+(i%4)*12),'grass')

for name in ('PlayableSun','PlayableSky'):
    a=owned.get(name)
    if not a: raise RuntimeError('Owned light missing: '+name)
    a.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
sun=owned['PlayableSun'].light_component
sun.set_editor_property('atmosphere_sun_light',True)
sun.set_editor_property('light_source_angle',1.0)
sun.set_editor_property('dynamic_shadow_distance_movable_light',20000.)
owned['PlayableSky'].light_component.set_editor_property('real_time_capture',True)
if 'PlayableLook_v2_Fog' not in owned:
    fog=actors.spawn_actor_from_class(unreal.ExponentialHeightFog,unreal.Vector(0,0,0))
    fog.set_actor_label('PlayableLook_v2_Fog');fog.tags=[unreal.Name(marker),unreal.Name('PlayableLook_v2')]
if not level.save_current_level(): raise RuntimeError('Cannot save playable visual upgrade')
receipt=os.environ.get('ANOMALIA_PLAYABLE_ZONE_REPORT')
if not receipt: raise RuntimeError('Explicit playable zone receipt path required')
proof=dict(state='PLAYABLE_LOOK_V2_SAVED',sourceCommit=os.environ.get('GITHUB_SHA'),map=PACKAGE,
           lookVersion=2,ownedActorCount=len(owned),materialCount=len(palette),
           dynamicLights=all(owned[name].light_component.get_editor_property('mobility')==unreal.ComponentMobility.MOVABLE for name in ('PlayableSun','PlayableSky')))
if not proof['dynamicLights']: raise RuntimeError('Dynamic lighting was not applied')
Path(receipt).write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
unreal.log('ANOMALIA playable look v2 saved: original materials, dynamic lighting, road detail and vegetation; packaged GPU validation required.')
