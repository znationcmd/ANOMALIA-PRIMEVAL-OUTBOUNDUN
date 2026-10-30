"""Add *real imported, verified* house scans and plants to one existing new world.

Only a review-quality additive authoring pass: no new terrain, replacement,
landscape sculpt, interiors, roads, network or playable-game claims.
A separately verified immutable backup is required; partial work stops safely.
"""
import hashlib,importlib.util,json,math,os,traceback
from pathlib import Path
import unreal

NAME=os.environ.get("PRIGIMALIA_POPULATE_NAME","")
MODE=os.environ.get("PRIGIMALIA_POPULATE_MODE","create")
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=Path(os.environ.get("PRIGIMALIA_POPULATE_REPORT",str(ROOT/"Saved/FourWorlds"/("population-"+(NAME or "invalid")+".json"))))
PACKAGE="/Game/Maps/PRIGIMALIA_"+NAME
OWNER="PRIGIMALIA_"+NAME+"_AutoPopulation_v1"
report=dict(state="FAILED",map=NAME,mapPackage=PACKAGE,sourceCommit=os.environ.get("GITHUB_SHA"),
            terrainModified=False,artistActorsModified=False,oldWorldsModified=False,
            interiorsReady=False,roadsBuilt=False,fullMapCompleted=False,
            playtested=False,photorealismValidated=False)

def get_module(name,file):
 spec=importlib.util.spec_from_file_location(name,file)
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 return mod

def sha256(path):
 h=hashlib.sha256()
 with path.open("rb") as stream:
  for block in iter(lambda:stream.read(1024*1024),b""):h.update(block)
 return h.hexdigest()

def models():
 catalogue={}
 for base,tag in (("ResidentialPhotogrammetryPrepared_v1","AnomaliaZPrigimaliaWorldFeatureSha256"),
                  ("RealismValidation_v2","AnomaliaZPrigimaliaRealismSha256")):
  path=ROOT/"SourceAssets"/base
  manifest=json.loads((path/"manifest.json").read_text(encoding="utf-8"))
  for entry in manifest["models"]:
   ident=entry["id"]
   if ident not in ("country_house_scan","abandoned_brick_house_scan","island_tree_02","rock_moss_set_01"):continue
   file=(path/entry["file"]).resolve()
   if not file.is_relative_to(path.resolve()) or sha256(file)!=entry["sha256"]:
    raise RuntimeError("Model source checksum failed: "+ident)
   suffix="" if base.startswith("Residential") else "_r2"
   mesh=unreal.load_asset(entry["objectPath"]+suffix)
   if not isinstance(mesh,unreal.StaticMesh) or unreal.EditorAssetLibrary.get_metadata_tag(mesh,tag)!=entry["sha256"]:
    raise RuntimeError("Only imported source-verified 3D meshes accepted: "+ident)
   materials=mesh.get_editor_property("static_materials")
   if not materials or any(not m.material_interface for m in materials):
    raise RuntimeError("Real materials missing: "+ident)
   catalogue[ident]=mesh
 if set(catalogue)!={"country_house_scan","abandoned_brick_house_scan","island_tree_02","rock_moss_set_01"}:
  raise RuntimeError("Four verified pre-imported models required; no fake shapes allowed")
 return catalogue

def transform(mesh,item,kind):
 b=mesh.get_bounds();origin=b.origin;extent=b.box_extent
 if min(extent.x,extent.y,extent.z)<=0:raise RuntimeError("Invalid mesh bounds")
 if kind=="house":
  # Scans fit within reserved 42 m street-grid parcels with room for walkways.
  scale=min(25*100/(2*extent.x),25*100/(2*extent.y),14*100/(2*extent.z))
  if not .0001<scale<1000:raise RuntimeError("Uncalibrated building mesh scale")
  yaw=item["yaw"];t=math.radians(yaw);c,s=math.cos(t),math.sin(t)
  ox=(c*origin.x-s*origin.y)*scale;oy=(s*origin.x+c*origin.y)*scale
  location=[item["east"]*100-ox,-item["north"]*100-oy,
            item["height"]*100-(origin.z-extent.z)*scale-8]
  return unreal.Transform(location=unreal.Vector(*location),
                          rotation=unreal.Rotator(yaw=yaw),
                          scale=unreal.Vector(scale,scale,scale))
 # Native-compatible foliage and rock instancing (review-only).
 scale=item["scale"]
 return unreal.Transform(location=unreal.Vector(item["east"]*100,-item["north"]*100,item["height"]*100),
                         rotation=unreal.Rotator(yaw=item["yaw"]),
                         scale=unreal.Vector(scale,scale,scale))

