"""Separate closed review track with a native metro lead and three server-owned coaches."""
import json
import math
import os
from pathlib import Path
import unreal
OUT=Path(os.environ['ANOMALIA_METRO_RAIL_REPORT'])
report=dict(state='FAILED',sourceCommit=os.environ.get('GITHUB_SHA','manual'),drivingTested=False,multiplayerTested=False)
try:
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    package='/Game/Maps/ANOMALIA_MetroRailReview_v2';marker='ANOMALIA_MetroRail1_OwnershipMarker'
    if unreal.EditorAssetLibrary.does_asset_exist(package):
        if not level.load_level(package):raise RuntimeError('Cannot load review map')
        present={a.get_actor_label():a for a in actors.get_all_level_actors()}
        if marker not in present or 'ANOMALIA_MetroRail1_Lead' not in present:raise RuntimeError('Unowned/incomplete map preserved')
        report.update(state='EXISTING_METRO_RAIL_REVIEW_PRESERVED_NOT_DRIVE_TESTED',mapPackage=package)
    else:
        for path in ['/Game/Anomalia/Vehicles/metro/SM_metro','/Game/Anomalia/Props/Metro1/SM_metro_wagon']:
            if not unreal.EditorAssetLibrary.does_asset_exist(path):raise RuntimeError('Metro art must be imported first')
        if not level.new_level(package):raise RuntimeError('Cannot create independent track map')
        def place(name,cls,pos):
            a=actors.spawn_actor_from_class(cls,unreal.Vector(*pos));a.set_actor_label('ANOMALIA_MetroRail1_'+name);return a
        place('OwnershipMarker',unreal.Actor,(0,0,0));cube=unreal.load_asset('/Engine/BasicShapes/Cube')
        def box(name,pos,scale,rotation=None):
            a=place(name,unreal.StaticMeshActor,pos);c=a.get_component_by_class(unreal.StaticMeshComponent);c.set_static_mesh(cube);c.set_collision_profile_name('BlockAll');a.set_actor_scale3d(unreal.Vector(*scale))
            if rotation:a.set_actor_rotation(rotation,False)
            return a
        box('Ground',(0,0,-25),(300,300,.5))
        track=place('Route',unreal.load_class(None,'/Script/AnomaliaZPrigimalia.AnomaliaRailTrack'),(0,0,0));spline=track.get_editor_property('track')
        spline.clear_spline_points(False)
        for i in range(16):
            t=i*math.tau/16;spline.add_spline_point(unreal.Vector(10000*math.cos(t),10000*math.sin(t),165),unreal.SplineCoordinateSpace.WORLD,False)
        spline.set_closed_loop(True,True)
        length=spline.get_spline_length();steps=math.ceil(length/400)
        for i in range(steps):
            d=length*i/steps;point=spline.get_location_at_distance_along_spline(d,unreal.SplineCoordinateSpace.WORLD);rotation=spline.get_rotation_at_distance_along_spline(d,unreal.SplineCoordinateSpace.WORLD)
            tangent=spline.get_direction_at_distance_along_spline(d,unreal.SplineCoordinateSpace.WORLD);right=unreal.Vector(-tangent.y,tangent.x,0)
            for side in [-1,1]:box('Rail_'+str(i)+'_'+str(side),(point.x+right.x*side*77,point.y+right.y*side*77,3),(length/steps/100+.02,.06,.04),rotation)
            box('Sleeper_'+str(i),(point.x,point.y,.5),(.22,2,.01),rotation)
        start=12000.;point=spline.get_location_at_distance_along_spline(start,unreal.SplineCoordinateSpace.WORLD)
        lead=place('Lead',unreal.load_class(None,'/Script/AnomaliaZPrigimalia.AnomaliaVehiclePawn'),(point.x,point.y,point.z))
        if not lead.configure_vehicle(unreal.Name('metro')):raise RuntimeError('Native metro unavailable')
        lead.set_actor_rotation(spline.get_rotation_at_distance_along_spline(start,unreal.SplineCoordinateSpace.WORLD),False)
        lead.set_editor_property('initial_rail_track',track);lead.set_editor_property('initial_rail_distance_cm',start)
        lead.configure_runtime_tuning(100.,0.,1.) # Prototype electric traction; no supply network simulation.
        place('PlayerStart',unreal.PlayerStart,(point.x+300,point.y,120))
        sun=place('Sun',unreal.DirectionalLight,(0,0,4000));sun.set_actor_rotation(unreal.Rotator(pitch=-45,yaw=-30,roll=0),False)
        place('Sky',unreal.SkyAtmosphere,(0,0,0));place('Ambient',unreal.SkyLight,(0,0,1000))
        if not level.save_current_level():raise RuntimeError('Cannot save review rail map')
        report.update(state='METRO_RAIL_REVIEW_CREATED_NOT_DRIVE_TESTED',mapPackage=package,trackLengthCm=length,trailingCoaches=3)
except Exception as error:report['error']=str(error);raise
finally:
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2)+'\n');unreal.log(json.dumps(report))
