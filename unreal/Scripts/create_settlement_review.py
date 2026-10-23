"""Build a separate, original urban review scene using previously validated art.
Never changes the archipelago or any player/server data. Placement is not a walk test.
"""
import importlib.util
import json
import os
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=Path(os.environ['ANOMALIA_SETTLEMENT_REPORT'])
report=dict(state='FAILED',sourceCommit=os.environ.get('GITHUB_SHA','manual'),walkingTested=False,multiplayerTested=False,productionWorldModified=False)
try:
    spec=importlib.util.spec_from_file_location('settlement_layout',ROOT/'Scripts/settlement_layout.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);plan=module.layout()
    source=[]
    for group in ['OriginalLot1','Expansion1']:source.extend(json.loads((ROOT/'SourceAssets'/group/'manifest.json').read_text())['models'])
    catalogue={m['id']:m for m in source};loaded={}
    # Resolve every source before creating anything, preserving any existing scene.
    for item in plan['buildings']+module.service_fleet():
        model=catalogue[item['model']];mesh=unreal.EditorAssetLibrary.load_asset(model['objectPath'])
        tag='AnomaliaOriginalLot1SHA' if item['model'] in ['hlm_8floors_v1','beach_villa_pool_v1'] else 'AnomaliaExpansionSHA'
        if not isinstance(mesh,unreal.StaticMesh) or unreal.EditorAssetLibrary.get_metadata_tag(mesh,tag)!=model['sha256']:
            raise RuntimeError('Missing or unverified building: '+item['model'])
        bounds=mesh.get_bounds()
        if bounds.box_extent.x*2>item['width']*100+1 or bounds.box_extent.y*2>item['depth']*100+1:
            raise RuntimeError('Building exceeds its reserved parcel: '+item['id'])
        loaded[item['model']]=mesh
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    package='/Game/Maps/ANOMALIA_UrbanReview_v1'
    def deploy_services():
        vehicle_class=unreal.load_class(None,'/Script/AnomaliaPrimeval.AnomaliaVehiclePawn')
        if not vehicle_class:raise RuntimeError('Native possessable vehicle class unavailable')
        existing={a.get_actor_label():a for a in actors.get_all_level_actors()}
        placed=[]
        for item in module.service_fleet():
            label='ANOMALIA_Urban1_'+item['id']
            if label in existing:
                a=existing[label]
                if a.get_class()!=vehicle_class or unreal.Name('ANOMALIA_Urban1_ServiceFleet') not in a.tags or str(a.get_editor_property('vehicle_id'))!=item['model']:
                    raise RuntimeError('Existing unowned or modified service actor preserved: '+label)
                placed.append(dict(id=item['id'],vehicleId=item['model'],state='EXISTING_PRESERVED'))
                continue
            # Sphere bottom at pavement elevation; native refresh places the model on that bottom.
            a=actors.spawn_actor_from_class(vehicle_class,unreal.Vector(item['x']*100,item['y']*100,175))
            if not a:raise RuntimeError('Could not create service vehicle: '+label)
            a.set_actor_label(label);a.tags=[unreal.Name('ANOMALIA_Urban1_ServiceFleet')]
            a.set_editor_property('presentation_mesh_override',loaded[item['model']])
            if not a.configure_vehicle(unreal.Name(item['model'])):raise RuntimeError('Service vehicle configuration failed: '+label)
            placed.append(dict(id=item['id'],vehicleId=item['model'],state='POSSESSABLE_NOT_PLAYTESTED'))
        return placed
    if unreal.EditorAssetLibrary.does_asset_exist(package):
        if not level.load_level(package):raise RuntimeError('Cannot load existing review map')
        present={a.get_actor_label():a for a in actors.get_all_level_actors()}
        if 'ANOMALIA_Urban1_OwnershipMarker' not in present:raise RuntimeError('Existing unowned map preserved')
        for item in plan['buildings']:
            if 'ANOMALIA_Urban1_'+item['id'] not in present:raise RuntimeError('Existing incomplete scene preserved for inspection')
        report['serviceFleet']=deploy_services()
        if not level.save_current_level():raise RuntimeError('Cannot save service fleet')
        report.update(state='EXISTING_URBAN_REVIEW_PRESERVED_NOT_PLAYTESTED',mapPackage=package,buildingCount=len(plan['buildings']))
    else:
        if not level.new_level(package):raise RuntimeError('Cannot create independent city review scene')
        def place(name,cls,position):
            actor=actors.spawn_actor_from_class(cls,unreal.Vector(*position));actor.set_actor_label('ANOMALIA_Urban1_'+name);actor.tags=[unreal.Name('ANOMALIA_Urban1')];return actor
        def material(name,color):
            path='/Game/Anomalia/World/UrbanReview1/'+name
            if unreal.EditorAssetLibrary.does_asset_exist(path):return unreal.EditorAssetLibrary.load_asset(path)
            value=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,'/Game/Anomalia/World/UrbanReview1',unreal.Material,unreal.MaterialFactoryNew())
            expression=unreal.MaterialEditingLibrary.create_material_expression(value,unreal.MaterialExpressionConstant3Vector)
            expression.set_editor_property('constant',unreal.LinearColor(*color,1))
            unreal.MaterialEditingLibrary.connect_material_property(expression,'',unreal.MaterialProperty.MP_BASE_COLOR)
            unreal.MaterialEditingLibrary.recompile_material(value)
            if not unreal.EditorAssetLibrary.save_loaded_asset(value,only_if_is_dirty=False):raise RuntimeError('Material save failed')
            return value
        palette=dict(ground=material('M_Grass',(.13,.2,.07)),road=material('M_Asphalt',(.055,.06,.065)),walk=material('M_Pavement',(.5,.48,.44)))
        cube=unreal.load_asset('/Engine/BasicShapes/Cube')
        def box(name,rect,z,height,mat):
            x0,y0,x1,y1=rect
            a=place(name,unreal.StaticMeshActor,((x0+x1)*50,(y0+y1)*50,z-height*50))
            c=a.get_component_by_class(unreal.StaticMeshComponent);c.set_static_mesh(cube);c.set_material(0,mat);c.set_collision_profile_name('BlockAll')
            a.set_actor_scale3d(unreal.Vector(x1-x0,y1-y0,height));return a
        place('OwnershipMarker',unreal.Actor,(0,0,0))
        # Ground top is zero; pool holes extend through the full ground slab.
        for i,rect in enumerate(module.ground_rectangles(plan['groundBounds'],plan['pools'])):box('ground_'+str(i),rect,0,3,palette['ground'])
        for item in plan['roads']:
            rect=module.rectangle(item);box(item['id'],rect,2,.12,palette['road'])
            horizontal=item['width']>item['depth']
            for side in [-1,1]:
                if horizontal:walk=[rect[0],item['y']+side*4.5-1,rect[2],item['y']+side*4.5+1]
                else:walk=[item['x']+side*4.5-1,rect[1],item['x']+side*4.5+1,rect[3]]
                # Crossroads keep the intersecting carriageway clear.
                cuts=[-80,0,80] if horizontal else [-180,-120,-60,0,60,120,180]
                low,high=(walk[0],walk[2]) if horizontal else (walk[1],walk[3])
                ends=sorted({low,high,*(max(low,min(high,v+d)) for v in cuts for d in [-5.5,5.5])})
                for index,(lo,hi) in enumerate(zip(ends,ends[1:])):
                    if any(v-5.5<(lo+hi)/2<v+5.5 for v in cuts):continue
                    part=[lo,walk[1],hi,walk[3]] if horizontal else [walk[0],lo,walk[2],hi]
                    box(item['id']+'_walk_'+str(side)+'_'+str(index),part,15,.15,palette['walk'])
        report['placements']=[]
        for item in plan['buildings']:
            mesh=loaded[item['model']];bounds=mesh.get_bounds()
            # Horizontal footprint centred on each parcel. Keep villa floor at grade;
            # its swimming-pool recess is represented by the matching ground hole.
            a=place(item['id'],unreal.StaticMeshActor,(item['x']*100-bounds.origin.x,item['y']*100-bounds.origin.y,0))
            c=a.get_component_by_class(unreal.StaticMeshComponent);c.set_static_mesh(mesh);c.set_collision_profile_name('BlockAll')
            report['placements'].append(dict(id=item['id'],model=item['model'],locationCm=str(a.get_actor_location())))
        report['serviceFleet']=deploy_services()
        sun=place('Sun',unreal.DirectionalLight,(0,0,3000));sun.set_actor_rotation(unreal.Rotator(pitch=-45,yaw=-30,roll=0),False)
        place('Sky',unreal.SkyAtmosphere,(0,0,0));place('Ambient',unreal.SkyLight,(0,0,1000))
        place('PlayerStart',unreal.PlayerStart,(1500,-1500,120))
        if not level.save_current_level():raise RuntimeError('Cannot save urban scene')
        report.update(state='URBAN_REVIEW_CREATED_NOT_PLAYTESTED',mapPackage=package,buildingCount=len(plan['buildings']),roadCount=len(plan['roads']),poolRecessCount=len(plan['pools']))
except Exception as error:
    report['error']=str(error);raise
finally:
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2)+'\n');unreal.log(json.dumps(report))
