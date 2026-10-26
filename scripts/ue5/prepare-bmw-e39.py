"""Fetch the already registered CC-BY E39 without authentication; preserve prior sources."""
import hashlib,json,os,subprocess,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def main():
    registry=json.loads((ROOT/'docs/vehicles/named-assets-sources.json').read_text())
    items=registry if isinstance(registry,list) else next(v for v in registry.values() if isinstance(v,list) and any(isinstance(x,dict) and x.get('id')=='bmw_e39' for x in v))
    item=next(x for x in items if x['id']=='bmw_e39')
    if item['license']!='CC-BY-4.0' or item['sourceSHA256']!='984a9daab49b5a31c45bbc284c657fa5898a010f2201c003358cb6b6f411751d':raise ValueError('Reviewed E39 identity required')
    folder=ROOT/'unreal/Saved/BMWE39Source';folder.mkdir(parents=True,exist_ok=True)
    target=folder/'bmw-e39.glb'
    def valid(p):return p.is_file() and p.stat().st_size==item['sourceBytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==item['sourceSHA256']
    if target.exists():
        if not valid(target):raise ValueError('Existing source preserved: hash mismatch')
    else:
        temp=folder/(uuid.uuid4().hex+'.part')
        try:
            subprocess.run(['curl.exe' if os.name=='nt' else 'curl','-fSL','--max-time','120','--max-filesize',str(item['sourceBytes']),item['downloadUrl'],'-o',str(temp)],check=True)
            if not valid(temp):raise ValueError('E39 source integrity mismatch')
            temp.replace(target)
        finally:temp.unlink(missing_ok=True)
    print('CC-BY E39 source verified; not a gameplay acceptance.')
if __name__=='__main__':main()
