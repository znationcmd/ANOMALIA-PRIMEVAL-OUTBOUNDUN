"""Fetch individually licensed world features using pinned public distribution bytes."""
import concurrent.futures
import hashlib
import json
import os
import subprocess
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'unreal/SourceAssets/WorldFeatures1'

def fetch(item):
    if item['license'] != 'CC-BY-4.0':
        raise ValueError('Unreviewed license')
    target = BASE / item['file']
    if target.parent.resolve() != BASE.resolve():
        raise ValueError('Invalid source path')
    def valid(path):
        return (path.is_file() and path.stat().st_size == item['bytes']
                and hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256'])
    if target.exists():
        if not valid(target):
            raise ValueError('Existing source preserved: ' + str(target))
        return
    part = target.with_name(target.name + '.part-' + uuid.uuid4().hex)
    try:
        subprocess.run(['curl.exe' if os.name == 'nt' else 'curl', '-fSL', '--retry', '2',
                        '--max-time', '300', item['download'], '-o', str(part)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        if not valid(part):
            raise ValueError('Pinned model identity mismatch: ' + item['id'])
        part.replace(target)
    finally:
        part.unlink(missing_ok=True)

def main():
    registry = json.loads((ROOT / 'docs/art/world-features-sources.json').read_text())
    BASE.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(fetch, registry['models']))
    print('Verified world features:', len(registry['models']))

if __name__ == '__main__':
    main()
