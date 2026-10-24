"""Independently audit saved house replacements without Python actor/mesh wrappers.

This task never authors packages. The native function copies short-lived Unreal
values to JSON; only strings, numbers and lists reach Python verification.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
PACKAGE='/Game/Maps/ANOMALIA_Inhabited_v2'
OUT=Path(os.environ['ANOMALIA_RESIDENTIAL_AUDIT_REPORT'])
report=dict(state='FAILED',sourceCommit=os.environ.get('GITHUB_SHA'),mapPackage=PACKAGE,
            packagesSaved=False,terrainModified=False,playerSavesModified=False,fullMapComplete=False)

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,file)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for part in iter(lambda:stream.read(1048576),b''):h.update(part)
    return h.hexdigest()

try:
    ground=module('residential_ground',ROOT/'Scripts/archipelago_population.py')
    layout=module('residential_layout',ROOT/'Scripts/residential_replacement.py')
    checker=module('residential_audit',ROOT/'Scripts/residential_audit.py')
    receipts=[]
    for path in (ROOT/'Saved/TransportCity').glob('run-*/populated-world.json'):
        value=json.loads(path.read_text())
        if value.get('state')=='POPULATED_WORLD_CREATED_NOT_PLAYTESTED' and value.get('mapPackage')==PACKAGE:
            receipts.append((path.stat().st_mtime,path))
    if not receipts:raise RuntimeError('Original population receipt required')
    plan_file=max(receipts)[1].parent/'population-plan.json'
    plan=json.loads(plan_file.read_text())
    if plan.get('mapPackage')!=PACKAGE:raise RuntimeError('Wrong population plan')
    items={'ANOMALIA_Inhabited1_'+i['id']:i for i in plan['buildings']}
    if len(items)!=4760:raise RuntimeError('Complete 4760-house plan required')
    source=ROOT/'SourceAssets/ResidentialPhotogrammetryPrepared_v1'
    models={m['id']:m for m in json.loads((source/'manifest.json').read_text())['models']}
    models={key:models[key] for key in layout.MODELS}
    for key,value in models.items():
        file=(source/value['file']).resolve()
        if not file.is_relative_to(source) or sha256(file)!=value['sha256']:raise RuntimeError('Prepared scan checksum mismatch: '+key)
    original=next(m for m in json.loads((ROOT/'SourceAssets/RealismValidation_v2/manifest.json').read_text())['models'] if m['id']=='detached_house')
    original=dict(original,objectPath=original['objectPath']+'_r2')
    if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(PACKAGE):raise RuntimeError('Saved world could not open')
    native=json.loads(unreal.AnomaliaWorldImportLibrary.audit_inhabited_residential(
        [m['objectPath'] for m in models.values()]+[original['objectPath']],sorted(items)))
    OUT.with_name('residential-native-values.json').write_text(json.dumps(native,indent=2))
    surface=ground.sampled_surface(unreal.AnomaliaWorldImportLibrary.inhabited_archipelago_height)
    counts=checker.verify(native,items,models,original,layout,surface,ground.ground_envelope)
    report.update(state='SAVED_RESIDENTIAL_NATIVE_AUDIT_PASSED',counts=counts,planSha256=sha256(plan_file))
except Exception as error:
    report['error']=str(error);raise
finally:
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2))
