import hashlib,json,shutil,os
from pathlib import Path
here=Path(__file__).parent;root=Path(r'D:\ANOMALIAZ\01_Projet_Principal\unreal');out=Path(os.environ['SCENE_REPAIR_OUT'])
source=here/'AnomaliaAuthenticGameProbe.cpp';target=root/'Source/AnomaliaPrimeval/AnomaliaAuthenticGameProbe.cpp'
def sha(p):return hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
if sha(target) not in [json.loads((here/'previous-probe.json').read_text())['sha256'],sha(source)]:raise RuntimeError('Existing native proof source changed; preserve it')
backup=out/'ProbeSourceBackup/AnomaliaAuthenticGameProbe.cpp';backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,backup);shutil.copy2(source,target)
