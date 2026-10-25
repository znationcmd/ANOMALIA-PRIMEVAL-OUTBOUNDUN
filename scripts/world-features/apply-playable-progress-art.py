"""Deliver verified art to the existing playable zone without changing save identities."""
import json
import os
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=Path(os.environ['ANOMALIA_PROGRESS_ART_REPORT'])
OWNER=unreal.Name('ANOMALIA_Playable_v1_Owner')
TAG=unreal.Name('ANOMALIA_ProgressArt_v1')
report=dict(state='FAILED',sourceCommit=os.environ.get('GITHUB_SHA'),fullMapComplete=False,houses=[],trees=0,vehicles=[],rocks=0,groundFoliage=0,hiddenBackgroundPrototypes=0)
try:
    level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    editor=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    manifest=json.loads((ROOT/'SourceAssets/ResidentialPhotogrammetryPrepared_v1/manifest.json').read_text())
    models={m['id']:m for m in manifest['models']};loaded={}
    for ident in ('country_house_scan','abandoned_brick_house_scan'):
        m=models[ident];mesh=unreal.load_asset(m['objectPath'])
        if not mesh or unreal.EditorAssetLibrary.get_metadata_tag(mesh,'AnomaliaWorldFeatureSha256')!=m['sha256']:
            raise RuntimeError('Source-verified native dwelling required')
        loaded[ident]=mesh
    tree_paths=unreal.EditorAssetLibrary.list_assets('/Game/Anomalia/VerifiedProps_v1/pine_tree_01',recursive=True,include_folder=False)
    trees=[unreal.load_asset(p) for p in tree_paths]
    trees=[m for m in trees if isinstance(m,unreal.StaticMesh) and unreal.EditorAssetLibrary.get_metadata_tag(m,'AnomaliaPropsSourceSha256')]
    if not trees:
        real=json.loads((ROOT/'SourceAssets/RealismValidation_v2/manifest.json').read_text())
        item=next(m for m in real['models'] if m['id']=='island_tree_02')
        candidate=unreal.load_asset(item['objectPath']+'_r2')
        if not candidate or unreal.EditorAssetLibrary.get_metadata_tag(candidate,'AnomaliaRealismSha256')!=item['sha256']:
            raise RuntimeError('A verified realistic tree is required')
        trees=[candidate]
    tree=max(trees,key=lambda m:max(m.get_num_triangles(0),m.get_num_nanite_triangles()))
    for mesh in [tree]+list(loaded.values()):
        settings=editor.get_nanite_settings(mesh)
        if settings.get_editor_property('enabled'):
            settings.set_editor_property('enabled',False);editor.set_nanite_settings(mesh,settings,apply_changes=True)
        body=mesh.get_editor_property('body_setup')
        if body:body.set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        if not unreal.EditorAssetLibrary.save_loaded_asset(mesh,only_if_is_dirty=False):raise RuntimeError('Art settings save failed')
    if not level.load_level('/Game/Maps/ANOMALIA_Playable_v1'):raise RuntimeError('Existing playable map required')
    present={a.get_actor_label():a for a in actors.get_all_level_actors()}
    if str(OWNER) not in present:raise RuntimeError('Owned playable zone required')
    for ident,x,y,height in [('country_house_scan',-5500,-4500,700.),('abandoned_brick_house_scan',6000,3500,1000.)]:
        mesh=loaded[ident];bounds=mesh.get_bounds();scale=height/(bounds.box_extent.z*2)
        if max(bounds.box_extent.x,bounds.box_extent.y)*scale>1800:raise RuntimeError('Scan exceeds its reserved parcel')
        label='ProgressArt_'+ident;actor=present.get(label)
        if actor:
            if TAG not in actor.tags or not isinstance(actor,unreal.StaticMeshActor):raise RuntimeError('Existing artist house preserved')
        else:
            actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(x,y,0));actor.set_actor_label(label);actor.tags=[TAG]
        actor.static_mesh_component.set_static_mesh(mesh);actor.static_mesh_component.set_collision_profile_name('BlockAll')
        actor.set_actor_scale3d(unreal.Vector(scale,scale,scale))
        actor.set_actor_location(unreal.Vector(x,y,-(bounds.origin.z-bounds.box_extent.z)*scale-45),False,False)
        report['houses'].append(dict(id=ident,mesh=mesh.get_path_name(),exteriorOnly=True,scaleMethod='Uniform artistic height calibration'))
    b=tree.get_bounds();tree_scale=min(1.,1400/(b.box_extent.z*2))
    for index in range(20):
        trunk=present.get('PlayableTreeTrunk'+str(index));crown=present.get('PlayableTreeCrown'+str(index))
        if not trunk or not crown or OWNER not in trunk.tags or OWNER not in crown.tags:raise RuntimeError('Owned original tree actors required')
        position=trunk.get_actor_location()
        trunk.static_mesh_component.set_static_mesh(tree)
        trunk.static_mesh_component.set_editor_property('override_materials',[])
        trunk.set_actor_scale3d(unreal.Vector(tree_scale,tree_scale,tree_scale))
        trunk.set_actor_location(unreal.Vector(position.x,position.y,-(b.origin.z-b.box_extent.z)*tree_scale),False,False)
        trunk.tags=list(set(list(trunk.tags)+[TAG,unreal.Name('ANOMALIA_ProgressTree_v1')]))
        # The look-v2 scene adds two more spherical canopies per original tree.
        # Retain all actors, but hide every provisional crown component explicitly.
        for label in ('PlayableTreeCrown'+str(index),'PlayableLook_v2_Canopy'+str(index),'PlayableLook_v2_CanopyTip'+str(index)):
            old=present.get(label)
            if not old or OWNER not in old.tags:raise RuntimeError('Owned provisional canopy required: '+label)
            old.set_actor_hidden_in_game(True)
            old.static_mesh_component.set_visibility(False,True)
            old.static_mesh_component.set_hidden_in_game(True,True)
            old.tags=list(set(list(old.tags)+[TAG,unreal.Name('ANOMALIA_ProgressHiddenCrown_v1')]))
        report['trees']+=1
    real=json.loads((ROOT/'SourceAssets/RealismValidation_v2/manifest.json').read_text())
    for prefix,source_id,target_size,tag,field in [
        ('PlayableLook_v2_Rock','rock_moss_set_01',130.,'ANOMALIA_ProgressRock_v1','rocks'),
        ('PlayableLook_v2_Shrub','grass_medium_01',200.,'ANOMALIA_ProgressGroundFoliage_v1','groundFoliage')]:
        item=next(m for m in real['models'] if m['id']==source_id)
        mesh=unreal.load_asset(item['objectPath']+'_r2')
        if not isinstance(mesh,unreal.StaticMesh) or unreal.EditorAssetLibrary.get_metadata_tag(mesh,'AnomaliaRealismSha256')!=item['sha256']:
            raise RuntimeError('Source-verified realistic terrain prop required: '+source_id)
        settings=editor.get_nanite_settings(mesh)
        if settings.get_editor_property('enabled'):
            settings.set_editor_property('enabled',False);editor.set_nanite_settings(mesh,settings,apply_changes=True)
        if not unreal.EditorAssetLibrary.save_loaded_asset(mesh,only_if_is_dirty=False):raise RuntimeError('Terrain prop settings did not save')
        bounds=mesh.get_bounds();extent=bounds.box_extent
        largest=max(extent.x,extent.y,extent.z)*2
        if largest<=0:raise RuntimeError('Empty terrain prop bounds')
        scale=target_size/largest
        for index in range(24):
            actor=present.get(prefix+str(index))
            if not actor or OWNER not in actor.tags or not isinstance(actor,unreal.StaticMeshActor):
                raise RuntimeError('Owned original terrain prop required')
            position=actor.get_actor_location()
            actor.static_mesh_component.set_static_mesh(mesh)
            actor.static_mesh_component.set_editor_property('override_materials',[])
            actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            actor.set_actor_scale3d(unreal.Vector(scale,scale,scale))
            actor.set_actor_location(unreal.Vector(position.x,position.y,(extent.z-bounds.origin.z)*scale+2),False,False)
            actor.tags=list(set(list(actor.tags)+[TAG,unreal.Name(tag)]))
            report[field]+=1
    for index in range(12):
        actor=present.get('PlayableLook_v2_BackgroundHill'+str(index))
        if not actor or OWNER not in actor.tags:raise RuntimeError('Owned background prototype required')
        actor.set_actor_hidden_in_game(True)
        actor.static_mesh_component.set_visibility(False,True)
        actor.static_mesh_component.set_hidden_in_game(True,True)
        actor.tags=list(set(list(actor.tags)+[TAG,unreal.Name('ANOMALIA_ProgressHiddenBackground_v1')]))
        report['hiddenBackgroundPrototypes']+=1
    for vehicle_id,source_id in [('car','concept_car'),('transport_truck','box_truck')]:
        item=next(m for m in real['models'] if m['id']==source_id)
        mesh=unreal.load_asset(item['objectPath']+'_r2')
        if not mesh or unreal.EditorAssetLibrary.get_metadata_tag(mesh,'AnomaliaRealismSha256')!=item['sha256']:raise RuntimeError('Verified vehicle art required')
        candidates=[a for a in present.values() if OWNER in a.tags and a.get_class().get_path_name()=='/Script/AnomaliaPrimeval.AnomaliaVehiclePawn' and str(a.get_editor_property('vehicle_id'))==vehicle_id]
        if len(candidates)!=1:raise RuntimeError('Unique existing playable vehicle required')
        vehicle=candidates[0];vehicle.set_editor_property('presentation_mesh_override',mesh)
        if not vehicle.configure_vehicle(unreal.Name(vehicle_id)):raise RuntimeError('Detailed vehicle binding failed')
        report['vehicles'].append(vehicle_id)
    if not level.save_current_level() or not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):raise RuntimeError('Playable progress art did not save')
    report['state']='PROGRESS_ART_SAVED_REQUIRES_PACKAGED_GAME_TEST'
except Exception as error:
    report['error']=str(error);raise
finally:
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2)+'\n')
