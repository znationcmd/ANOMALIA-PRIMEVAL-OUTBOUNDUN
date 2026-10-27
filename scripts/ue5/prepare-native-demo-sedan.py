"""Fetch one source-verified original CC0 sedan; no catalogue or installed game changes."""
import hashlib,json,os,subprocess,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def main():
    item=json.loads((ROOT/'docs/art/native-demo-sedan-source.json').read_text())
    if item['license']!='CC0-1.0':raise ValueError('Reviewed source license required')
    folder=ROOT/'unreal/Saved/NativeDemoSedanSource';folder.mkdir(parents=True,exist_ok=True)
    target=folder/'graphite_sedan.glb'
    def valid(path):
        return path.is_file() and path.stat().st_size==item['bytes'] and hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']
    if target.exists():
        if not valid(target):raise ValueError('Existing source preserved: identity mismatch')
    else:
        temporary=folder/('download-'+uuid.uuid4().hex+'.part')
        try:
            subprocess.run(['curl.exe' if os.name=='nt' else 'curl','-fSL','--max-time','120','--max-filesize',str(item['bytes']),item['download'],'-o',str(temporary)],check=True)
            if not valid(temporary):raise ValueError('Downloaded sedan integrity mismatch')
            temporary.replace(target)
        finally:
            if temporary.exists():temporary.unlink()
    print('Verified original CC0 sedan source; rig, doors and gameplay are not yet validated.')
if __name__=='__main__':main()
