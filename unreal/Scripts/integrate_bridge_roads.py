"""Append two original road approaches; never replace existing map objects."""
import hashlib,json,os,sys,uuid,math
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve();sys.path.insert(0,str(ROOT/'Scripts'))
from road_mesh import build_road
REPORT=Path(os.environ['ANOMALIA_ROADS_REPORT']);MARKER=ROOT/'Saved/AnomaliaMigration/detroit-roads-v2.json'
LEGACY=ROOT/'Saved/AnomaliaMigration/detroit-roads-v1.json'
TAG='ANOMALIA_DetroitRoads_v1';PACKAGE='/Game/Maps/ANOMALIA_Archipelago_v2'
result=dict(state='FAILED',sourceCommit=os.environ.get('GITHUB_SHA','manual'),walkTested=False,renderingValidated=False)
try:
    if MARKER.exists():
        prior=json.loads(MARKER.read_text())
        if prior.get('state')!='PLACED_NOT_PLAYTESTED' or prior.get('roadCount')!=2:raise RuntimeError('Unrecognized existing road marker preserved')
        result.update(prior);result.update(state='EXISTING_PLACEMENTS_PRESERVED',sourceCommit=os.environ.get('GITHUB_SHA','manual'))
    else:
        level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        if not level.load_level(PACKAGE):raise RuntimeError('Could not open validated map')
        actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        if not LEGACY.exists() and any(unreal.Name(TAG) in a.tags for a in actors.get_all_level_actors()):raise RuntimeError('Existing road actors preserved; refusing duplicate placement')
        previous={}
        if LEGACY.exists():
            legacy=json.loads(LEGACY.read_text())
            if legacy.get('state')!='PLACED_NOT_PLAYTESTED' or legacy.get('roadCount')!=2:raise RuntimeError('Unrecognized legacy roads preserved')
            descriptors=unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or []
            wanted=[d.guid for d in descriptors if str(d.label) in ['ANOMALIA_DetroitRoad_West','ANOMALIA_DetroitRoad_East']]
            if len(wanted)!=2:raise RuntimeError('Could not identify both original road actors; no duplicates created')
            unreal.WorldPartitionBlueprintLibrary.load_actors(wanted)
            for side in ['West','East']:
                found=[a for a in actors.get_all_level_actors() if a.get_actor_label()=='ANOMALIA_DetroitRoad_'+side and unreal.Name(TAG) in a.tags]
                old=next(r for r in legacy['roads'] if r['side']==side)
                if len(found)!=1 or found[0].get_component_by_class(unreal.StaticMeshComponent).get_editor_property('static_mesh').get_path_name()!=old['objectPath']:raise RuntimeError('User-modified or missing road actor preserved')
                previous[side]=found[0]
        source=(ROOT/'SourceAssets/Infrastructure/Bridge/bridge50m.glb').read_bytes()
        def height(x,north):
            # Landscape height samples are quantized to 1/16 metre. Bilinear interpolation
            # follows the imported grid, rather than unquantized analytic hills.
            step=48000/3024;gx=(x+24000)/step;gy=(-north+24000)/step;ix=math.floor(gx);iy=math.floor(gy);fx=gx-ix;fy=gy-iy
            def vertex(a,b):
                h=unreal.AnomaliaWorldImportLibrary.archipelago_height(-24000+a*step,24000-b*step)
                return math.floor(32768+h*16+.5)/16-2048
            return (vertex(ix,iy)*(1-fx)+vertex(ix+1,iy)*fx)*(1-fy)+(vertex(ix,iy+1)*(1-fx)+vertex(ix+1,iy+1)*fx)*fy
        placed=[]
        for name,x0,x1,end in [('West',13000.,13500.,13500.),('East',16000.,16500.,16000.)]:
            data,origin=build_road(height,x0,x1,end,unreal.AnomaliaWorldImportLibrary.archipelago_height(end,-9000)+.25,source)
            sha=hashlib.sha256(data).hexdigest();destination='/Game/Anomalia/Infrastructure/Roads/SM_Detroit'+name+'_'+sha[:12]
            if unreal.EditorAssetLibrary.does_asset_exist(destination):raise RuntimeError('Existing road asset preserved; inspect before reusing')
            staging=ROOT/'Saved/AnomaliaMigration'/('road-'+uuid.uuid4().hex);staging.mkdir(parents=True)
            file=staging/(name+'.glb');file.write_bytes(data)
            task=unreal.AssetImportTask();task.filename=str(file);task.destination_path='/Game/Anomalia/Infrastructure/Roads/Imports/Road_'+uuid.uuid4().hex;task.automated=True;task.replace_existing=False;task.save=True;task.async_=False
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);task.get_objects()
            meshes=[unreal.EditorAssetLibrary.load_asset(p) for p in unreal.EditorAssetLibrary.list_assets(task.destination_path,recursive=True,include_folder=False)]
            meshes=[m for m in meshes if isinstance(m,unreal.StaticMesh)]
            if len(meshes)!=1:raise RuntimeError('Expected one complete terrain road mesh')
            mesh=unreal.EditorAssetLibrary.duplicate_asset(meshes[0].get_path_name(),destination)
            mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
            if not unreal.EditorAssetLibrary.save_loaded_asset(mesh,only_if_is_dirty=False):raise RuntimeError('Road collision save failed')
            actor=previous.get(name) or actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(origin[0]*100,900000,origin[1]*100))
            if not actor:raise RuntimeError('Road actor creation failed')
            actor.tags=[unreal.Name(TAG)];actor.set_actor_label('ANOMALIA_DetroitRoad_'+name)
            comp=actor.get_component_by_class(unreal.StaticMeshComponent);comp.set_static_mesh(mesh);comp.set_collision_profile_name('BlockAll')
            placed.append(dict(side=name,lengthMeters=x1-x0,sourceSha256=sha,objectPath=mesh.get_path_name()))
        if not level.save_all_dirty_levels() or not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):raise RuntimeError('Road level save failed')
        result.update(state='PLACED_NOT_PLAYTESTED',roadCount=2,totalLengthMeters=1000,widthMeters=11,roads=placed,geometryVersion=2,legacyGeometryAndMarkerPreserved=LEGACY.exists())
        MARKER.parent.mkdir(parents=True,exist_ok=True);MARKER.write_text(json.dumps(result,indent=2)+'\n')
except Exception as error:
    result['error']=str(error);raise
finally:
    REPORT.parent.mkdir(parents=True,exist_ok=True);REPORT.write_text(json.dumps(result,indent=2)+'\n')
