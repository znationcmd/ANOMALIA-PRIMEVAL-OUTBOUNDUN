"""Repair the current Windows native project without changing maps or saves."""
import argparse, hashlib, json, re, shutil
from pathlib import Path

MEDIA = {
    'INTRO_JEU_24s_MUSIQUE.mp4': 'f88c9016797361b3b5341afc23a3530df029a0c65815e36127efde6d618f3b5b',
    'ANOMALIAZ_PRIGIMALIA_Clic_Sang_6s.mp4': 'e9c7b9659babf09bae103b508a2982c528173c6b5a3c1ac34dcfb19cd3900a15',
    'VOIX_ET_SON_ORIGINAUX_NON_MODIFIES.wav': '2404b40734cd597c755a1564c8467691e218d8e6260062713afa92b5f0d13dff',
}

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',required=True)
    p.add_argument('--bundle',required=True)
    p.add_argument('--report',required=True)
    a=p.parse_args()
    root=Path(a.root).resolve(); bundle=Path(a.bundle).resolve(); report=Path(a.report).resolve()
    if root != Path('D:/ANOMALIA/unreal').resolve():
        raise RuntimeError('Expected current main native project')
    project=root/'AnomaliaPrimeval.uproject'
    meta=json.loads(project.read_text(encoding='utf-8-sig'))
    if 'AnomaliaPrimeval' not in [m['Name'] for m in meta['Modules']]:
        raise RuntimeError('Unexpected native module')
    out=report.parent; out.mkdir(parents=True,exist_ok=True)
    backup=out/'before'; backup.mkdir(exist_ok=False)
    src=root/'Source/AnomaliaPrimeval'
    game=src/'AnomaliaGameMode.cpp'; widget=src/'AnomaliaSessionWidget.cpp'; build=src/'AnomaliaPrimeval.Build.cs'
    g=game.read_text(encoding='utf-8-sig'); w=widget.read_text(encoding='utf-8-sig'); b=build.read_text(encoding='utf-8-sig')
    if 'UAnomaliaSessionWidget::Open(PC,true)' not in g and 'UAnomaliaIntroWidget::Open(PC)' not in g:
        raise RuntimeError('Expected existing native menu startup was not found')
    replacements=[]
    for m in re.finditer(r'(?m)^([ \t]*)if\s*\((GetNetMode\(\)==NM_Standalone[^\r\n]+)\)\s*$',g):
        following=g[m.end():m.end()+600]
        if 'SessionWidget::Open(PC,true)' not in following and 'IntroWidget::Open(PC)' not in following:
            continue
        condition=re.sub(r'\s*&&\s*GetWorld\(\)->GetMapName\(\)\.EndsWith\(TEXT\("[^"]+"\)\)', '', m[2])
        if 'AnomaliaSkipMainMenu' not in condition:
            condition+=' && !FParse::Param(FCommandLine::Get(),TEXT("AnomaliaSkipMainMenu"))'
        replacements.append((m.start(),m.end(),m[1]+'if('+condition+')'))
    if len(replacements)!=1:
        raise RuntimeError('Expected one native main-menu startup condition, found '+str(len(replacements)))
    start,end,new=replacements[0]; g=g[:start]+new+g[end:]
    w=re.sub(r'(if\(bMainMenu && PC && GetWorld\(\)) && GetWorld\(\)->GetMapName\(\)\.EndsWith\(TEXT\("[^"]+"\)\)',r'\1',w)
    # Restore the existing native intro; asset filenames remain the approved originals.
    intro_include='#include "AnomaliaIntroWidget.h"'
    if intro_include not in g:
        anchor='#include "AnomaliaSessionWidget.h"'
        if anchor not in g: raise RuntimeError('Missing existing menu include')
        g=g.replace(anchor,anchor+'\n'+intro_include,1)
    if 'UAnomaliaIntroWidget::Open(PC)' not in g:
        g=g.replace('UAnomaliaSessionWidget::Open(PC,true);','if(!UAnomaliaIntroWidget::Open(PC)) UAnomaliaSessionWidget::Open(PC,true);',1)
    if '"MediaAssets"' not in b:
        anchor='PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;'
        if anchor not in b: raise RuntimeError('Unexpected native module constructor')
        b=b.replace(anchor,anchor+'\n        PrivateDependencyModuleNames.Add("MediaAssets");',1)
    changes={game:g,widget:w,build:b}
    for ext in ('cpp','h'):
        text=(bundle/('AnomaliaZPrigimaliaIntroWidget.'+ext)).read_text(encoding='utf-8-sig')
        text=text.replace('ANOMALIAZPRIGIMALIA_API','ANOMALIAPRIMEVAL_API').replace('AnomaliaZPrigimalia','Anomalia')
        changes[src/('AnomaliaIntroWidget.'+ext)]=text
    importer=(bundle/'install_prigimalia_intro.py').read_text(encoding='utf-8-sig')
    importer=importer.replace('AnomaliaZPrigimalia.uproject','AnomaliaPrimeval.uproject').replace('AnomaliaZPrigimalia','Anomalia')
    changes[root/'Scripts/install_current_main_intro.py']=importer
    ini=root/'Config/DefaultGame.ini'; config=ini.read_text(encoding='utf-8-sig')
    needed=['+DirectoriesToAlwaysStageAsNonUFS=(Path="Movies")','+DirectoriesToAlwaysCook=(Path="/Game/Anomalia/Branding")']
    missing=[line for line in needed if line not in config]
    if missing: config+='\n[/Script/UnrealEd.ProjectPackagingSettings]\n'+'\n'.join(missing)+'\n'
    changes[ini]=config
    launcher=root/'Launcher/Launch-Current-Anomalia.ps1'
    if launcher.exists():
        launch=launcher.read_text(encoding='utf-8-sig')
        if '[switch]$ChooseMap' not in launch:
            launch=launch.replace('[switch]$ValidateOnly)', '[switch]$ValidateOnly,[switch]$ChooseMap)',1)
            anchor='  if($MapId){'
            if anchor not in launch: raise RuntimeError('Unexpected current launcher')
            launch=launch.replace(anchor,'  if(!$MapId -and !$ChooseMap){$MapId=[string]$c.defaultMap}\n'+anchor,1)
        changes[launcher]=launch
    folders=[root/'Content/Movies',root/'SourceAssets/Intro',Path('D:/ANOMALIAZ-PRIGIMALIA/unreal/Content/Movies'),Path('D:/ANOMALIAZ-PRIGIMALIA/unreal/SourceAssets/Intro'),Path('C:/ANOMALIAZ_SKARVIK_STAGE_41188816555/unreal/Content/Movies')]
    found={}
    for name,expected in MEDIA.items():
        for folder in folders:
            f=folder/name
            if f.is_file() and digest(f)==expected:
                found[name]=f; break
    # Known installation ZIP locations only; do not crawl unrelated user files.
    import zipfile
    if len(found)<len(MEDIA):
        candidates=[]
        for folder in [Path.home()/'Downloads',Path.home()/'Desktop',Path('D:/ANOMALIA')]:
            if folder.exists(): candidates.extend(folder.glob('ANOMALIAZ_INSTALLATION_VRAI_JEU_30s*.zip'))
        for archive in candidates:
            with zipfile.ZipFile(archive) as z:
                for name,expected in MEDIA.items():
                    if name in found or name not in z.namelist(): continue
                    data=z.read(name)
                    if hashlib.sha256(data).hexdigest()!=expected: continue
                    dst=out/'approved-media'/name; dst.parent.mkdir(parents=True,exist_ok=True); dst.write_bytes(data); found[name]=dst
    manifest=[]
    for target,text in changes.items():
        if target.exists():
            save=backup/target.relative_to(root); save.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(target,save)
            if digest(save)!=digest(target):raise RuntimeError('Backup mismatch')
            manifest.append({'original':str(target),'backup':str(save)})
    for target,text in changes.items():
        target.parent.mkdir(parents=True,exist_ok=True); target.write_text(text,encoding='utf-8')
    for name,source in found.items():
        for folder in [root/'SourceAssets/Intro']+([root/'Content/Movies'] if name.endswith('.mp4') else []):
            target=folder/name; target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists() and digest(target)!=MEDIA[name]:
                shutil.copy2(target,backup/('previous-'+name))
            if source.resolve()!=target.resolve(): shutil.copy2(source,target)
            if digest(target)!=MEDIA[name]: raise RuntimeError('Approved media copy mismatch')
    result={'state':'NATIVE_MENU_AND_INTRO_SOURCE_STAGED','project':str(project),'menuMapRestrictionRemoved':True,'launcherOpensNativeGameDirectly':launcher.exists(),'approvedMediaFound':list(found),'missingMedia':[n for n in MEDIA if n not in found],'backupManifest':manifest,'introPlaybackVerified':False,'packagedGameUpdated':False}
    report.write_text(json.dumps(result,indent=2),encoding='utf-8'); print(json.dumps(result,indent=2))

if __name__=='__main__':main()
