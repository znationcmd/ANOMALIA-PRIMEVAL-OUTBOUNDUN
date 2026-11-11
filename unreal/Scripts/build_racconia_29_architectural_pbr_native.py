"""Stage RACCONIA 29 original locations with PBR architectural V2 GLB shells.

This script works ONLY in isolated C: UE5 staging. It NEVER edits the
old RACCONIA blockouts, the three SKARVIK maps or the D: project.

Output is a first playable-area *architectural placement*, not a full
photorealistic interior replacement. It assumes native Unreal project module
AnomaliaZPrigimaliaRacconiaLandscape compiled successfully and real R16 source.
"""
from __future__ import annotations
import csv
import math
import struct
import hashlib
import json
import os
import re
import unicodedata
from pathlib import Path
import traceback
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
STAGE=Path('C:/ANOMALIAZ_SKARVIK_STAGE_41188816555/unreal')
MARKER=ROOT/'.skarvik-ci-stage-marker'
TARGET='/Game/Maps/PRIGIMALIA_RACCONIA_VARKOVIA_16KM_v1'
LEVEL_FILE=ROOT/'Content/Maps/PRIGIMALIA_RACCONIA_VARKOVIA_16KM_v1.umap'
ROOT_ASSETS='/Game/Anomalia/Racconia/ArchitecturalPBR_V2'
PBR_ROOT=ROOT/'SourceAssets/Racconia29PBR_20261111'
SOURCE_ROOT=ROOT/'SourceAssets/Racconia16km_20261111'
CSV=SOURCE_ROOT/'racconia-29-sites-UE5.csv'
RAW=SOURCE_ROOT/'RACCONIA_UE5_READY_1009_north_up.r16'
MANIFEST=PBR_ROOT/'RACCONIA_29_PBR_ARCHITECTURE_MANIFEST.json'
OUT=Path(os.environ['RACCONIA_29_PBR_NATIVE_IMPORT_REPORT']).resolve()
PROTECTED=[
    ROOT/'Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap',
    ROOT/'Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap',
    ROOT/'Content/Maps/PRIGIMALIA_SKARVIK_ISLANDS_v1.umap',
    ROOT/'Content/Map/Big_City_LVL.umap',
    Path('D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap'),
]
R={
    'state':'FAILED','target':TARGET,'originalSiteCount':29,
    'originalBlockoutSourceActorCount':0,'PBR_GLBSourcesValidated':0,
    'nativeStaticMeshPartsImported':0,'nativePBRBuildingPartsPlaced':0,
    'originalSiteAnchorsSaved':0,'nativeLandscapeComponents':0,
    'nativeMapSaved':False,'originalUserSourcesUnchanged':False,
    'realisticMaterialsVisuallyVerifiedInUE5':False,
    'allOriginal491RoomsFinished':False,
    'doorsGameplayValidated':False,'UnrealGameplayPIETested':False,
    'photorealFinalCertified':False,'partsPerSite':{},
}


def normalized(t):
    text=unicodedata.normalize('NFKD',t).encode('ascii','ignore').decode('ascii').lower()
    return re.sub('[^a-z0-9]+','',text)

def terrain_surface_cm(raw, x_cm, y_cm):
    """Bilinear height from the exact north-up raster imported by the C++ helper."""
    if len(raw) != 1009*1009*2 or not (-800000 <= x_cm <= 800000 and -800000 <= y_cm <= 800000):
        raise ValueError("Racconia terrain sample outside verified raster")
    px=(x_cm+800000.0)*1008.0/1600000.0
    py=(y_cm+800000.0)*1008.0/1600000.0
    x0,y0=int(px),int(py)
    x1,y1=min(x0+1,1008),min(y0+1,1008)
    u,v=px-x0,py-y0
    value=sum(struct.unpack_from("<H",raw,2*(yy*1009+xx))[0]*wx*wy
              for xx,wx in ((x0,1-u),(x1,u))
              for yy,wy in ((y0,1-v),(y1,v)))
    return (value-32768.0)*2500.0/128.0

