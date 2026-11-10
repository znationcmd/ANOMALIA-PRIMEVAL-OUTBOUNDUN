"""Read-only 48km SKARVIK road proposal planner based on authentic C++ 7-island grid.

Original 125 settlements / 382 roads preserved. Inaccessible dry-land
links are reported for bridge/ferry review, NEVER filled across the sea.
Protect full 4x4 km City Sample footprint at [2,-8]km; coast relocs
remain UNAPPROVED. Output is route design, not UE5 actor meshes or a .umap.

Usage:
 python scripts/plan_skarvik_native_coastal_routes.py \
   --grid /tmp/skarvik-coastal-native-grid-200m.csv \
   --world public/config/skarvik-world-layout-48km.json \
   --coast public/config/skarvik-final-coastal-migration-125-sites.json \
   --output /tmp/SKARVIK_ROUTES_NEW
"""
from __future__ import annotations
import argparse,csv,heapq,json,math,hashlib
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
N=241
STEP=200
E0=-24000
MAX_EXPANSIONS=25000


def node_xy(i:int)->tuple[int,int]:
    return (E0+(i%N)*STEP,E0+(i//N)*STEP)


def grid_index(x:int,y:int)->int:
    return y*N+x


def nearest(e:float,n:float,dry:list[bool],limit=1000):
    cx=round((e-E0)/STEP)
    cy=round((n-E0)/STEP)
    best=(float("inf"),None)
    for radius in range(7):
        for j in range(max(0,cy-radius),min(N,cy+radius+1)):
            for i in range(max(0,cx-radius),min(N,cx+radius+1)):
                if max(abs(i-cx),abs(j-cy))!=radius:continue
                pos=grid_index(i,j)
                if not dry[pos]:continue
                d=math.hypot(e-(E0+i*STEP),n-(E0+j*STEP))
                if d<best[0]:best=(d,pos)
    return (round(best[0],2),best[1] if best[0]<=limit else None)


def city_portal(a:dict,b:dict):
    x,y=a["targetKm"]
    if a["id"]!="citysample":return (1000*x,1000*y)
    dx,dy=b["targetKm"][0]-x,b["targetKm"][1]-y
    factor=max(abs(dx)/2,abs(dy)/2)
    if factor<1e-6:raise ValueError("City Sample route with same endpoints")
    return (1000*(x+dx/factor),1000*(y+dy/factor))


def in_city(x:int,y:int)->bool:
    return 0<x<4000 and -10000<y<-6000


def build_edges(z,coast,dry):
    offsets=((-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1))
    adjacency=[[] for _ in range(N*N)]
    for u in range(N*N):
        if not dry[u]:continue
        x,y=u%N,u//N
        p=node_xy(u)
        if in_city(*p):continue
        for dx,dy in offsets:
            nx,ny=x+dx,y+dy
            if not 0<=nx<N or not 0<=ny<N:continue
            v=grid_index(nx,ny)
            if not dry[v] or in_city(*node_xy(v)):continue
            if dx and dy:
                if not dry[grid_index(nx,y)] or not dry[grid_index(x,ny)]:
                    continue # never take diagonal shortcut through water
            length=STEP*math.hypot(dx,dy)
            slope=abs(z[v]-z[u])/length
            if slope>0.15:continue
            shore=max(0,450-min(coast[u],coast[v]))/450
            adjacency[u].append((v,length*(1+4.5*slope+1.25*shore)))
    return adjacency


def a_star(start,goal,edges):
    if start==goal:return [start]
    target=node_xy(goal)
    heap=[(0.,0,start)]
    best={start:0.}
    parent={}
    serial=0
    visits=0
    while heap and visits<MAX_EXPANSIONS:
        score,_,u=heapq.heappop(heap)
        e,n=node_xy(u)
        distance=math.hypot(e-target[0],n-target[1])
        if score>best[u]+distance+.001:continue
        if u==goal:
            result=[u]
            while result[-1]!=start:result.append(parent[result[-1]])
            return result[::-1]
        visits+=1
        for v,cost in edges[u]:
            new_cost=best[u]+cost
            if new_cost<best.get(v,float("inf")):
                best[v]=new_cost
                parent[v]=u
                serial+=1
                x,y=node_xy(v)
                heapq.heappush(heap,(new_cost+math.hypot(x-target[0],y-target[1]),serial,v))
    return None


def simplify(points):
    if len(points)<3:return points
    keep=[points[0]]
    for i in range(1,len(points)-1):
        a,b,c=(node_xy(points[j]) for j in (i-1,i,i+1))
        if (b[0]-a[0],b[1]-a[1])!=(c[0]-b[0],c[1]-b[1]):
            keep.append(points[i])
    keep.append(points[-1])
    return keep


def plan(world,coastal,grid_text):
    if world.get("world")!="SKARVIK" or coastal.get("world")!="SKARVIK" or len(world.get("roads",[]))!=382 or len(coastal.get("sites",[]))!=125:
        raise ValueError("Not the approved 382-road, 125-town SKARVIK map")
    if coastal.get("destinationWorld")!="/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1" or \
       sum(bool(p.get("relocated")) for p in coastal["sites"])!=67:
        raise ValueError("Untrusted 7-island coast or 67 provisional town moves")
    if world["citySample"]["cityCenterKm"]!=[2,-8] or world["citySample"]["fullCityKm"]!=[4,4]:
        raise ValueError("City Sample 4km protected footprint changed")
    grid=list(csv.DictReader(grid_text.splitlines()))
    if len(grid)!=N*N:raise ValueError("Missing full 241x241 REAL C++ terrain grid")
    h=[];c=[];dry=[]
    for idx,r in enumerate(grid):
        e,n=node_xy(idx)
        if (int(r["east_m"]),int(r["north_m"]))!=(e,n) or \
            r["source_cxx"]!="SKARVIK_FINAL_7_ISLANDS_CXX_V1":
            raise ValueError("Wrong coast samples or row ordering")
        h.append(float(r["terrain_z_m"]))
        c.append(float(r["coast_distance_m"]))
        dry.append(r["land_for_road"]=="1")
    edges=build_edges(h,c,dry)
    sites={p["id"]:p for p in coastal["sites"]}
    if len(sites)!=125:raise ValueError("Duplicate original site IDs")
    rows=[]
    routes={}
    counts=Counter()
    cache={}
    for i,road in enumerate(world["roads"]):
        src,dst=sites[road["from"]],sites[road["to"]]
        rid=road.get("id") or f"LEGACY_NO_GEOMETRY_{i+1:03d}"
        da,a=nearest(*city_portal(src,dst),dry)
        db,b=nearest(*city_portal(dst,src),dry)
        record={
            "id":rid,"from":src["id"],"to":dst["id"],"class":road.get("class"),
            "originalHasDetailedGeometry":len(road.get("waypointsKm",[]))>=2,
            "provisionalRelocationOnEitherEnd":bool(src["relocated"] or dst["relocated"]),
            "distanceToLandGridMeters":[da,db],"nativePavedActorsCreated":0,
            "nativeCollisionVerified":False,
            "originalAssetsChanged":False,
        }
        if a is None or b is None:
            record["status"]="NO_COAST_SAFE_ENTRY_NEEDS_PORT_BRIDGE_OR_FERRY_REVIEW"
        else:
            if (a,b) not in cache:cache[a,b]=a_star(a,b,edges)
            path=cache[a,b]
            if path is None:
                record["status"]="NO_SEVEN_ISLAND_LAND_LINK_BRIDGE_OR_FERRY_REVIEW"
            else:
                record["status"]="COAST_SAFE_200M_CANDIDATE_NOT_BUILT"
                key=f"{i+1:03d}_{rid}"
                reduced=simplify(path)
                routes[key]=[[round(node_xy(n)[0]/1000,4),
                              round(node_xy(n)[1]/1000,4),round(h[n],2)] for n in reduced]
                total=sum(math.dist(node_xy(a),node_xy(b)) for a,b in zip(path,path[1:]))
                record["lengthKm"]=round(total/1000,3)
                record["routeKey"]=key
        counts[record["status"]]+=1
        rows.append(record)
    return {
        "schemaVersion":1,"map":"SKARVIK","sizeKm":[48,48],
        "originalWorldAndSevenIslandsUntouched":True,
        "originalSiteCount":125,"provisionalRelocationsNotApproved":67,
        "originalRegionalRoutes":382,
        "coastalTerrainSource":"true original C++ seven island height function sampled at 200m",
        "gridSHA256":hashlib.sha256(grid_text.encode("utf-8")).hexdigest(),
        "sampleStepMeters":STEP,"sourceWorldPartitionNotModified":True,
        "nativeRoadMeshesBuilt":0,"UE5PIETested":False,
        "statusCounts":dict(counts),"roads":rows,
        "candidateWaypointsEastNorthKmAndHeightMeters":routes,
        "important":"Only design candidates. Before building inspect slopes/bridge/water at ~5m and preserved actor collisions; protect existing City Sample 4km.",
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--grid",required=True,type=Path)
    ap.add_argument("--world",required=True,type=Path)
    ap.add_argument("--coast",required=True,type=Path)
    ap.add_argument("--output",required=True,type=Path)
    args=ap.parse_args()
    root=args.output.expanduser().resolve()
    if root==ROOT or ROOT in root.parents:raise ValueError("Do not write reports inside source tree")
    if root.exists():raise FileExistsError("Never overwrite output")
    doc=plan(json.loads(args.world.read_text(encoding="utf-8")),
             json.loads(args.coast.read_text(encoding="utf-8")),
             args.grid.read_text(encoding="utf-8"))
    root.mkdir(parents=True)
    (root/"skarvik-382-route-geometry-candidates.json").write_text(
        json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with (root/"skarvik-382-route-status.csv").open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.writer(f)
        writer.writerow(["id","from","to","status","originalHasDetailedGeometry",
                         "provisionalRelocationOnEitherEnd","candidateLengthKm","nativePavedActorsCreated"])
        for row in doc["roads"]:
            writer.writerow([row["id"],row["from"],row["to"],row["status"],
                row["originalHasDetailedGeometry"],
                row["provisionalRelocationOnEitherEnd"],row.get("lengthKm",""),0])
    print(json.dumps({"map":doc["map"],"totalRoutes":len(doc["roads"]),
                      "statusCounts":doc["statusCounts"],"newNativeRoadMeshes":0},ensure_ascii=False))


if __name__=="__main__":main()