def run():
 if NAME not in ("KARSKOV","VORGRAD","NEMORIS","DRAKHEIM"):
  raise RuntimeError("Unrecognised map")
 if MODE not in ("create","verify"):raise RuntimeError("Invalid mode")
 mapfile=ROOT/"Content/Maps"/("PRIGIMALIA_"+NAME+".umap")
 if not mapfile.is_file():raise RuntimeError("Native real .umap is missing")
 marker=ROOT/"Saved/FourWorlds"/("population-"+NAME+"-complete.json")
 plan_path=marker.with_name("population-"+NAME+"-plan.json")
 if MODE=="create":
  backup=Path(os.environ["PRIGIMALIA_POPULATE_BACKUP"]).resolve()
  proof=json.loads(backup.read_text(encoding="utf-8"))
  if proof.get("map")!=NAME or proof.get("verified") is not True:
   raise RuntimeError("Verified pre-authoring native map snapshot required")
  zip_path=Path(proof["archive"])
  if not zip_path.is_file() or sha256(zip_path)!=proof["sha256"]:
   raise RuntimeError("Immutable backup checksum mismatch")
  if marker.exists() or plan_path.exists():
   raise RuntimeError("Previous population state exists: never overwrite or resume unsafely")
 elif not marker.is_file() or not plan_path.is_file():
  raise RuntimeError("No completed population ownership record for independent verification")
 level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 if not level.load_level(PACKAGE):raise RuntimeError("Native map refused to reopen")
 present=actors.get_all_level_actors()
 ownership=[a for a in present if OWNER in {str(t) for t in a.tags}]
 if MODE=="create" and ownership:
  raise RuntimeError("Partial owned population already present; do not duplicate")
 if not any(isinstance(a,unreal.LandscapeProxy) for a in present):
  raise RuntimeError("Cannot author content without the actual landscape")
 height=lambda e,n:unreal.AnomaliaZPrigimaliaWorldImportLibrary.named_world_height(NAME,e,n)
 layout=get_module("original_four_world_layout",ROOT/"Scripts/four_world_layout.py")
 if MODE=="create":
  plan=layout.plan(NAME,height)
  if len(plan["sites"])<5 or len(plan["buildings"])<180 or len(plan["vegetation"])<50:
   raise RuntimeError("Incomplete terrain-safe auto-building plan")
  raw=json.dumps(plan,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
  plan_sha=hashlib.sha256(raw).hexdigest()
  outplan=OUT.with_name("proposed-population.json")
  outplan.parent.mkdir(parents=True,exist_ok=True)
  with outplan.open("xb") as stream:stream.write(raw)
 else:
  raw=plan_path.read_bytes()
  plan_sha=sha256(plan_path)
  ownership_info=json.loads(marker.read_text(encoding="utf-8"))
  if ownership_info.get("planSha256")!=plan_sha or ownership_info.get("map")!=NAME:
   raise RuntimeError("Saved authored population plan not verified")
  plan=json.loads(raw)
 mesh_map=models()
 labels=set()
 for item in plan["buildings"]:
  label=OWNER+"_Building_"+item["id"]
  if label in labels:raise RuntimeError("Duplicate house identity")
  labels.add(label)
 clusters={}
 for item in plan["vegetation"]:
  cx,cy=math.floor(item["east"]/1000),math.floor(item["north"]/1000)
  key=(item["kind"],cx,cy);clusters.setdefault(key,[]).append(item)
 for model,cx,cy in clusters:
  label=OWNER+"_HISM_"+model+"_"+str(cx)+"_"+str(cy)
  if label in labels:raise RuntimeError("Duplicate HISM cluster identity")
  labels.add(label)
 if MODE=="verify":
  existing={a.get_actor_label():a for a in present if OWNER in {str(t) for t in a.tags}}
  if set(existing)!=labels:raise RuntimeError("Saved owned actors missing or duplicated")
  for item in plan["buildings"]:
   a=existing[OWNER+"_Building_"+item["id"]]
   if not isinstance(a,unreal.StaticMeshActor) or a.static_mesh_component.get_editor_property("static_mesh")!=mesh_map[item["kind"]]:
    raise RuntimeError("Owned building mesh changed")
  for (model,cx,cy),items in clusters.items():
   a=existing[OWNER+"_HISM_"+model+"_"+str(cx)+"_"+str(cy)]
   if a.get_editor_property("instances").get_instance_count()!=len(items):
    raise RuntimeError("Foliage cluster count changed")
  report.update(state="POPULATION_REOPENED_AND_VERIFIED_NOT_PLAYTESTED",
                houses=len(plan["buildings"]),plants=len(plan["vegetation"]),
                sites=len(plan["sites"]),foliageClusters=len(clusters),planSha256=plan_sha)
  return
 cluster_class=unreal.load_class(None,"/Script/AnomaliaZPrigimalia.AnomaliaZPrigimaliaSceneryCluster")
 if not cluster_class:raise RuntimeError("Compiled HISM scenery cluster required")
 # Stage only new actors; existing terrain, lights and user actors are never modified.
 packages={}
 def track(actor):
  p=actor.get_outermost()
  pkg=p.get_name()
  if pkg!=PACKAGE and not pkg.startswith("/Game/__ExternalActors__/Maps/PRIGIMALIA_"+NAME+"/"):
   raise RuntimeError("Refusing unrelated map package: "+pkg)
  packages[pkg]=p
 for item in plan["buildings"]:
  mesh=mesh_map[item["kind"]]
  t=transform(mesh,item,"house")
  actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,t.translation)
  if not actor:raise RuntimeError("Building actor spawn failed")
  actor.set_actor_label(OWNER+"_Building_"+item["id"])
  actor.tags=[unreal.Name(OWNER),unreal.Name("PRIGIMALIA_Plan_"+plan_sha[:16])]
  actor.set_editor_property("is_spatially_loaded",True)
  actor.static_mesh_component.set_static_mesh(mesh)
  actor.set_actor_rotation(unreal.Rotator(yaw=item["yaw"]),False)
  actor.set_actor_scale3d(t.scale3d)
  actor.static_mesh_component.set_collision_profile_name("BlockAll")
  track(actor)
 for (model,cx,cy),items in sorted(clusters.items()):
  actor=actors.spawn_actor_from_class(cluster_class,unreal.Vector((cx+.5)*100000,(-cy-.5)*100000,0))
  if not actor:raise RuntimeError("HISM cluster failed")
  actor.set_actor_label(OWNER+"_HISM_"+model+"_"+str(cx)+"_"+str(cy))
  actor.tags=[unreal.Name(OWNER),unreal.Name("PRIGIMALIA_Plan_"+plan_sha[:16])]
  actor.set_editor_property("is_spatially_loaded",True)
  comp=actor.get_editor_property("instances")
  comp.set_static_mesh(mesh_map[model])
  for item in items:
   if comp.add_instance(transform(mesh_map[model],item,"plant"),world_space=True)<0:
    raise RuntimeError("Could not add real 3D vegetation")
  track(actor)
 if not unreal.EditorLoadingAndSavingUtils.save_packages(list(packages.values()),False):
  raise RuntimeError("Native external actor package save failed")
 marker.parent.mkdir(parents=True,exist_ok=True)
 with plan_path.open("xb") as stream:stream.write(raw)
 with marker.open("x",encoding="utf-8") as stream:
  json.dump(dict(map=NAME,mapPackage=PACKAGE,planSha256=plan_sha,sourceCommit=report["sourceCommit"],
                 houses=len(plan["buildings"]),plants=len(plan["vegetation"]),
                 actorCount=len(labels),assets=list(mesh_map)),stream,indent=2)
 report.update(state="AUTO_POPULATION_SAVED_REQUIRES_INDEPENDENT_REOPEN",
               houses=len(plan["buildings"]),plants=len(plan["vegetation"]),
               sites=len(plan["sites"]),foliageClusters=len(clusters),planSha256=plan_sha,
               assetReviewRequired=True,only3DImportedAssets=True)

try:
 run()
except Exception as error:
 report["error"]=str(error);report["traceback"]=traceback.format_exc()
 raise
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
