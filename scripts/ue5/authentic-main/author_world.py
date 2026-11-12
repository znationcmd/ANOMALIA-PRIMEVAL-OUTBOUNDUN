"""Place the existing complete native E39 in the actual, backed-up SKARVIK world."""
import gc
import hashlib
import json
import os
import shutil
import traceback
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir()).resolve()
out = Path(os.environ['AUTHENTIC_OUT'])
report = {'state': 'FAILED', 'map': '/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1'}


def vector(v):
    return [float(v.x), float(v.y), float(v.z)]


def path(a):
    return a.get_path_name() if a else None


try:
    if root != Path(r'D:\ANOMALIAZ\01_Projet_Principal\unreal').resolve():
        raise RuntimeError('Unexpected authoritative native project')
    # These genuine models are loaded by native gameplay at runtime, so package
    # them explicitly even when their assets are not placed as editor actors.
    config = root/'Config/DefaultGame.ini'
    previous_config = config.read_text(encoding='utf-8-sig')
    config_backup = out/'DefaultGame.ini.before'
    if not config_backup.exists():
        shutil.copy2(config, config_backup)
    section = '/Script/UnrealEd.ProjectPackagingSettings'
    cooked_dirs = ['/Game/Survival_Character', '/Game/German_Shepherd_3D_Model']
    lines = ['+DirectoriesToAlwaysCook=(Path="'+item+'")' for item in cooked_dirs]
    missing = [line for line in lines if line not in previous_config]
    if missing:
        config.write_text(previous_config+'\n['+section+']\n'+'\n'.join(missing)+'\n', encoding='utf-8')
    report['runtimeModelCookDirectories'] = cooked_dirs
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    registry.wait_for_completion()
    editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    review = root/'Content/Maps/ANOMALIA_E39DriveReview_v1.umap'
    validated = Path(r'C:\ANOMALIA-Validation\c40543166274\unreal\Content\Maps\ANOMALIA_E39DriveReview_v1.umap')
    if not review.exists():
        if not validated.is_file():
            raise RuntimeError('The previously configured genuine E39 physics review is missing')
        shutil.copy2(validated, review)
        registry.scan_paths_synchronous(['/Game/Maps'], True)
    if not editor.load_level('/Game/Maps/ANOMALIA_E39DriveReview_v1'):
        raise RuntimeError('The original complete E39 configuration did not load')
    cars = [a for a in actors.get_all_level_actors() if isinstance(a, unreal.AnomaliaChaosRoadVehicle)]
    if len(cars) != 1:
        raise RuntimeError('Expected one previously authored E39 native physics actor')
    car = cars[0]
    # Restore broken review-world soft references from the installed vehicle kit.
    # The visible body remains the real E39; this is its skeletal physics carrier.
    rig_assets = registry.get_assets_by_path('/Game/Vehicles/OffroadCar', recursive=True)
    report['installedPhysicsKitAssets'] = [str(a.package_name) for a in rig_assets]
    for field, expected, generated in [('road_mesh','SKM_Offroad',False),('road_animation','Offroad_AnimBP',True)]:
        if car.get_editor_property(field):
            continue
        candidates = [a for a in rig_assets if str(a.asset_name)==expected]
        if len(candidates)!=1:
            raise RuntimeError('Cannot resolve installed original physics carrier '+expected)
        asset_path = str(candidates[0].package_name)+'.'+expected+('_C' if generated else '')
        restored = unreal.load_class(None,asset_path) if generated else unreal.load_asset(asset_path)
        if not restored:
            raise RuntimeError('Original physics carrier failed to load: '+asset_path)
        car.set_editor_property(field,restored)

    rig_mesh = car.get_editor_property('road_mesh')
    if not rig_mesh.get_editor_property('physics_asset'):
        original_physics = unreal.load_asset('/Game/Vehicles/OffroadCar/SKM_Offroad_PhysicsAsset')
        if not original_physics:
            raise RuntimeError('Installed original vehicle physics asset is missing')
        shutil.copy2(root/'Content/Vehicles/OffroadCar/SKM_Offroad.uasset',out/'SKM_Offroad.before.uasset')
        rig_mesh.set_editor_property('physics_asset',original_physics)
        if not unreal.EditorAssetLibrary.save_loaded_asset(rig_mesh):
            raise RuntimeError('Restored skeletal vehicle physics reference did not save')
    report['restoredCarrierPhysicsAsset'] = path(rig_mesh.get_editor_property('physics_asset'))
    carrier_component = car.get_editor_property('chassis')
    carrier_component.set_skeletal_mesh_asset(rig_mesh)
    carrier_bones = [str(carrier_component.get_bone_name(i)) for i in range(carrier_component.get_num_bones())]
    report['installedCarrierBones'] = carrier_bones
    if any(carrier_component.get_bone_index(b)<0 for b in car.get_editor_property('wheel_bones')):
        aliases = [('wheelfl','wheelfrontleft','frontleftwheel'),('wheelfr','wheelfrontright','frontrightwheel'),('wheelbl','wheelrl','wheelbackleft','wheelrearleft','rearleftwheel'),('wheelbr','wheelrr','wheelbackright','wheelrearright','rearrightwheel')]
        resolved_bones = []
        for suffixes in aliases:
            matches = [b for b in carrier_bones if ''.join(c.lower() for c in b if c.isalnum()).endswith(suffixes)]
            if len(matches)!=1:
                raise RuntimeError('Installed wheel skeleton mapping is ambiguous: '+str(matches)+' in '+str(carrier_bones))
            resolved_bones.append(unreal.Name(matches[0]))
        if len(set(str(b) for b in resolved_bones))!=4:
            raise RuntimeError('Original wheel skeleton mapping is not unique')
        car.set_editor_property('wheel_bones',resolved_bones)
    carrier_component = None

    rig_mesh = None
    restored = None
    candidates = []
    rig_assets = []

    asset_fields = ['road_mesh', 'road_animation', 'road_body_mesh', 'road_wheel_mesh', 'road_glass_mesh', 'driver_door_mesh']
    recipe = {name: path(car.get_editor_property(name)) for name in asset_fields}
    if not recipe['road_body_mesh'].startswith('/Game/Anomalia/BMWE39Review_v7/'):
        raise RuntimeError('Reference vehicle is not the genuine E39 v7')
    recipe['wheel_bones'] = [str(x) for x in car.get_editor_property('wheel_bones')]
    recipe['wheel_radius_cm'] = float(car.get_editor_property('wheel_radius_cm'))
    recipe['driver_door_pivot_cm'] = vector(car.get_editor_property('driver_door_pivot_cm'))
    recipe['driver_door_open_angle'] = float(car.get_editor_property('driver_door').get_editor_property('open_angle_degrees'))
    recipe['road_wheel_meshes'] = [path(x) for x in car.get_editor_property('road_wheel_meshes')]
    recipe['road_wheel_hub_targets_cm'] = [vector(x) for x in car.get_editor_property('road_wheel_hub_targets_cm')]
    recipe['panels'] = []
    for panel in car.get_editor_property('additional_panel_definitions'):
        recipe['panels'].append({'panel_id': str(panel.get_editor_property('panel_id')), 'mesh': path(panel.get_editor_property('mesh')), 'pivot_cm': vector(panel.get_editor_property('pivot_cm')), 'hinge_axis': vector(panel.get_editor_property('hinge_axis')), 'open_angle_degrees': float(panel.get_editor_property('open_angle_degrees'))})
    (out/'genuine-e39-recipe.json').write_text(json.dumps(recipe, indent=2), encoding='utf-8')
    # Release every reference to the review-world actor before switching maps.
    car = None
    cars = []
    panel = None
    gc.collect()
    target = root/'Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap'
    if not target.is_file():
        raise RuntimeError('The authoritative SKARVIK world is missing')
    backup = out/'PRIGIMALIA_SKARVIK_FINAL_v1.before.umap'
    shutil.copy2(target, backup)
    report['sourceMapSha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
    if not editor.load_level(report['map']):
        raise RuntimeError('The actual SKARVIK world failed to open')
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not world.get_path_name().startswith(report['map']+'.'):
        raise RuntimeError('Editor opened a different world')
    descs = unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or []
    if len(descs) < 1000:
        raise RuntimeError('Actual SKARVIK actor population is missing')
    chosen = [d.guid for d in descs if 'PLAYERSTART' in str(d.label).upper().replace('_', '').replace(' ', '') or str(d.label).startswith('SKARVIK_COMPLETE_REAL_BUILDING_')]
    if chosen:
        unreal.WorldPartitionBlueprintLibrary.load_actors(chosen)
    loaded = actors.get_all_level_actors()
    starts = [a for a in loaded if isinstance(a, unreal.PlayerStart) and not a.actor_has_tag('ANOMALIA_AUTHENTIC_START')]
    if not starts:
        raise RuntimeError('No original SKARVIK player start is available')
    start = min(starts, key=lambda a: (a.get_actor_location().x-200000)**2+(a.get_actor_location().y-800000)**2)
    p = start.get_actor_location()
    report['originalStart'] = {'label': start.get_actor_label(), 'position': vector(p)}
    # Load actual nearby ground, roads and landscape cells as runtime would.
    region = unreal.Box(min=unreal.Vector(p.x-5000,p.y-5000,p.z-50000), max=unreal.Vector(p.x+5000,p.y+5000,p.z+50000))
    nearby = unreal.WorldPartitionBlueprintLibrary.get_intersecting_actor_descs(region) or []
    runtime_nearby = [d for d in nearby if not d.actor_is_editor_only]
    report['nearbyRuntimeDescriptors'] = [{'label':str(d.label),'class':str(d.native_class),'min':vector(d.bounds.min),'max':vector(d.bounds.max)} for d in runtime_nearby]
    unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in runtime_nearby])
    loaded = actors.get_all_level_actors()
    report['groundTraceDiagnostics'] = []

    city = []
    for a in loaded:
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            mesh = c.get_editor_property('static_mesh')
            if mesh and mesh.get_path_name().startswith(('/Game/Building/', '/Game/City/')):
                city.append({'actor': a.get_actor_label(), 'mesh': mesh.get_path_name()})
    if len(city) < 10:
        raise RuntimeError('Actual City Sample building geometry is not present at the authored scene')
    report['authenticCityMeshes'] = len(city)
    report['cityMeshSample'] = city[:30]

    def trace(x, y):
        hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, p.z+500), unreal.Vector(x, y, p.z-10000), unreal.TraceTypeQuery.ECC_VISIBILITY, True, [], unreal.DrawDebugTrace.NONE)
        if hit is None or not hit.to_tuple()[0]:
            return None
        point = hit.to_tuple()[5]
        normal = hit.to_tuple()[6]
        report['groundTraceDiagnostics'].append({'x':x,'y':y,'point':vector(point),'normal':vector(normal)})
        if normal.z < .8 or abs(point.z-p.z) > 10000:
            return None
        return point

    ground = trace(p.x, p.y)
    if ground is None:
        raise RuntimeError('No verified real ground underneath original city player start')
    existing = {a.get_actor_label(): a for a in loaded}

    def owned_actor(cls, label, tag, location):
        a = existing.get(label)
        if a:
            if not a.actor_has_tag(tag) or not isinstance(a, cls):
                raise RuntimeError('An unrelated artist actor occupies '+label)
        else:
            a = actors.spawn_actor_from_class(cls, location)
            if not a:
                raise RuntimeError('Could not create '+label)
            a.set_actor_label(label)
            a.tags = [unreal.Name(tag)]
        a.set_editor_property('is_spatially_loaded', False)
        return a

    spawn = owned_actor(unreal.PlayerStart, 'ANOMALIA_AUTHENTIC_CITY_START', 'ANOMALIA_AUTHENTIC_START', unreal.Vector(ground.x, ground.y, ground.z+120))
    report['authenticStart'] = vector(spawn.get_actor_location())
    parking = None
    for dx, dy in [(600,100),(600,-100),(-600,100),(100,600),(100,-600),(900,0),(-900,0)]:
        q = trace(p.x+dx, p.y+dy)
        if q is None:
            continue
        wheel_floors = [trace(q.x+x, q.y+y) for x,y in [(150,-76),(150,75),(-131,-76),(-131,75)]]
        if all(x is not None for x in wheel_floors) and max(x.z for x in wheel_floors)-min(x.z for x in wheel_floors)<25:
            parking = q
            break
    if parking is None:
        raise RuntimeError('No flat real ground for the E39 near the genuine city start')
    car = owned_actor(unreal.AnomaliaChaosRoadVehicle, 'ANOMALIA_AUTHENTIC_BMW_E39_V7', 'ANOMALIA_AUTHENTIC_E39', unreal.Vector(parking.x, parking.y, parking.z+100))
    for name in asset_fields:
        value = recipe[name]
        a = unreal.load_class(None, value) if name=='road_animation' and value else unreal.load_asset(value) if value else None
        if value and a is None:
            raise RuntimeError('Missing real vehicle dependency: '+value)
        car.set_editor_property(name, a)
    car.set_editor_property('wheel_bones', [unreal.Name(x) for x in recipe['wheel_bones']])
    car.set_editor_property('wheel_radius_cm', recipe['wheel_radius_cm'])
    car.set_editor_property('driver_door_pivot_cm', unreal.Vector(*recipe['driver_door_pivot_cm']))
    car.get_editor_property('driver_door').set_editor_property('open_angle_degrees', recipe['driver_door_open_angle'])
    car.set_editor_property('road_wheel_meshes', [unreal.load_asset(x) for x in recipe['road_wheel_meshes']])
    car.set_editor_property('road_wheel_hub_targets_cm', [unreal.Vector(*x) for x in recipe['road_wheel_hub_targets_cm']])
    panels = []
    for item in recipe['panels']:
        definition = unreal.AnomaliaRoadPanelDefinition()
        for name in ['panel_id','mesh','pivot_cm','hinge_axis','open_angle_degrees']:
            value = item[name]
            if name=='panel_id':value=unreal.Name(value)
            elif name=='mesh':value=unreal.load_asset(value)
            elif name in ['pivot_cm','hinge_axis']:value=unreal.Vector(*value)
            definition.set_editor_property(name,value)
        panels.append(definition)
    car.set_editor_property('additional_panel_definitions', panels)
    car.get_editor_property('survival_systems').set_editor_property('enabled', True)
    car.get_editor_property('survival_systems').set_editor_property('battery_access_panel', unreal.Name('trunk'))
    car.set_actor_location(unreal.Vector(parking.x, parking.y, parking.z+100), False, True)
    car.set_actor_rotation(unreal.Rotator(), False)

    try:
        chassis = car.get_editor_property('chassis')
        chassis.set_skeletal_mesh_asset(car.get_editor_property('road_mesh'))
        report['rigDiagnostics'] = {'roadMesh':path(car.get_editor_property('road_mesh')), 'animation':path(car.get_editor_property('road_animation')), 'panelDefinitions':len(panels), 'panelCapacity':len(car.get_editor_property('additional_panels')), 'boneIndices':{str(b):chassis.get_bone_index(b) for b in car.get_editor_property('wheel_bones')}, 'valid':car.has_valid_road_rig()}
        chassis = None
    except Exception as diagnostic_error:
        report['rigDiagnosticsError'] = str(diagnostic_error)
    if not car.has_valid_road_rig():
        raise RuntimeError('Original native E39 rig rejected in the true world')
    if not editor.save_all_dirty_levels() or not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True):
        raise RuntimeError('Real-world authored actors did not save')
    report.update(state='AUTHENTIC_E39_SAVED_IN_TRUE_SKARVIK_NOT_YET_PLAYTESTED', originalActorsNotDeleted=True, carPosition=vector(car.get_actor_location()), body=recipe['road_body_mesh'], panels=len(panels)+1, worldPartitionDescriptors=len(descs))
except Exception:
    report['error'] = traceback.format_exc()
finally:
    (out/'authored-world.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    unreal.SystemLibrary.quit_editor()
