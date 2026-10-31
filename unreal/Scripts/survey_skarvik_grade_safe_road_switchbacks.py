"""Survey grade-safe switchback alternatives for SKARVIK's 182 remaining broken road tiles.
Read-only UE 5.8 height sampler + 20m grid A*; do not touch Landscape or saved roads.
A route is only a proposed alignment until physical collision/SM5 drive tests pass.
"""
from pathlib import Path
import os,json,math,hashlib,heapq,traceback
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=Path(os.environ["SKARVIK_SWITCHBACK_SURVEY_REPORT"])
PLAN=Path(os.environ["SKARVIK_SWITCHBACK_MASTERPLAN"])
PKG="/Game/Maps/PRIGIMALIA_SKARVIK_GRADED_v2"
TARGET=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap"
ORIGINAL=Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap")
ROADIDS=("SK-RX-008","SK-RX-009","SK-RX-016","SK-RX-031","SK-RX-047",
         "SK-RX-051","SK-RX-054","SK-RX-063","SK-RX-094","SK-RX-097",
         "SK-RX-122","SK-RX-181","SK-RX-196","SK-RX-198","SK-RX-201")
report={"state":"FAILED","readOnly":True,"realAsphaltActorsAdded":0,
 "landscapeTerrainModified":False,"bigCityModified":False,"originalDModified":False,
 "terrainGradeSurveyed":False,"bridgeCulvertWaterCrossingsVerified":False,
 "SM5VehicleDrivingVerified":False,"detourGroups":[]}
