"""Original relief language for CHERNASKALUXRIA's 10 reference images.

Images 1-2: desert mountain terraces and greener inhabited mountain valleys
Images 3-4: fragmented temperate coastal island and highland settlements
Images 5-6: densely wooded island groups, volcanic slopes and sheltered bays
Images 7-8: frozen volcanic island, sea ice and polar archipelago
Images 9-10: fertile rural fields, forest mosaics, long rivers and country roads

This is original coordinate-based source, NOT a heightmap extraction, traced
coastline or copy of any DayZ, Arma Reforger, iZurvive or other game assets.
The values are in metres and only affect the ninth world. No actors spawned.
"""
from __future__ import annotations
import math

FUSION_REFERENCES={
    "1-2":{"terrain":"arid mountain escarpments, valleys, plateau and seasonal wadis",
           "zone":"arid-highlands"},
    "3-4":{"terrain":"temperate coastal rocky hills, islets and long shore valleys",
           "zone":"coastal-ports"},
    "5-6":{"terrain":"tropical wooded island ridges, bays and fractured volcanic coast",
           "zone":"tropical-rainforest"},
    "7-8":{"terrain":"broken polar ice coast, high snowy mountains and volcanic islands",
           "zone":"polar-volcanic"},
    "9-10":{"terrain":"agricultural lowlands, temperate ridges, long rivers and wetlands",
            "zone":"farming-lowlands"},
}
SOURCE_IMAGE_USE="VISUAL_COMPOSITION_REFERENCE_ONLY_NO_PIXEL_OR_HEIGHTMAP_COPY"

def _gauss(x:float,y:float,cx:float,cy:float,rx:float,ry:float)->float:
    return math.exp(-((x-cx)/rx)**2-((y-cy)/ry)**2)

def _wave(x:float,y:float,a:float,b:float)->float:
    return math.sin(x/a + .32*math.cos(y/b))*math.cos(y/b-.25*math.sin(x/a))

def source_height_overlay(e:float,n:float,weights:dict[str,float])->float:
    """Blend original geomorphology from five pairs without heightmap seams."""
    if not math.isfinite(e) or not math.isfinite(n):
        raise ValueError("Invalid world coordinate")
    # Arid terrain, mountainous on both sides of green valley.
    ridge_east=(120+90*abs(_wave(e,n,2150,1850)))*_gauss(e,n,29500,9000,15500,17000)
    ridge_south=(80+105*abs(_wave(e,n,1250,1900)))*_gauss(e,n,21000,-12000,12000,7500)
    desert_wadi=n-(3500*math.sin(e/8300)+6500)
    dry_wash=90*math.exp(-(desert_wadi/1150)**2)
    desert=(ridge_east+ridge_south-dry_wash)*weights["arid-highlands"]

    # Temperate port region: naturally graded hills and shallow coast inlets.
    rolling=65*_wave(e,n,3300,2900)+100*_gauss(e,n,-35500,-7000,9500,14500)
    sea_cliffs=110*abs(_wave(e,n,1250,960))*_gauss(e,n,-43500,-7000,6500,9500)
    coastal=(rolling+sea_cliffs)*weights["coastal-ports"]

    # Two reference forest/island maps: curved valleys, rugged tropical ridges.
    rainforest_ridge=140*abs(_wave(e,n,1800,2150))*_gauss(e,n,-14000,-29000,17500,14000)
    rainforest_wetland=65*_gauss(e,n,-9500,-34500,8000,11000)
    tropical=(rainforest_ridge-rainforest_wetland)*weights["tropical-rainforest"]
    paradise=60*_wave(e,n,1350,1550)*weights["paradise-islands"]

    # Polar territory: ragged glaciated mountains + frozen volcanic summit.
    glacier=(230*abs(_wave(e,n,2000,2600))+
             110*_gauss(e,n,24000,35500,12000,8000))
    volcanic_cone=230*_gauss(e,n,33500,33000,6400,7300) * (
        1.-.75*_gauss(e,n,33500,33000,2200,2400))
    polar=(glacier+volcanic_cone)*weights["polar-volcanic"]
    alpine=(130*abs(_wave(e,n,1700,1350))*
            _gauss(e,n,-23500,32500,17000,15000))*weights["northern-alpine"]

    # Continental Chernarus/Livonia-inspired farmland and continuous river,
    # deliberately NOT the same river tracing or topographic outlines.
    rural_ridge=85*_wave(e,n,4100,3800)
    riverline=n-(8500+2200*math.sin(e/9200)+950*math.sin(e/2700))
    river_valley=72*math.exp(-(riverline/670.)**2)
    countryside=(rural_ridge-river_valley)*weights["farming-lowlands"]
    city_valley=(-14*_gauss(e,n,1800,1200,9200,7800))*weights["central-metropolis"]

    # Damaged island: sharp crater rim and eroded badlands.
    radioactive=(85*abs(_wave(e,n,2000,1550))*
                 _gauss(e,n,26000,-30000,14000,14000))*weights["devastated-exclusion"]
    return (desert+coastal+tropical+paradise+polar+alpine+
            countryside+city_valley+radioactive)

def fusion_manifest()->dict:
    return {
      "mapId":"chernaskaluxria-v1",
      "worldSizeKm":[100,100],
      "sourceUse":SOURCE_IMAGE_USE,
      "imagePairs":FUSION_REFERENCES,
      "realHeightSampleInput":False,
      "realNativeWorldBuilt":False,
      "originalTopographicOverlayCodeReady":True,
      "topologyAndCoastlinesRequireUEValidation":True,
      "bridgesAndUnderseaTunnelsBuilt":False,
    }