try:
    if str(ROOT).replace('\\','/').lower()!=str(STAGE).replace('\\','/').lower():
        raise RuntimeError('Wrong Unreal project root; refuse original D: writes')
    if not MARKER.is_file() or MARKER.read_text(encoding='utf-8-sig').strip()!='41188816555':
        raise RuntimeError('Verified Unreal staging marker not found')
    if LEVEL_FILE.exists() or (ROOT/'Content/__ExternalActors__/Maps/PRIGIMALIA_RACCONIA_VARKOVIA_16KM_v1').exists():
        raise RuntimeError('Target already exists: refuse to overwrite or duplicate')
    if any(not p.is_file() for p in PROTECTED):
        raise RuntimeError('Existing protected original map missing')
    if not MANIFEST.is_file() or not CSV.is_file() or not RAW.is_file():
        raise RuntimeError('Both real RACCONIA source terrain and PBR artifacts required')
    source_manifest=json.loads((SOURCE_ROOT/'racconia-height-scale-and-sites.json').read_text(encoding='utf-8'))
    raw_height=RAW.read_bytes()
    if hashlib.sha256(raw_height).hexdigest()!=source_manifest['correctedRaw16Sha256']:
        raise RuntimeError('Source heightmap SHA256 mismatch')
    if RAW.stat().st_size!=1009*1009*2:
        raise RuntimeError('Invalid RACCONIA real source RAW16')
    manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
    originals={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in PROTECTED}
    records=manifest['models']
    if len(records)!=29:
        raise RuntimeError('Original horror identities corrupt')
    if len(set(r['id'] for r in records))!=29:
        raise RuntimeError('Duplicate horror building identity')
    if any(r['photorealismVisuallyCertified'] or r['interiorsComplete'] or r['newTexturedMaterialGroups']<6 for r in records):
        raise RuntimeError('Untrusted PBR model or false visual/room claim')
    site_rows=list(csv.DictReader(CSV.open(encoding='utf-8-sig',newline='')))
    if len(site_rows)!=29:
        raise RuntimeError('Missing 29 original terrain coordinates')
    sites={normalized(s['name']):s for s in site_rows}
    if len(sites)!=29:
        raise RuntimeError('Duplicate real source site names')
    for rec in records:
        model=PBR_ROOT/'GLB_PBR_EXTERIORS_V1'/rec['file']
        if not model.is_file() or model.stat().st_size!=rec['bytes']:
            raise RuntimeError('Missing 3D PBR original venue '+rec['id'])
        if hashlib.sha256(model.read_bytes()).hexdigest()!=rec['sha256']:
            raise RuntimeError('PBR source texture/mesh hash changed for '+rec['id'])
        if normalized(rec['name']) not in sites:
            raise RuntimeError('Original RACCONIA placement not found: '+rec['name'])
    R['PBR_GLBSourcesValidated']=29
    lib=unreal.EditorAssetLibrary
    tools=unreal.AssetToolsHelpers.get_asset_tools()
    if lib.does_directory_exist(ROOT_ASSETS):
        raise RuntimeError('PBR V2 imported previously or folder already exists; refuse duplicates')
    if lib.does_asset_exist(TARGET):
        raise RuntimeError('Target native map already authored')

    # Source-mesh import only. Each GLB is a multi-material assembly, which may
    # become several StaticMesh parts on import, all sharing original local origin.
    # Keep each set in its own folder to prevent cross-site name collisions.
    model_assets={}
    for rec in records:
        key=rec['id'];dest=ROOT_ASSETS+'/'+key
        task=unreal.AssetImportTask()
        task.filename=str(PBR_ROOT/'GLB_PBR_EXTERIORS_V1'/rec['file'])
        task.destination_path=dest
        task.automated=True
        task.replace_existing=False
        task.save=True
        task.async_=False
        tools.import_asset_tasks([task])
        task.get_objects()
        asset_paths=list(lib.list_assets(dest,recursive=True,include_folder=False))
        meshes=[]
        for a in asset_paths:
            obj=lib.load_asset(a)
            if isinstance(obj,unreal.StaticMesh):
                bounds=obj.get_bounds()
                if max(float(bounds.box_extent.x),float(bounds.box_extent.y),float(bounds.box_extent.z))>15000:
                    raise RuntimeError('Imported mesh bounds implausible: '+str(a))
                meshes.append(obj)
        if not meshes or sum(int(obj.get_num_triangles(0)) for obj in meshes)<1000:
            raise RuntimeError('Imported architectural geometry is incomplete: '+key+' parts='+str(len(meshes)))
        model_assets[key]=meshes
        R['nativeStaticMeshPartsImported']+=len(meshes)
        unreal.log('RACCONIA_PBR_NATIVE_MESHES_{}={}'.format(key,len(meshes)))

    # Terrain import is dedicated to NEW RACCONIA map only; pre-existing maps
    # cannot be changed, no duplicate landscape allowed.
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels.new_level(TARGET,is_partitioned_world=True):
        raise RuntimeError('Could not create original RACCONIA new 16km World Partition map')
    importer=unreal.AnomaliaZPrigimaliaRacconiaLandscape
    terrain=importer.create_racconia_verified_landscape()
    if not terrain:raise RuntimeError('Native 1009 original heightmap Landscape import failed')
    terrain_actors=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.LandscapeProxy)]
    components=[c for a in terrain_actors for c in a.get_components_by_class(unreal.LandscapeComponent)]
    collision=[c for a in terrain_actors for c in a.get_components_by_class(unreal.LandscapeHeightfieldCollisionComponent)]
    if len(collision)!=64:raise RuntimeError("Expected 64 native terrain collision components")
    R["nativeLandscapeProxyActors"]=len(terrain_actors)
    R["nativeLandscapeCollisionComponents"]=len(collision)
    R["sitePlacementsCm"]={}
    R["maxOriginalSiteGroundCorrectionCm"]=0.0
    if len(components)!=64:raise RuntimeError('Expected 64 real Landscape components; got '+str(len(components)))
    R['nativeLandscapeComponents']=len(components)
    for rec in records:
        key=rec['id'];site=sites[normalized(rec['name'])]
        x=float(site['X_cm'])
        y=-float(site['Y_cm'])  # model source CSV north positive, UE north negative
        z=terrain_surface_cm(raw_height,x,y)
        R["maxOriginalSiteGroundCorrectionCm"]=max(R["maxOriginalSiteGroundCorrectionCm"],abs(z-float(site["Z_cm"])))
        R["sitePlacementsCm"][key]=[x,y,z+20.0]
        marker=actors.spawn_actor_from_class(unreal.TargetPoint,unreal.Vector(x,y,z+200.))
        if not marker:raise RuntimeError('Source site marker cannot be spawned: '+key)
        marker.set_actor_label('RACCONIA_ORIGINAL_SITE_'+site['id']+'_'+key)
        marker.tags=[unreal.Name('RACCONIA_ORIGINAL_29_SITE'),unreal.Name(key)]
        R['originalSiteAnchorsSaved']+=1
        count=0
        for mesh in model_assets[key]:
            actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(x,y,z+20.))
            if not actor:raise RuntimeError('Cannot spawn original horror building part: '+key)
            actor.set_actor_label('RACCONIA_ARCH_PBR_V2_'+key+'_'+str(count).zfill(3))
            actor.tags=[unreal.Name('RACCONIA_PBR_ARCHITECTURAL_V2'),unreal.Name('RACCONIA_SITE_'+key)]
            comp=actor.get_component_by_class(unreal.StaticMeshComponent)
            if not comp or not comp.set_static_mesh(mesh):
                raise RuntimeError('Cannot assign original horror PBR mesh: '+key)
            comp.set_collision_profile_name('BlockAll')
            count+=1
            R['nativePBRBuildingPartsPlaced']+=1
        R['partsPerSite'][key]=count
    if R['originalSiteAnchorsSaved']!=29 or any(v<1 for v in R['partsPerSite'].values()):
        raise RuntimeError('Original 29 houses not all assembled in new World Partition')
    if not levels.save_all_dirty_levels() or not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
        raise RuntimeError('Native RACCONIA level or external actor packages not saved')
    for p in PROTECTED:
        if hashlib.sha256(p.read_bytes()).hexdigest()!=originals[str(p)]:
            raise RuntimeError('Protected original was modified: '+str(p))
    R['originalUserSourcesUnchanged']=True
    R['nativeMapSaved']=True
    R['state']='29_ORIGINAL_SITE_PBR_EXTERIOR_PARTS_IN_NATIVE_RACCONIA_LEVEL_NOT_FULL_GAMEPLAY'
    unreal.log('RACCONIA_NATIVE_ARCH_PBR_29_SITES_SAVED=true')
except Exception as e:
    R['error']=str(e)
    R['traceback']=traceback.format_exc()[-7000:]
    unreal.log_error('RACCONIA_29_PBR_NATIVE_IMPORT_ERROR='+str(e))
finally:
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(R,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')