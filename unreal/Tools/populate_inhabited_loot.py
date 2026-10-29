"""Generate loot defaults from collision-tested floors of actual saved houses.
Only explicit points accepted on a house mesh are written. No theoretical sites.
"""
import hashlib,json,math,os,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=Path("D:/ANOMALIA/StorageRecovery/inhabited-loot-placement.json")
MAP="/Game/Maps/ANOMALIA_Inhabited_v2"
def main():
    report=dict(state="STARTED",map=MAP,points=[],rejected=[],playtested=False)
    level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    lib=unreal.AnomaliaWorldImportLibrary
    def guidkey(actor):
        return "".join("%08x"%(v & 0xffffffff) for v in actor.get_actor_guid().to_tuple())
    def trace(world,x,y,z,actor):
        hit=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(x,y,z+140),unreal.Vector(x,y,z-30),
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[],unreal.DrawDebugTrace.NONE)
        if hit is None:return None
        values=hit.to_tuple()
        if not values[0] or values[1] or values[7].z<.9 or values[9]!=actor:return None
        point=values[5]
        block=unreal.SystemLibrary.box_trace_single(world,unreal.Vector(point.x,point.y,point.z+45),
            unreal.Vector(point.x,point.y,point.z+75),unreal.Vector(20,20,20),unreal.Rotator(),
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[],unreal.DrawDebugTrace.NONE)
        if block is not None and block.to_tuple()[0]:return None
        return [point.x,point.y,point.z+30]
    try:
        if not level.load_level(MAP):raise RuntimeError("Saved inhabited world absent")
        world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        desc=json.loads(lib.get_archipelago_actor_descriptors())
        if desc.get("state")!="COPIED_DESCRIPTOR_VALUES":raise RuntimeError("Unverified world descriptors")
        houses=[d for d in desc["actors"] if d.get("boundsValid") and
            d.get("nativeClass")=="/Script/Engine.StaticMeshActor" and
            d.get("label","").startswith("ANOMALIA_Inhabited1_")]
        if len(houses)<100:raise RuntimeError("Actual saved house population missing")
        selected=[]
        for site in lib.inhabited_settlement_sites():
            nearby=[d for d in houses if abs((d["boundsMinCm"][0]+d["boundsMaxCm"][0])/200-site.x)<420 and
                    abs(-(d["boundsMinCm"][1]+d["boundsMaxCm"][1])/200-site.y)<420]
            nearby.sort(key=lambda d:hashlib.sha256(d["guid"].encode()).hexdigest())
            selected.extend(nearby[:8])
        selected=list({d["guid"]:d for d in selected}.values())
        initial={guidkey(a) for a in actors.get_all_level_actors()}
        groups=[["canned_food"],["drinks"],["medical_supplies"],["tops","pants"],
                ["backpacks"],["tools"],["camping_storage"],["shoes_gloves"]]
        for begin in range(0,len(selected),24):
            batch=selected[begin:begin+24]
            guids=[d["guid"] for d in batch]
            if not lib.set_archipelago_actors_loaded(guids,True):raise RuntimeError("House streaming failed")
            try:
                loaded={guidkey(a):a for a in actors.get_all_level_actors()}
                for d in batch:
                    a=loaded.get(d["guid"].replace("-","").lower())
                    if a is None:
                        report["rejected"].append(dict(id=d["label"],reason="ACTOR_NOT_LOADED"));continue
                    base=a.get_actor_location();yaw=math.radians(a.get_actor_rotation().yaw)
                    pos=None
                    for dx,dy in ((150,150),(-150,150),(150,-150),(-150,-150),(250,250),(-250,-250)):
                        x=base.x+dx*math.cos(yaw)-dy*math.sin(yaw)
                        y=base.y+dx*math.sin(yaw)+dy*math.cos(yaw)
                        pos=trace(world,x,y,base.z,a)
                        if pos:break
                    if not pos:
                        report["rejected"].append(dict(id=d["label"],reason="NO_CLEAR_COLLIDING_FLOOR"));continue
                    ident="inhabited-"+hashlib.sha256(d["guid"].encode()).hexdigest()[:24]
                    report["points"].append(dict(id=ident,map="ANOMALIA_Inhabited_v2",buildingType="house",
                        x=pos[0],y=pos[1],z=pos[2],categories=groups[len(report["points"])%len(groups)]))
            finally:
                unload=[g for g in guids if g.replace("-","").lower() not in initial]
                if not lib.set_archipelago_actors_loaded(unload,False):raise RuntimeError("Could not restore house streaming")
        if not report["points"]:raise RuntimeError("No floor-tested loot points; original layout preserved")
        path=ROOT/"Content/Anomalia/Data/loot_spawns.json"
        original=path.read_bytes();layout=json.loads(original)
        byid={(p["map"],p["id"]):p for p in layout["spawns"]}
        for p in report["points"]:byid[(p["map"],p["id"])]=p
        if len(byid)>512:raise RuntimeError("Native point capacity exceeded; no layout written")
        layout["spawns"]=sorted(byid.values(),key=lambda p:(p["map"],p["id"]))
        encoded=(json.dumps(layout,indent=2)+"\n").encode()
        if len(encoded)>1024*1024:raise RuntimeError("Native file size limit exceeded")
        backup=path.with_name(path.name+"."+hashlib.sha256(original).hexdigest()[:12]+".bak")
        if not backup.exists():backup.write_bytes(original)
        tmp=path.with_suffix(".tmp");tmp.write_bytes(encoded);os.replace(tmp,path)
        report.update(state="FLOOR_TESTED_LOOT_LAYOUT_SAVED_NOT_PLAYTESTED",housesInSavedWorld=len(houses),
                      housesSampled=len(selected),totalPoints=len(layout["spawns"]),layout=str(path),
                      layoutSha256=hashlib.sha256(encoded).hexdigest())
    except Exception as error:
        report.update(state="FAILED",error=str(error),traceback=traceback.format_exc())
        raise
    finally:
        OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2),encoding="utf-8")
        unreal.log("ANOMALIA_WORLD_LOOT_RESULT="+json.dumps(report))

main()
