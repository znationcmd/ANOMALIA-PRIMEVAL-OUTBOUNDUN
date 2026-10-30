"""Import original meshes without replacing existing art; build an independent review level."""
import hashlib,json,os,uuid
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve();BASE=ROOT/'SourceAssets/OriginalLot1'
OUT=Path(os.environ['ANOMALIA_LOT1_REPORT'])
report=dict(state='FAILED',sourceCommit=os.environ.get('GITHUB_SHA','manual'),models=[],drivingTested=False,animationsTested=False)
try:
 spec=json.loads((BASE/'manifest.json').read_text());tools=unreal.AssetToolsHelpers.get_asset_tools();loaded={}
 for item in spec['models']:
  source=BASE/item['file'];dest=item['objectPath']
  if source.resolve().parent!=BASE or hashlib.sha256(source.read_bytes()).hexdigest()!=item['sha256']:raise RuntimeError('Source identity mismatch')
  mesh=unreal.EditorAssetLibrary.load_asset(dest) if unreal.EditorAssetLibrary.does_asset_exist(dest) else None
  if mesh:
   if not isinstance(mesh,unreal.StaticMesh) or unreal.EditorAssetLibrary.get_metadata_tag(mesh,'AnomaliaZPrigimaliaOriginalLot1SHA')!=item['sha256']:raise RuntimeError('Existing unrelated mesh preserved: '+dest)
  else:
   staging='/Game/Anomalia/OriginalImports/Lot1_'+item['id']+'_'+uuid.uuid4().hex
   task=unreal.AssetImportTask();task.filename=str(source);task.destination_path=staging;task.automated=True;task.replace_existing=False;task.save=True;task.async_=False
   tools.import_asset_tasks([task]);task.get_objects()
   meshes=[unreal.EditorAssetLibrary.load_asset(p) for p in unreal.EditorAssetLibrary.list_assets(staging,recursive=True,include_folder=False)]
   meshes=[m for m in meshes if isinstance(m,unreal.StaticMesh)]
   if len(meshes)!=1:raise RuntimeError('Expected one assembled model: '+item['id'])
   mesh=unreal.EditorAssetLibrary.duplicate_asset(meshes[0].get_path_name(),dest)
   if not mesh:raise RuntimeError('Cannot save canonical mesh')
   unreal.EditorAssetLibrary.set_metadata_tag(mesh,'AnomaliaZPrigimaliaOriginalLot1SHA',item['sha256'])
   body=mesh.get_editor_property('body_setup')
   if not body:raise RuntimeError('Missing BodySetup')
   body.set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
   if not unreal.EditorAssetLibrary.save_loaded_asset(mesh,only_if_is_dirty=False):raise RuntimeError('Cannot save collision mesh')
  bounds=mesh.get_bounds();dims=[bounds.box_extent.x*2,bounds.box_extent.y*2,bounds.box_extent.z*2]
  expected=[item['dimensionsMetresYUp'][i]*100 for i in [0,2,1]]
  if any(abs(a-b)>3 for a,b in zip(dims,expected)):raise RuntimeError('Scale/axis mismatch: '+item['id']+' '+str(dims))
  mats=mesh.get_editor_property('static_materials')
  if not mats or any(not m.material_interface for m in mats):raise RuntimeError('Missing PBR material')
  if mesh.get_editor_property('body_setup').get_editor_property('collision_trace_flag')!=unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE:raise RuntimeError('Triangle collision not configured')
  loaded[item['id']]=mesh
  report['models'].append(dict(id=item['id'],objectPath=mesh.get_path_name(),dimensionsCm=dims,materials=len(mats),triangleCollisionConfigured=True,nativePresentationBound=False,state='IMPORTED_NOT_PLAYTESTED'))
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 vehicle=unreal.load_class(None,'/Script/AnomaliaZPrigimalia.AnomaliaZPrigimaliaVehiclePawn')
 for item in report['models']:
  if item['id'] not in ['quad','snowmobile','jetski','zodiac']:continue
  probe=actors.spawn_actor_from_class(vehicle,unreal.Vector(0,0,500),transient=True)
  try:
   if not probe.configure_vehicle(unreal.Name(item['id'])) or probe.get_editor_property('body').get_editor_property('static_mesh')!=loaded[item['id']]:raise RuntimeError('Native presentation binding failed')
   item['nativePresentationBound']=True
  finally:actors.destroy_actor(probe)
 package='/Game/Maps/ANOMALIA_AssetsShowcase_v1';level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 existing=unreal.EditorAssetLibrary.does_asset_exist(package)
 if existing:
  if not level.load_level(package):raise RuntimeError('Cannot open existing review map')
  if not any(a.get_actor_label()=='ANOMALIA_Lot1_OwnershipMarker' for a in actors.get_all_level_actors()):raise RuntimeError('Existing unowned review map preserved')
 else:
  if not level.new_level(package):raise RuntimeError('Cannot create separate review map')
  def place(name,cls,pos):
   a=actors.spawn_actor_from_class(cls,unreal.Vector(*pos));a.set_actor_label(name);a.tags=[unreal.Name('ANOMALIA_OriginalLot1')];return a
  place('ANOMALIA_Lot1_OwnershipMarker',unreal.Actor,(0,0,0))
  floor=place('ANOMALIA_Lot1_Ground',unreal.StaticMeshActor,(0,0,-30));c=floor.get_component_by_class(unreal.StaticMeshComponent);c.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'));floor.set_actor_scale3d(unreal.Vector(100,100,.4));c.set_collision_profile_name('BlockAll')
  positions={'hlm_8floors_v1':(-2400,-800,0),'beach_villa_pool_v1':(2500,1500,0),'quad':(-700,-700,0),'snowmobile':(0,-700,0),'jetski':(650,-700,0),'zodiac':(1300,-700,0),'coastal_house_v1':(-750,700,0),'garage_v1':(750,700,0)}
  for item in spec['models']:
   a=place('ANOMALIA_Lot1_'+item['id'],unreal.StaticMeshActor,positions[item['id']]);c=a.get_component_by_class(unreal.StaticMeshComponent);c.set_static_mesh(loaded[item['id']]);c.set_collision_profile_name('BlockAll')
  light=place('ANOMALIA_Lot1_Sun',unreal.DirectionalLight,(0,0,2000));light.set_actor_rotation(unreal.Rotator(pitch=-45,yaw=-40,roll=0),False)
  place('ANOMALIA_Lot1_Sky',unreal.SkyAtmosphere,(0,0,0));place('ANOMALIA_Lot1_Ambient',unreal.SkyLight,(0,0,500))
  place('ANOMALIA_Lot1_PlayerStart',unreal.PlayerStart,(0,-1300,120))
  if not level.save_current_level():raise RuntimeError('Cannot save review map')
 report.update(state='IMPORTED_AND_REVIEW_LEVEL_CREATED_NOT_PLAYTESTED',reviewMap=package,existingReviewMapPreserved=existing)
except Exception as error:
 report['error']=str(error);raise
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2)+'\n');unreal.log(json.dumps(report))
