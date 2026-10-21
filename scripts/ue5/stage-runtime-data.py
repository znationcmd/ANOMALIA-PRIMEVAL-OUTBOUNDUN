"""Stage authoritative catalogue defaults for Unreal and packaged builds; never touch Saved."""
from pathlib import Path
import hashlib
import json
import os
import tempfile

ROOT = Path(__file__).resolve().parents[2]
FILES = ('loot_items_catalog.json', 'loot_tiers.json', 'loot_spawns.json')


def stage(root=ROOT):
    destination = root / 'unreal/Content/Anomalia/Data'
    destination.mkdir(parents=True, exist_ok=True)
    owner_file = destination / 'stage-manifest.json'
    previous = json.loads(owner_file.read_text()) if owner_file.exists() else {'files': {}}
    prepared = {}
    for name in FILES:
        data = (root / 'public/config' / name).read_bytes()
        parsed = json.loads(data)
        if parsed.get('schemaVersion') != 1:
            raise ValueError(f'Unsupported runtime catalogue: {name}')
        target = destination / name
        digest = hashlib.sha256(data).hexdigest()
        if target.exists():
            old = hashlib.sha256(target.read_bytes()).hexdigest()
            if old != digest and previous['files'].get(name) != old:
                raise ValueError(f'Preserving edited or unowned runtime data: {target}')
        prepared[name] = data, digest
    # Validate every input and ownership before updating any runtime default.
    for name, (data, _) in prepared.items():
        fd, temp = tempfile.mkstemp(prefix='stage-', dir=destination)
        try:
            with os.fdopen(fd, 'wb') as stream:
                stream.write(data)
            os.replace(temp, destination / name)
        finally:
            if os.path.exists(temp):
                os.unlink(temp)
    owner_file.write_text(json.dumps({'schemaVersion': 1, 'files': {name: digest for name, (_, digest) in prepared.items()}}, indent=2)+'\n')
    return len(prepared)


if __name__ == '__main__':
    print(f'Staged {stage()} runtime catalogues; server overrides and saves untouched.')