try:
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper() or (
  ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
  raise RuntimeError("Incorrect stage")
 for p in (TARGET,ORIGINAL):
  if not p.is_file():raise RuntimeError("Missing source world "+str(p))
 before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (TARGET,ORIGINAL)}
 source=json.loads(PLAN.read_text(encoding="utf-8"))
 roads={x["id"]:x for x in source["roads"] if x.get("id") in ROADIDS}
 if len(roads)!=len(ROADIDS):raise RuntimeError("Missing gap route id")
 levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 if not levels.load_level(PKG):raise RuntimeError("Graded world did not open")
 descs=unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or []
 labels={str(d.label) for d in descs}
 if sum(l.startswith("SKARVIK_GRADED_SITE_") for l in labels)!=1039:raise RuntimeError("Saved 3D sites missing")
 if sum(l.startswith("SKARVIK_CONTINUITY_PATCH_V1_") for l in labels)!=375:raise RuntimeError("Previous 375 safe road repairs not present")
 library=unreal.AnomaliaZPrigimaliaWorldImportLibrary
 def height(p):
  z=float(library.skarvik_graded_height(p[0]*1000.,p[1]*1000.))
  if not math.isfinite(z):raise RuntimeError("Non-finite landscape grade")
  return z
 centers=[(x["eastKm"],x["northKm"],x["footprintKm"][0]/2+.025,x["footprintKm"][1]/2+.025) for x in source["settlements"]]
 def townclear(p):
  e,n=p
  if not -23.85<e<23.85 or not -23.85<n<23.85:return False
  return all(not(abs(e-cx)<w and abs(n-cy)<h) for cx,cy,w,h in centers)
 # Deterministic grid A*, bounded to a 350m corridor around each missing run.
 # Grid side fixed 20m, eight neighbors; cap search per gap for reproducibility.
 step=.020
 directions=((1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1),(0,-1),(1,-1))
 def propose(start,end,route_id,group_id):
  width=max(0.33,min(0.80,math.hypot(end[0]-start[0],end[1]-start[1])*.55))
  lo=(min(start[0],end[0])-width,min(start[1],end[1])-width)
  hi=(max(start[0],end[0])+width,max(start[1],end[1])+width)
  nx=int(math.ceil((hi[0]-lo[0])/step))+1
  ny=int(math.ceil((hi[1]-lo[1])/step))+1
  if nx*ny>25000:return None,"grid-too-large",0
  def ix(p):return (max(0,min(nx-1,round((p[0]-lo[0])/step))),max(0,min(ny-1,round((p[1]-lo[1])/step))))
  def xy(a):return (lo[0]+a[0]*step,lo[1]+a[1]*step)
  orig=ix(start);dest=ix(end)
  valid={};hs={}
  def ok(a):
   if a in valid:return valid[a]
   p=xy(a);valid[a]=townclear(p)
   return valid[a]
  def h(a):
   if a not in hs:hs[a]=height(xy(a))
   return hs[a]
  def edge(a,b):
   if not ok(b):return None
   x=xy(a);y=xy(b)
   dist=math.hypot((y[0]-x[0])*1000,(y[1]-x[1])*1000)
   if dist<1:return None
   slope=abs(h(a)-h(b))/dist
   if slope>.145:return None
   mid=((x[0]+y[0])/2,(x[1]+y[1])/2)
   if not townclear(mid):return None
   if abs(height(mid)-(h(a)+h(b))/2)>.65:return None
   ux=(y[0]-x[0])*1000/dist;uy=(y[1]-x[1])*1000/dist
   orth=(-uy*.002,ux*.002)
   if abs(height((mid[0]+orth[0],mid[1]+orth[1]))-height((mid[0]-orth[0],mid[1]-orth[1])))>.95:
    return None
   return dist*(1.0+2.0*slope*slope)
  if not ok(orig) or not ok(dest):return None,"terminal-town-or-edge",0
  Q=[(0,orig,-1)]
  distances={(orig,-1):0}
  back={}
  visited=0;win=None
  while Q and visited<35000:
   prio,node,prev_dir=heapq.heappop(Q)
   state=(node,prev_dir)
   cost=distances[state]
   if prio>cost+math.hypot((xy(node)[0]-end[0])*1000,(xy(node)[1]-end[1])*1000)+1.0:
    continue
   visited+=1
   if node==dest:win=state;break
   for direction,(dx,dy) in enumerate(directions):
    b=(node[0]+dx,node[1]+dy)
    if b[0]<0 or b[0]>=nx or b[1]<0 or b[1]>=ny:continue
    w=edge(node,b)
    if w is None:continue
    turn=0.0 if prev_dir<0 else min(abs(direction-prev_dir),8-abs(direction-prev_dir))
    if turn>=3:continue
    new=cost+w+turn*3.0
    nxt=(b,direction)
    if new>=distances.get(nxt,float("inf")):continue
    distances[nxt]=new;back[nxt]=state
    heuristic=math.hypot((xy(b)[0]-end[0])*1000,(xy(b)[1]-end[1])*1000)
    heapq.heappush(Q,(new+heuristic,b,direction))
  if win is None:return None,"grade-safe-path-not-found",visited
  nodes=[]
  node=win
  while node in back:
   nodes.append(xy(node[0]));node=back[node]
  nodes.append(xy(orig));nodes=list(reversed(nodes))
  # Keep raw 20m-step centerline instead of smoothing through unsurveyed terrain.
  nodepath=[list(map(lambda x:round(x,5),start))]+[list(map(lambda x:round(x,5),p)) for p in nodes[1:-1]]+[list(map(lambda x:round(x,5),end))]
  dist=sum(math.hypot((b[0]-a[0])*1000,(b[1]-a[1])*1000) for a,b in zip(nodepath,nodepath[1:]))
  if dist>6*math.hypot((end[0]-start[0])*1000,(end[1]-start[1])*1000):
   return None,"detour-longer-than-sixfold",visited
  return {"route":route_id,"group":group_id,"sourceStartKm":list(start),
          "sourceEndKm":list(end),"detourCenterlineKm":nodepath,
          "estimatedRoadMetres":round(dist,1),"maxDesignedLongitudinalGrade":.145,
          "status":"PROPOSED_NON_NATIVE_ALIGNMENT_NOT_VALIDATED_OR_DRIVEN"},None,visited
 for roadid in ROADIDS:
  road=roads[roadid]
  if roadid=="SK-RX-196":continue
  candidates=[]
  for a,b in zip(road["waypointsKm"],road["waypointsKm"][1:]):
   length=math.hypot((b[0]-a[0])*1000,(b[1]-a[1])*1000)
   if length<12:continue
   count=int(math.ceil(length/19))
   for j in range(count):
    t0=j/count;t1=(j+1)/count
    p=(a[0]+(b[0]-a[0])*t0,a[1]+(b[1]-a[1])*t0)
    q=(a[0]+(b[0]-a[0])*t1,a[1]+(b[1]-a[1])*t1)
    candidates.append((p,q))
  pref=next((x for x in ("SKARVIK_EXPANSION_ROAD_","SKARVIK_EXPANSION_B2_ROAD_",
                         "SKARVIK_EXPANSION_C3_ROAD_") if
             any(l.startswith(x+roadid+"_") for l in labels)),None)
  if not pref:continue
  gaps=[]
  for i,(a,b) in enumerate(candidates):
   orig=pref+roadid+"_"+str(i)
   patched="SKARVIK_CONTINUITY_PATCH_V1_"+roadid+"_"+str(i)+"_"
   if orig not in labels and not any(l.startswith(patched) for l in labels):gaps.append(i)
  if not gaps:continue
  runs=[]
  current=[gaps[0]]
  for g in gaps[1:]:
   if g==current[-1]+1:current.append(g)
   else:runs.append(current);current=[g]
  runs.append(current)
  for groupid,run in enumerate(runs):
   if len(run)>45:
    report["detourGroups"].append({"route":roadid,"group":groupid,"state":"LARGE_GAP_REQUIRES_MANUAL_EARTHWORK","baseTileCount":len(run)})
    continue
   first,last=run[0],run[-1]
   proposal,error,visited=propose(candidates[first][0],candidates[last][1],roadid,groupid)
   report["detourGroups"].append(proposal if proposal else {
       "route":roadid,"group":groupid,"state":"CANNOT_AUTO_REROUTE","reason":error,
       "baseTileCount":len(run),"nodesVisited":visited})
 report["terrainGradeSurveyed"]=True
 report["proposedDetours"]=sum("detourCenterlineKm" in d for d in report["detourGroups"])
 report["unresolvedDetourGroups"]=len(report["detourGroups"])-report["proposedDetours"]
 for file in (TARGET,ORIGINAL):
  if hashlib.sha256(file.read_bytes()).hexdigest()!=before[str(file)]:
   raise RuntimeError("Read-only A* survey changed a protected map")
 report["state"]="SKARVIK_GRADE_SAFE_ROAD_SWITCHBACKS_SURVEYED_WITHOUT_MODIFYING_TERRAIN"
 unreal.log("SKARVIK_ROAD_SWITCHBACK_SURVEY_PROPOSALS="+str(report["proposedDetours"]))
except Exception as e:
 report["error"]=str(e);report["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_ROAD_SWITCHBACK_SURVEY_FAILED="+str(e))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
