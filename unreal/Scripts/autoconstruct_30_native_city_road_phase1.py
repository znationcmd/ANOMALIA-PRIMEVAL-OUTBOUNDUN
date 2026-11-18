r"""Idempotent, additive real-asset native UE5 city/village and road authoring.

Operates on ONE explicitly allowlisted original native World Partition map per
invocation. Uses actual original ANOMALIA house/road meshes, no cube proxies.
Only saves if the physical terrain has both Landscape and collision components.
Terrain/actor grade and collision preflight run BEFORE touching an existing
world; no clearing, deleting, reimporting or resculpting original land.
One bounded batch per invocation; repeat until every planned locality is done.
"""
import hashlib,json,math,os,shutil,traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
ID=os.environ.get("ANOMALIA_AUTOBUILD_MAP_ID","")
MASTER=Path(os.environ.get("ANOMALIA_AUTOBUILD_MASTER_PLAN",""))
OUT=Path(os.environ.get("ANOMALIA_AUTOBUILD_NATIVE_REPORT",""))
MAX_SITES=int(os.environ.get("ANOMALIA_AUTOBUILD_SITE_LIMIT","2"))
MAX_ACTORS=int(os.environ.get("ANOMALIA_AUTOBUILD_ACTOR_LIMIT","150"))
PREFIX="ANOMALIA_AUTO30_V1_"
ASSETS={
 "wood":"/Game/Anomalia/InteractiveRealismReview_v1/wood_house_enterable/SM_wood_house_enterable",
 "coastal":"/Game/Anomalia/Buildings/Lot1/SM_coastal_house_v1",
 "garage":"/Game/Anomalia/Buildings/Lot1/SM_garage_v1",
 "apartment":"/Game/Anomalia/Buildings/Lot1/SM_hlm_8floors_v1",
 "residence":"/Game/Anomalia/Buildings/Expansion1/SM_residence_4floors",
 "townhouse":"/Game/Anomalia/Buildings/Expansion1/SM_townhouse",
 "hospital":"/Game/Anomalia/Buildings/Expansion1/SM_hospital",
 "police":"/Game/Anomalia/Buildings/Expansion1/SM_police_station",
 "barn":"/Game/Anomalia/Buildings/Expansion1/SM_farm_barn",
 "fire":"/Game/Anomalia/Buildings/Expansion1/SM_fire_station"
}
ROAD="/Game/Road/Kit_City_Road/SM_ROAD_19_10_0_0_road"
ORIGINAL_NATIVE_ID={
 "apocalyptic-outbreak-v1":"APOCALYPTIC_OUTBREAK",
 "morodenachtmerr-v1":"MOROEDENACHTMERR",
 "mokupunawai-v1":"MOKUPUNAWAI",
 "nasdaras-v1":"NASDARAS",
 "kiryumori-v1":"KIRYUMORI",
 "aranyapura-v1":"ARANYAPURA",
 "falc-v1":"FALC",
 "unknown-horror-x-v1":"UNKNOWN_HORROR_X",
 "konigsbruck-v1":"KONIGSBRUCK",
 "skjaeroyas-v1":"SKJAEROYAS",
 "valhalla-extinction-v1":"VALHALLA_EXTINCTION",
}
ORIGINAL_EXTRA_NATIVE={
 "karskov-v1":"KARSKOV","vorgrad-v1":"VORGRAD",
 "nemoris-v1":"NEMORIS","drakheim-v1":"DRAKHEIM",
 "yudinavia-v1":"YUDINAVIA","moscovie-v1":"MOSCOVIE",
 "corsivia-v1":"CORSIVIA","bot-sever-v1":"BOT_SEVER",
}
report={"state":"FAILED","mapId":ID,"sourceWorldModified":False,
        "existingRoadsDeleted":0,"existingBuildingsDeleted":0,
        "realBuildingsCreated":0,"realRoadMeshActorsCreated":0,
        "localitiesConstructed":0,"completedSiteIds":[],
        "rejectedSites":[],"roadMetresCovered":0.,
        "regionalLinksBuilt":0,"roadsConnectedAndDrivableTested":False,
        "completeInteriorsTested":False,"fullGamePlaytestPassed":False,
        "realTerrainCollisionVerified":False,"originalTerrainResculpted":False,
        "all30Completed":False}
def ground_from_world(world, east, north):
    start=unreal.Vector(east*100.,-north*100.,500000.)
    finish=unreal.Vector(east*100.,-north*100.,-200000.)
    hit=unreal.SystemLibrary.line_trace_single(world,start,finish,
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[],unreal.DrawDebugTrace.NONE,True)
    if not isinstance(hit,tuple) or not hit[0]:return None
    obj=hit[1]
    try:return float(obj.location.z)/100.
    except Exception:
        return None
