"""Create Windows executable and installer icon from CMD's uploaded ANOMALIA emblem."""
from pathlib import Path
from PIL import Image, ImageOps
source=Path("build/prigimalia-logo-small.jpg")
target=Path("build/icon.ico")
if not source.is_file():
    raise SystemExit("PRIGIMALIA logo missing: "+str(source))
with Image.open(source) as original:
    image=ImageOps.fit(original.convert("RGBA"),(256,256),method=Image.Resampling.LANCZOS)
    target.parent.mkdir(parents=True,exist_ok=True)
    image.save(target,format="ICO",sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
print("Windows installer icon:",target,"size",target.stat().st_size)
