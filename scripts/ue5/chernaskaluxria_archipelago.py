"""Original CHERNASKALUXRIA marine geography and UNBUILT crossing corridors.

Marine channels make one World Partition world containing separated islands,
not six or nine new map packages. Structures below are route proposals only.
Do not depict bridge decks, watertight submarine tunnels, nav meshes or
vehicle connectivity as finished: each requires separate native UE art/test.
"""
from __future__ import annotations
import math

WORLD_ID = "chernaskaluxria-v1"
SEA_LEVEL_METRES = 0.0
SHORE_SLOPE_METRES = 1500.0

def _smooth(t: float) -> float:
    x=max(0.0,min(1.0,t))
    return x*x*(3.0-2.0*x)

def channel_centre(channel: str, coord: float) -> float:
    """Returns E coordinate for NS channels; N for the southern EW sea."""
    if channel=="west":
        return -16000 + 1300*math.sin(coord/7600) + 850*math.sin(coord/22000+.8)
    if channel=="east":
        return 17000 + 2000*math.sin(coord/11500+.7)
    if channel=="south":
        return -12000 + 1600*math.sin(coord/14000) + 500*math.sin(coord/6100)
    raise ValueError("Unknown channel")

def half_width(channel: str, coord: float) -> float:
    """Narrow navigable straits at intended crossings, wider elsewhere."""
    if channel=="west":
        return max(620., 1830 + 280*math.sin(coord/10000)
                   - 750*math.exp(-((coord-15000)/3300)**2))
    if channel=="east":
        return max(650., 1910 + 290*math.sin(coord/9200+.7)
                   - 820*math.exp(-((coord-16000)/3200)**2))
    if channel=="south":
        return max(630., 1790 + 260*math.sin(coord/10500)
                   - 700*math.exp(-(coord/3200)**2)
                   - 520*math.exp(-((coord+31000)/3100)**2))
    raise ValueError("Unknown channel")

def water_distances(east: float, north: float) -> dict[str,float]:
    """Signed distance: negative=sea, positive=land beyond channel edge."""
    coast_margin=50000 - max(abs(east),abs(north))
    irregular=4800 + 700*math.sin((east+north)/9500) + 500*math.cos((east-north)/6100)
    return {
      "ocean":coast_margin-irregular,
      "west":abs(east-channel_centre("west",north))-half_width("west",north),
      "east":abs(east-channel_centre("east",north))-half_width("east",north),
      "south":abs(north-channel_centre("south",east))-half_width("south",east),
    }

def carve_archipelago(original_height: float,east: float,north: float) -> float:
    """Physically carved water below sea level, softened shores to prevent walls."""
    if not math.isfinite(original_height):raise ValueError("Invalid original height")
    value=original_height
    distances=water_distances(east,north)
    for name,d in distances.items():
        # Each channel has a navigable floor and natural side slopes.
        # Steeper shorelines can later be improved with authored coastal meshes.
        bottom=-24. if name!="ocean" else -65.
        seabed=bottom-7.*_smooth(-d/1500.)
        shaped=seabed + (original_height-seabed)*_smooth(d/SHORE_SLOPE_METRES)
        value=min(value,shaped)
    return value