def sampler_for_map(map_id,world):
    if map_id in ORIGINAL_NATIVE_ID:
        lib=getattr(unreal,"AnomaliaPrimevalElevenWorldLibrary",None)
        if lib and hasattr(lib,"named_world_height"):
            ident=ORIGINAL_NATIVE_ID[map_id]
            return lambda e,n:float(lib.named_world_height(ident,float(e),float(n)))
    native=getattr(unreal,"AnomaliaPrimevalWorldImportLibrary",None)
    if native:
        if map_id=="archipelago-v2" and hasattr(native,"archipelago_height"):
            return lambda e,n:float(native.archipelago_height(float(e),float(n)))
        if map_id=="inhabited-v2" and hasattr(native,"inhabited_archipelago_height"):
            return lambda e,n:float(native.inhabited_archipelago_height(float(e),float(n)))
        if map_id in ORIGINAL_EXTRA_NATIVE and hasattr(native,"named_world_height"):
            ident=ORIGINAL_EXTRA_NATIVE[map_id]
            return lambda e,n:float(native.named_world_height(ident,float(e),float(n)))
    # No made-up flat-world fallback: actual collision is the only permitted sample.
    return lambda e,n:ground_from_world(world,e,n)
def digest_file(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        while True:
            part=f.read(4*1024*1024)
            if not part:break
            h.update(part)
    return h.hexdigest()
def grade_ok(sampler,e,n,footprint=14.):
    try:
        val=sampler(e,n)
        if val is None or not math.isfinite(val) or not (5.<=val<=1900.):return None
        points=[sampler(e+dx,n+dy) for dx,dy in
            [(-footprint,-footprint),(-footprint,footprint),(footprint,-footprint),(footprint,footprint)]]
        if any(x is None or not math.isfinite(x) for x in points):return None
        if max([val]+points)-min([val]+points)>2.4:return None
        return val,max([val]+points)
    except Exception:return None
def saved_actor_labels(actors):
    labels=set()
    for a in actors.get_all_level_actors():
        try:labels.add(a.get_actor_label())
        except Exception:pass
    try:
        wp=unreal.WorldPartitionBlueprintLibrary
        for d in wp.get_actor_descs() or []:labels.add(str(d.label))
    except Exception:pass
    return labels
def looks_occupied(actors,ex,ny,radius=20.):
    for a in actors:
        if isinstance(a,unreal.LandscapeProxy):continue
        if isinstance(a,(unreal.DirectionalLight,unreal.SkyLight,unreal.SkyAtmosphere)):continue
        try:
            pos=a.get_actor_location()
            if math.hypot(float(pos.x)/100.-ex,-float(pos.y)/100.-ny)<radius:
                return True
        except Exception:pass
    return False
def place_mesh(sub,mesh,p,ident,road=False,scale=None,rot=None):
    actor=sub.spawn_actor_from_class(unreal.StaticMeshActor,p)
    if not actor:raise RuntimeError("Unreal actor spawn failed")
    actor.set_actor_label(ident)
    actor.tags=[unreal.Name("ANOMALIA_AUTO30_GENERATED_V1"),unreal.Name(ID.replace("-","_")),
                unreal.Name("AUTO30_NATIVE_ASPHALT" if road else "AUTO30_REAL_BUILDING")]
    comp=actor.get_component_by_class(unreal.StaticMeshComponent)
    if not comp or not comp.set_static_mesh(mesh):
        raise RuntimeError("Original verified StaticMesh assignment failed")
    comp.set_collision_profile_name("BlockAll")
    if scale is not None:actor.set_actor_scale3d(unreal.Vector(*scale))
    if rot is not None:actor.set_actor_rotation(unreal.Rotator(*rot),False)
    return actor
try:
    if ROOT!=Path(r"D:\ANOMALIA\unreal").resolve():raise RuntimeError("Wrong original game project root")
    if not MASTER.is_file():raise RuntimeError("Original 30-map masterplan missing")
    if not ID or not OUT or MAX_SITES not in (1,2,3,4) or not 16<=MAX_ACTORS<=400:
        raise RuntimeError("Invalid explicit map ID / output / safe batch limits")
    doc=json.loads(MASTER.read_text(encoding="utf-8-sig"))
    if doc.get("levelCount")!=30 or doc.get("generationVersion")!="ANOMALIA-AUTO30-ORIGINAL-2026-V1":
        raise RuntimeError("Wrong 30-map generation plan")
    rows=[m for m in doc["maps"] if m["id"]==ID]
    if len(rows)!=1:raise RuntimeError("Unregistered auto-construction world")
    mapdata=rows[0]
    if not mapdata.get("worldPackage","").startswith("/Game/Maps/"):
        raise RuntimeError("Native target World Partition package missing")
    if not (ROOT/"Content/Maps/ANOMALIA_Archipelago_v2.umap").is_file():
        raise RuntimeError("Original SKARVIK map is missing")
    filename=ROOT/"Content"/("Maps/"+mapdata["worldPackage"].split("/")[-1]+".umap")
    if not filename.is_file():raise RuntimeError("Target real .umap not found")
    realmesh={}
    for key,path in dict(ASSETS,road=ROAD).items():
        m=unreal.EditorAssetLibrary.load_asset(path)
        if not isinstance(m,unreal.StaticMesh):
            raise RuntimeError("No verified genuine static mesh "+key+": "+path)
        b=m.get_bounds()
        w,h=2*float(b.box_extent.x)/100.,2*float(b.box_extent.y)/100.
        if key=="road":
            if not 17<w<23 or not 5<h<15:raise RuntimeError("Road mesh size not verified")
        elif not (2<w<80 and 2<h<80):
            raise RuntimeError("Building mesh source dimensions not valid: "+key)
        realmesh[key]=(m,b)
    lv=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    if not lv or not actors or not editor or not lv.load_level(mapdata["worldPackage"]):
        raise RuntimeError("Real existing World Partition level failed to open")
    world=editor.get_editor_world()
    if not world or world.get_outermost().get_name()!=mapdata["worldPackage"]:
        raise RuntimeError("Unexpected editor world after load")
    loaded=actors.get_all_level_actors()
    landscapes=[a for a in loaded if isinstance(a,unreal.LandscapeProxy)]
    report["landscapeCount"]=len(landscapes)
    terrainComponents=0;terrainCollisions=0
    for land in landscapes:
        terrainComponents+=len(land.get_components_by_class(unreal.LandscapeComponent))
        terrainCollisions+=len(land.get_components_by_class(unreal.LandscapeHeightfieldCollisionComponent))
    report["landscapeComponents"]=terrainComponents
    report["landscapeCollisionComponents"]=terrainCollisions
    if not terrainComponents or not terrainCollisions:
        raise RuntimeError("Native Landscape terrain/collision not loaded after reopen; refuse floating roads/buildings")
    report["realTerrainCollisionVerified"]=True
    h=sampler_for_map(ID,world)
    existingLabels=saved_actor_labels(actors)
    generatedLabels={x for x in existingLabels if x.startswith(PREFIX+ID.replace("-","_")+"_")}
    if mapdata.get("requestedLocalities")==0:
        report["state"]="SPECIAL_GAME_MODE_PRESERVED_NO_CIVILIAN_TOWNS"
    elif len(generatedLabels)>=MAX_ACTORS*5:
        report["state"]="EXISTING_AUTOCONSTRUCTION_BATCHES_PRESERVED"
    else:
        targetSites=[]
        for s in mapdata["sites"]:
            prefix=PREFIX+ID.replace("-","_")+"_"+s["id"]+"_"
            if any(label.startswith(prefix) for label in existingLabels):continue
            if len(targetSites)>=MAX_SITES:break
            # Test all terrain and existing actors BEFORE modifying the world.
            candidate=None
            for radial in (0.,170.,340.,520.,760.,1050.):
                for angle in range(0,360,30):
                    e=s["eastMeters"]+radial*math.cos(math.radians(angle))
                    n=s["northMeters"]+radial*math.sin(math.radians(angle))
                    if abs(e)>mapdata["worldSizeMeters"][0]*.47 or abs(n)>mapdata["worldSizeMeters"][1]*.47:continue
                    if not grade_ok(h,e,n,20.):continue
                    if looks_occupied(loaded,e,n,135.):continue
                    candidate=(e,n);break
                if candidate:break
            if candidate:
                targetSites.append((s,candidate))
            else:
                report["rejectedSites"].append({"id":s["id"],"reason":"no-dry-flat-unoccupied-terrain"})
        if not targetSites:
            report["state"]="NO_SAFE_BUILDABLE_CENTRES"
        else:
            # Back up exact original .umap before any actor is created. Original
            # existing actor data is never deleted/overwritten.
            backup=OUT.parent/"pre-autoconstruction-original-map.umap"
            backup.parent.mkdir(parents=True,exist_ok=True)
            srcSha=digest_file(filename)
            if backup.exists():
                if digest_file(backup)!=srcSha:
                    raise RuntimeError("Existing safety backup does not match original map")
            else:
                shutil.copy2(filename,backup)
                if digest_file(backup)!=srcSha:raise RuntimeError("Original world backup checksum differs")
            report["backup"]=str(backup)
            before_buildings=0;before_roads=0
            maxRoads=min(90,MAX_ACTORS//2)
            for s,(e0,n0) in targetSites:
                prefix=PREFIX+ID.replace("-","_")+"_"+s["id"]+"_"
                count=0
                # The local road runs East-West through the center. Buildings
                # occupy separate, spaced north/south parcels.
                widths=[float(realmesh[key][1].box_extent.x)*2/100. for key in s["meshPalette"]]
                for j in range(s["buildingTarget"]):
                    if report["realBuildingsCreated"]+report["realRoadMeshActorsCreated"]>=MAX_ACTORS:break
                    group=s["meshPalette"][j%len(s["meshPalette"])]
                    obj,b=realmesh[group]
                    column=j%6;row=j//6
                    de=(column-2.5)*s["plotSpacingMeters"]
                    dn=(1 if row%2 else -1)*(65.+(row//2)*s["plotSpacingMeters"])
                    x,y=e0+de,n0+dn
                    footprint=max(10.,float(b.box_extent.x)/100.,float(b.box_extent.y)/100.)
                    g=grade_ok(h,x,y,footprint)
                    if not g or looks_occupied(loaded,x,y,footprint+8.):continue
                    z,high=g
                    bottom=float(b.origin.z-b.box_extent.z)
                    pos=unreal.Vector(x*100.,-y*100.,high*100.-bottom+2.)
                    label=prefix+"BUILDING_"+str(j).zfill(3)
                    if label in existingLabels:continue
                    actor=place_mesh(actors,obj,pos,label)
                    loaded.append(actor)
                    count+=1;report["realBuildingsCreated"]+=1
                    existingLabels.add(label)
                # Genuine road static meshes follow native relief; only short
                # smooth dry segments are saved. No fabricated bridge/causeway.
                built=0
                road,bounds=realmesh["road"]
                widthMeters=2*float(bounds.box_extent.x)/100.
                depthMeters=2*float(bounds.box_extent.y)/100.
                for k in range(-9,9):
                    if report["realRoadMeshActorsCreated"]>=maxRoads:break
                    east=e0+(k+.5)*19.
                    north=n0
                    if looks_occupied(loaded,east,north,12.):continue
                    p0=h(east-9.5,north);p1=h(east+9.5,north);mid=h(east,north)
                    if any(v is None or not math.isfinite(v) for v in (p0,p1,mid)):continue
                    if min(p0,p1,mid)<5 or abs(p1-p0)>1.55 or abs((p0+p1)/2.-mid)>.7:continue
                    sy=8.5/depthMeters
                    pitch=-math.degrees(math.atan2(p1-p0,19.))
                    roadLabel=prefix+"REAL_ROAD_"+str(k+9).zfill(3)
                    if roadLabel in existingLabels:continue
                    pos=unreal.Vector(east*100.,-north*100.,mid*100.+9.)
                    actor=place_mesh(actors,road,pos,roadLabel,True,(19./widthMeters,sy,1.),(pitch,0.,0.))
                    loaded.append(actor)
                    built+=1;report["realRoadMeshActorsCreated"]+=1
                    report["roadMetresCovered"]+=19.
                    existingLabels.add(roadLabel)
                if count>0:
                    report["localitiesConstructed"]+=1
                    report["completedSiteIds"].append(s["id"])
                else:
                    report["rejectedSites"].append({"id":s["id"],"reason":"no-safe-building-parcels"})
            if not report["realBuildingsCreated"] or not report["realRoadMeshActorsCreated"]:
                raise RuntimeError("No safe native building/road actors created; refusing empty terrain save")
            if not lv.save_all_dirty_levels():
                raise RuntimeError("Could not save native World Partition map with authentic assets")
            if not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
                raise RuntimeError("Could not save native external actor packages")
            report["sourceWorldModified"]=True
            report["savedWorldPackage"]=mapdata["worldPackage"]
            report["state"]="PARTIAL_NATIVE_REAL_ASSETS_SAVED_UNPLAYTESTED"
except Exception as e:
    report["error"]=str(e)
    report["traceback"]=traceback.format_exc()
    unreal.log_error("ANOMALIA_AUTO30_WORLD_BUILD_ERROR "+str(e))
finally:
    if OUT:
        OUT.parent.mkdir(parents=True,exist_ok=True)
        OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    unreal.log("ANOMALIA_AUTO30_WORLD_BUILD_REPORT "+json.dumps({k:v for k,v in report.items() if k!="traceback"},ensure_ascii=False))
