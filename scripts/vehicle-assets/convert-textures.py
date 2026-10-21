"""Convert embedded review textures with Pillow in the isolated asset Python process."""
import json
from pathlib import Path
import sys
from PIL import Image
folder=Path(sys.argv[1]);spec=json.loads((folder/'textures.json').read_text())
for item in spec:
    if Path(item['input']).name!=item['input'] or Path(item['output']).name!=item['output']:raise RuntimeError('Invalid temporary texture path')
    with Image.open(folder/item['input']) as image:
        image=image.convert('RGBA');image.thumbnail((1024,1024),Image.Resampling.LANCZOS);image.save(folder/item['output'],format='PNG',optimize=False)