# Separate offshore territories inside ONE World Partition map. Areas are
# target square kilometres (km²), not linear distance, and must be measured
# from sampled ground after terrain generation.
# Gameplay hooks below are design intents; structures/loot are NOT deployed.
SATELLITE_ISLANDS = (
    {"id":"elyndra","centreKm":(-33,-35),"axesKm":(8.9,7.15),
     "targetKm2":200,"phase":.4,"biome":"paradise-islands",
     "discovery":"tropical coves, wreck dives, water-access caves"},
    {"id":"karvex","centreKm":(37,-38),"axesKm":(8.9,7.15),
     "targetKm2":200,"phase":1.3,"biome":"devastated-exclusion",
     "discovery":"abandoned research complex, rare engineering materials"},
    {"id":"skelvar","centreKm":(-34,35),"axesKm":(6.2,5.1),
     "targetKm2":100,"phase":1.9,"biome":"northern-alpine",
     "discovery":"snowbound observatory, hidden mountain passage"},
    {"id":"horvak","centreKm":(38,35),"axesKm":(6.2,5.1),
     "targetKm2":100,"phase":2.7,"biome":"polar-volcanic",
     "discovery":"geothermal research outpost, hazardous caves"},
    {"id":"telyra","centreKm":(0,-36),"axesKm":(6.2,5.1),
     "targetKm2":100,"phase":3.3,"biome":"tropical-rainforest",
     "discovery":"jungle sanctuary, ancient underground facilities"},
    {"id":"vasdun","centreKm":(38,4),"axesKm":(4.6,3.5),
     "targetKm2":50,"phase":.8,"biome":"arid-highlands",
     "discovery":"desert fort, scarce fuel and water"},
    {"id":"marona","centreKm":(-38,-4),"axesKm":(4.6,3.5),
     "targetKm2":50,"phase":2.0,"biome":"coastal-ports",
     "discovery":"smuggler harbour, repair supplies"},
    {"id":"frosh","centreKm":(-5,39),"axesKm":(4.6,3.5),
     "targetKm2":50,"phase":3.1,"biome":"northern-alpine",
     "discovery":"remote radio tower, cold-weather loot"},
)
AREA_TARGETS_KM2 = (200,100,50)
# Marine water belts surround the islands; no inadvertent causeways.
MARINE_BASIN_FACTOR = 1.55

def satellite_score(island: dict, east: float, north: float) -> tuple[float,float]:
    x,y=island["centreKm"]
    ax,ay=island["axesKm"]
    dx=(east/1000.-x)/ax
    dy=(north/1000.-y)/ay
    theta=math.atan2(dy,dx)
    angle_offset=island["phase"]
    radius=math.hypot(dx,dy)
    coastline=1.+.035*math.sin(5.*theta+angle_offset)+.025*math.cos(9.*theta-angle_offset)
    return radius,coastline-radius

def satellite_land_mask(island: dict,east: float,north: float) -> bool:
    r,edge=satellite_score(island,east,north)
    return edge>0.

def apply_satellite_islands(carved_height: float,east: float,north: float) -> float:
    """Enforce offshore saltwater basins and original islands with gentle beaches.

    Designed to be O(1) near each island: only ellipses in the nearby
    coordinates are evaluated, and no per-frame runtime actor spawns occur.
    """
    result=carved_height
    for island in SATELLITE_ISLANDS:
        cx,cy=island["centreKm"];ax,ay=island["axesKm"]
        # Broadphase to keep millions of source samples affordable.
        if abs(east/1000.-cx) > ax*MARINE_BASIN_FACTOR or abs(north/1000.-cy)>ay*MARINE_BASIN_FACTOR:
            continue
        radius,positive=satellite_score(island,east,north)
        if radius>=MARINE_BASIN_FACTOR:
            continue
        # Water ring outside the island: no dry connection to the continent.
        if positive>0.:
            island_height=min(220.,positive*155.+8.*math.sin(east/1300.)**2)
            result=max(result if radius>1.13 else -25.,island_height)
        else:
            # Sand shelf (sea-level at the beach), then deep navigable water,
            # then a smooth shallow shore on the outer continent.
            from_coast=max(0.,-positive)
            if radius<1.22:
                sea_floor=-34.*_smooth(from_coast/.23)
            else:
                sea_floor=-34.
            if radius>1.28:
                outer=_smooth((radius-1.28)/(MARINE_BASIN_FACTOR-1.28))
                sea_floor=sea_floor*(1.-outer)+carved_height*outer
            result=min(result,sea_floor)
    return result

def satellite_island_plans() -> list[dict]:
    result=[]
    for item in SATELLITE_ISLANDS:
        x,y=item["centreKm"]
        result.append({
            "id":item["id"],"centreKm":[x,y],"targetKm2":item["targetKm2"],
            "approximateAxesKm":list(item["axesKm"]),
            "biome":item["biome"],"discoveryGoal":item["discovery"],
            "marineAccessRequired":True,"sizeRequiresSourceAreaValidation":True,
            "islandAssetsPopulated":False,"boatRouteTested":False,
            "roadOrTunnelBuilt":False,
        })
    return result

