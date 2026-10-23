"""Download pinned CC0 4K marine terrain textures without replacing existing files."""
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import subprocess
import uuid

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'unreal/SourceAssets/MarineTerrain_v1'

def fetch(item):
    target = BASE / item['path']
    if target.parent.resolve() != BASE.resolve():
        raise ValueError('Unsafe texture path')
    def valid(path):
        return (path.is_file() and path.stat().st_size == item['bytes']
                and hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256'])
    if target.exists():
        if not valid(target):
            raise RuntimeError('Existing source preserved: ' + str(target))
        return
    part = target.with_name(target.name + '.part-' + uuid.uuid4().hex)
    try:
        subprocess.run(['curl.exe' if os.name == 'nt' else 'curl', '-fSL', '--retry', '2',
                        '--max-time', '300', item['url'], '-o', str(part)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        if not valid(part):
            raise RuntimeError('Texture identity mismatch: ' + item['path'])
        part.replace(target)
    finally:
        part.unlink(missing_ok=True)

def main():
    registry = json.loads((ROOT / 'docs/art/marine-terrain-sources.json').read_text())
    if len(registry['models']) != 2 or any(m['license'] != 'CC0-1.0' for m in registry['models']):
        raise RuntimeError('Unreviewed marine material registry')
    BASE.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(fetch, [f for m in registry['models'] for f in m['files']]))
    print('Verified six pinned 4096px marine terrain textures.')

if __name__ == '__main__':
    main()
