"""Download only pinned, credited sources for the isolated visual validation map."""
import concurrent.futures, hashlib, json, os, subprocess, uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REGISTRY=ROOT/'docs/art/realism-validation-sources.json'
CACHE=ROOT/'unreal/Saved/RealismSourceCache'

def fetch(entry):
    model,item=entry
    target=CACHE/model['id']/item['path']
    if not target.resolve().is_relative_to(CACHE.resolve()): raise ValueError('Unsafe asset path')
    target.parent.mkdir(parents=True,exist_ok=True)
    def valid(path):
        return path.is_file() and path.stat().st_size==item['bytes'] and hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']
    if target.exists():
        if not valid(target): raise ValueError('Existing source differs; preserved: '+str(target))
        return
    part=target.with_name(target.name+'.part-'+uuid.uuid4().hex)
    try:
        subprocess.run(['curl.exe' if os.name=='nt' else 'curl','-fSL','--retry','2','--max-time','180',item['url'],'-o',str(part)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        if not valid(part): raise ValueError('Asset identity mismatch: '+model['id'])
        part.replace(target)
    finally:
        if part.exists():part.unlink()

def main():
    models=json.loads(REGISTRY.read_text())['models']
    if any(m['license'] not in {'CC0-1.0','CC-BY-4.0'} for m in models):raise ValueError('Unreviewed asset license')
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(fetch,[(m,f)for m in models for f in m['files']]))
    print('Verified pinned sources:',len(models),'assets; no existing art overwritten.')

if __name__=='__main__':main()
