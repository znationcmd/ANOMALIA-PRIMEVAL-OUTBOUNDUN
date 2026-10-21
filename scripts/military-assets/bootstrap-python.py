"""Project-local official embeddable Python. No MSI, registry, PATH or execution-policy changes."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request
import uuid
import zipfile
ROOT=Path(__file__).resolve().parents[2]
LOCK=json.loads((ROOT/'scripts/military-assets/python-runtime-lock.json').read_text())


def download(item,folder):
    target=folder/item['sha256'];folder.mkdir(parents=True,exist_ok=True)
    raw=target.read_bytes() if target.exists() else urllib.request.urlopen(item['url'],timeout=90).read()
    if len(raw)!=item['bytes'] or hashlib.sha256(raw).hexdigest()!=item['sha256']:raise RuntimeError('Runtime download integrity failed')
    if not target.exists():target.write_bytes(raw)
    return target


def main():
    if sys.platform!='win32':raise RuntimeError('Windows asset runtime bootstrap only')
    base=ROOT/'unreal/Saved/AssetRuntime/python-3.12.10';marker=base/'anomalia-owner.json';cache=ROOT/'unreal/Saved/AssetRuntime/downloads'
    if base.exists():
        if not marker.exists() or json.loads(marker.read_text()).get('pythonZipSHA256')!=LOCK['python']['sha256']:raise RuntimeError('Unowned runtime preserved')
    else:
        archive=download(LOCK['python'],cache);stage=base.parent/('staging-'+uuid.uuid4().hex);stage.mkdir(parents=True)
        with zipfile.ZipFile(archive) as package:package.extractall(stage)
        pth=stage/'python312._pth';pth.write_text('python312.zip\n.\nLib/site-packages\nimport site\n')
        (stage/'Lib/site-packages').mkdir(parents=True)
        (stage/'anomalia-owner.json').write_text(json.dumps(dict(pythonZipSHA256=LOCK['python']['sha256'],pythonExeSHA256=hashlib.sha256((stage/'python.exe').read_bytes()).hexdigest())))
        shutil.move(str(stage),str(base))
    owner=json.loads(marker.read_text());exe=base/'python.exe'
    if hashlib.sha256(exe.read_bytes()).hexdigest()!=owner['pythonExeSHA256']:raise RuntimeError('Modified project runtime preserved')
    pip_wheel=download(LOCK['pip'],cache)
    if not (base/'Lib/site-packages/pip').exists():
        with zipfile.ZipFile(pip_wheel) as package:package.extractall(base/'Lib/site-packages')
    subprocess.run([str(exe),'-m','pip','install','--disable-pip-version-check','--no-warn-script-location','-r',str(ROOT/'scripts/military-assets/requirements.txt')],check=True)
    if os.environ.get('GITHUB_ENV'):
        with open(os.environ['GITHUB_ENV'],'a',encoding='utf-8') as file:file.write('ANOMALIA_ASSET_PYTHON_EXE='+str(exe)+'\n')
    print(json.dumps(dict(state='PROJECT_LOCAL_ASSET_RUNTIME_READY',python=str(exe),globalSettingsChanged=False)))
if __name__=='__main__':main()