def interisland_voyages() -> list[dict]:
    """Future sea-travel POIs; no fake working vehicle or ferry."""
    return [
      {"id":"boat-to-"+item["id"],"island":item["id"],
       "arrivalKm":list(item["centreKm"]),
       "routeType":"boat-or-ferry",
       "physicalHarbourBuilt":False,"waterNavigationTested":False}
      for item in SATELLITE_ISLANDS
    ]

CROSSINGS = (
    {"id":"pont-nord-ouest","kind":"bridge","channel":"west","axisCoordM":15000,
     "mode":"road","plannedType":"suspension-or-cable-stayed"},
    {"id":"pont-nord-est","kind":"bridge","channel":"east","axisCoordM":16000,
     "mode":"road","plannedType":"multi-span"},
    {"id":"tunnel-sud-ouest","kind":"undersea-tunnel","channel":"west","axisCoordM":-29000,
     "mode":"road","plannedType":"sealed-bored-tunnel"},
    {"id":"tunnel-sud-est","kind":"undersea-tunnel","channel":"east","axisCoordM":-28000,
     "mode":"road","plannedType":"sealed-bored-tunnel"},
    {"id":"pont-central-sud","kind":"bridge","channel":"south","axisCoordM":0,
     "mode":"road","plannedType":"multi-span"},
    {"id":"tunnel-cote-ouest","kind":"undersea-tunnel","channel":"south","axisCoordM":-31000,
     "mode":"road","plannedType":"sealed-bored-tunnel"},
)

def crossing_plans(height_function) -> list[dict]:
    """Pure source calculations; no actual asphalt, bridge or tunnel geometry."""
    planned=[]
    for c in CROSSINGS:
        axis=c["channel"]
        fixed=c["axisCoordM"]
        middle=channel_centre(axis,fixed)
        # Route is normal to the marine channel; bridge landings exceed banks.
        setback=half_width(axis,fixed)+SHORE_SLOPE_METRES+1350.
        if axis in ("west","east"):
            start=(middle-setback,fixed)
            end=(middle+setback,fixed)
            mid=(middle,fixed)
        else:
            start=(fixed,middle-setback)
            end=(fixed,middle+setback)
            mid=(fixed,middle)
        first_z=height_function(*start)
        last_z=height_function(*end)
        mid_z=height_function(*mid)
        planned.append({
          "id":c["id"],"type":c["kind"],"mode":c["mode"],
          "channel":axis,"plannedType":c["plannedType"],
          "startMeters":[round(start[0],2),round(start[1],2),round(first_z,2)],
          "endMeters":[round(end[0],2),round(end[1],2),round(last_z,2)],
          "channelCentreMeters":[round(mid[0],2),round(mid[1],2),round(mid_z,2)],
          "spanOrRouteMeters":round(math.dist(start,end),2),
          "requiresSealedTunnelAndWaterExclusion":c["kind"]=="undersea-tunnel",
          "requiresDetailedShoreAndSlopeSurvey":True,
          "requiresVehicleAndNetworkPlaytest":True,
          "physicalStructureBuilt":False,
          "routeOpenToPlayers":False
        })
    return planned

def sampled_surface_area(height_function,step_metres: int=500) -> dict:
    """Deterministic cell-centre surface estimate, NOT official UE area audit."""
    if step_metres<100 or 100000%step_metres:
        raise ValueError("Sampling step must divide 100000 metres and be >= 100m")
    n=100000//step_metres
    dry=0
    for row in range(n):
        y=-50000+(row+.5)*step_metres
        for col in range(n):
            x=-50000+(col+.5)*step_metres
            if height_function(x,y)>SEA_LEVEL_METRES:dry+=1
    land=round(dry*step_metres**2/1e6,2)
    return {"mapId":WORLD_ID,"sampleStepMetres":step_metres,
            "landKm2":land,"waterKm2":round(10000-land,2),
            "landPercent":round(land/100,2),
            "measuredOn":"procedural_source_terrain_not_native_unreal",
            "totalKm2":10000}
