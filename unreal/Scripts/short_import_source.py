"""Make hash-owned short-name GLB import copies without changing source geometry or credits."""
from pathlib import Path
import hashlib
import json
import os
import struct
import tempfile

JSON_CHUNK = 0x4E4F534A


def normalized_glb(data):
    if len(data) < 20 or struct.unpack_from('<III', data) != (0x46546C67, 2, len(data)):
        raise ValueError('Invalid GLB header')
    chunks, offset = [], 12
    while offset < len(data):
        if offset + 8 > len(data):
            raise ValueError('Truncated GLB chunk')
        size, kind = struct.unpack_from('<II', data, offset)
        offset += 8
        if size % 4 or offset + size > len(data):
            raise ValueError('Invalid GLB chunk length')
        chunks.append((kind, data[offset:offset+size]))
        offset += size
    if not chunks or chunks[0][0] != JSON_CHUNK:
        raise ValueError('GLB JSON chunk missing')
    doc = json.loads(chunks[0][1])
    # These standard names label indexed objects; geometry and all index references stay intact.
    # Keep asset.copyright, extras, extensions and original credited source files unchanged.
    for collection, prefix in [('meshes','m'),('materials','a'),('textures','t'),('images','i'),('nodes','n'),('scenes','s')]:
        for index, obj in enumerate(doc.get(collection, [])):
            if 'name' in obj:
                obj['name'] = f'{prefix}{index}'
    # Imports must be self-contained; renaming a source file must not break relative dependencies.
    for obj in doc.get('buffers', []) + doc.get('images', []):
        if 'uri' in obj and not obj['uri'].startswith('data:'):
            raise ValueError('External GLB dependency is not supported by the short-name adapter')
    text = json.dumps(doc, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    chunks[0] = (JSON_CHUNK, text + b' ' * (-len(text) % 4))
    body = b''.join(struct.pack('<II', len(payload), kind)+payload for kind, payload in chunks)
    return struct.pack('<III', 0x46546C67, 2, 12+len(body))+body


def prepare_short_import(project, source, expected_sha):
    project, source = Path(project), Path(source)
    original = source.read_bytes()
    if hashlib.sha256(original).hexdigest() != expected_sha:
        raise ValueError('Original import source hash mismatch')
    normalized = normalized_glb(original)
    digest = hashlib.sha256(normalized).hexdigest()
    folder = project/'SourceAssets/ImportInputs'/digest[:16]
    target = folder/'m.glb'
    if target.exists():
        if target.read_bytes() != normalized:
            raise ValueError('Modified import copy preserved: '+str(target))
    else:
        folder.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix='input-', suffix='.tmp', dir=folder)
        try:
            with os.fdopen(fd, 'wb') as output:
                output.write(normalized)
            # Never replace a pre-existing artist/user file.
            try:
                os.link(temporary, target)  # Atomic creation; cannot replace an existing path.
            except FileExistsError:
                if target.read_bytes() != normalized:
                    raise ValueError('Existing import copy preserved: '+str(target))
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    return target, dict(originalSHA256=expected_sha, importSHA256=digest, objectNamesShortened=True,
                        geometryChanged=False, copyrightPreserved=True)


def canonical_destination(group, original):
    # Preserve partial v1 imports and their materials instead of overwriting them.
    return original.replace('/NamedVehicles1/', '/NamedVehicles2/') if group == 'NamedVehicles1' else original


def review_version(group):
    return 'v2' if group == 'NamedVehicles1' else 'v1'
