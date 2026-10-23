"""Read only known ANOMALIA installation identities; never open player save files."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(os.environ['ANOMALIA_INSTALLED_STATE_REPORT'])
base = Path(os.environ['LOCALAPPDATA'])
report = dict(state='INSTALLED_VERSION_INVENTORY_READ_ONLY', sourceCommit=os.environ.get('GITHUB_SHA'), installations=[])
for relative, expected in [('CMD/ANOMALIA-Windows','ANOMALIA-WINDOWS-TEST-v1'),('CMD/ANOMALIA-UE5','ANOMALIA-UE5-EDITOR-v1')]:
    root=base/relative; row=dict(kind=expected, exists=root.is_dir(), ownerVerified=False)
    if root.is_dir():
        try:
            identity=json.loads((root/'owner.json').read_text(encoding='utf-8-sig'))
            row['ownerVerified']=identity.get('product')==expected
            if row['ownerVerified'] and (root/'active.json').is_file():
                active=json.loads((root/'active.json').read_text(encoding='utf-8-sig'))
                row.update(activeCommit=active.get('commit'),activeState=active.get('state'),
                           activeExecutablePresent=Path(active.get('executable',active.get('project',''))).is_file())
            row['sharedSaveDirectoryPresent']=(root/'userdata/Saved').is_dir()
        except (OSError,ValueError) as error: row['identityReadError']=type(error).__name__
    report['installations'].append(row)
if os.name=='nt':
    import winreg
    report['registeredApplications']=[]
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Microsoft\Windows\CurrentVersion\Uninstall') as uninstall:
            for index in range(winreg.QueryInfoKey(uninstall)[0]):
                try:
                    with winreg.OpenKey(uninstall,winreg.EnumKey(uninstall,index)) as key:
                        name=winreg.QueryValueEx(key,'DisplayName')[0]
                        if 'ANOMALIA' not in name.upper(): continue
                        try: version=winreg.QueryValueEx(key,'DisplayVersion')[0]
                        except OSError: version=None
                        report['registeredApplications'].append(dict(name=name,version=version))
                except OSError: pass
    except OSError: pass
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
