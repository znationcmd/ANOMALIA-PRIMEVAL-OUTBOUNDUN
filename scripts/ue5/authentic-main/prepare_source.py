"""Patch the authoritative native project, preserving its existing real gameplay code."""
from pathlib import Path
import argparse, shutil, json, hashlib


def patch_game_mode(cpp, header):
    marker = 'ANOMALIA_AUTHENTIC_INSTALL'
    if marker in cpp:
        return cpp, header
    cpp = cpp.replace('#include "AnomaliaGameMode.h"', '#include "AnomaliaGameMode.h"\n#include "AnomaliaAuthenticGameProbe.h"\n#include "GameFramework/PlayerStart.h"', 1)
    anchor = 'void AAnomaliaGameMode::BeginPlay()'
    if cpp.count(anchor) != 1:
        raise RuntimeError('Unexpected main GameMode implementation')
    cpp = cpp.replace(anchor, '''// ANOMALIA_AUTHENTIC_INSTALL: use the actual authored city start in this world.
AActor* AAnomaliaGameMode::ChoosePlayerStart_Implementation(AController* Player)
{
    if(GetWorld() && GetWorld()->GetMapName().EndsWith(TEXT("PRIGIMALIA_SKARVIK_FINAL_v1")))
        for(TActorIterator<APlayerStart> It(GetWorld());It;++It)
            if(It->ActorHasTag(TEXT("ANOMALIA_AUTHENTIC_START"))) return *It;
    return Super::ChoosePlayerStart_Implementation(Player);
}

''' + anchor, 1)
    anchor = '        FString ProbeFile;'
    if cpp.count(anchor) != 1:
        raise RuntimeError('Unexpected native validation scope')
    cpp = cpp.replace(anchor, anchor + '''
        if(GetNetMode()==NM_Standalone && ServerId.StartsWith(TEXT("authentic-smoke-")) &&
           GetWorld()->GetMapName().EndsWith(TEXT("PRIGIMALIA_SKARVIK_FINAL_v1")) &&
           FParse::Value(FCommandLine::Get(),TEXT("AnomaliaAuthenticProbe="),ProbeFile) && !ProbeFile.IsEmpty())
            GetWorld()->SpawnActor<AAnomaliaAuthenticGameProbe>();
''', 1)
    anchor = 'GetWorld()->GetMapName().EndsWith(TEXT("ANOMALIA_Playable_v1")) && !ServerId.StartsWith(TEXT("playable-smoke-"))'
    if cpp.count(anchor) != 1:
        raise RuntimeError('Cannot identify original main-menu entry condition')
    cpp = cpp.replace(anchor, '(GetWorld()->GetMapName().EndsWith(TEXT("ANOMALIA_Playable_v1")) || GetWorld()->GetMapName().EndsWith(TEXT("PRIGIMALIA_SKARVIK_FINAL_v1"))) && !ServerId.StartsWith(TEXT("playable-smoke-")) && !ServerId.StartsWith(TEXT("authentic-smoke-"))', 1)
    anchor = '    virtual void BeginPlay() override;'
    if header.count(anchor) != 1:
        raise RuntimeError('Cannot identify native GameMode declaration')
    header = header.replace(anchor, anchor + '\n    virtual AActor* ChoosePlayerStart_Implementation(AController* Player) override;', 1)
    return cpp, header


def patch_menu(cpp):
    if 'ANOMALIA_AUTHENTIC_MENU' in cpp:
        return cpp
    a = cpp.index('void UAnomaliaSessionWidget::NativeConstruct()')
    b = cpp.index('void UAnomaliaSessionWidget::NativeDestruct()', a)
    cpp = cpp[:a] + '''// ANOMALIA_AUTHENTIC_MENU: the camera shows the actual restored character and world.
void UAnomaliaSessionWidget::NativeConstruct()
{
    Super::NativeConstruct();SetIsFocusable(true);bStartupIntro=false;
    if(MenuArtwork) MenuArtwork->SetVisibility(ESlateVisibility::Collapsed);
    if(NavigationFrame) NavigationFrame->SetVisibility(ESlateVisibility::Visible);
    auto* PC=GetOwningPlayer();
    auto* Survivor=PC?Cast<AAnomaliaSurvivor>(PC->GetPawn()):nullptr;
    if(bMainMenu && Survivor && GetWorld())
    {
        const FVector Center=Survivor->GetActorLocation()+FVector(0,0,100);
        const FVector Eye=Center+Survivor->GetActorForwardVector()*285.f+Survivor->GetActorRightVector()*140.f+FVector(0,0,60);
        FActorSpawnParameters Params;Params.ObjectFlags|=RF_Transient;
        MenuCamera=GetWorld()->SpawnActor<ACameraActor>(ACameraActor::StaticClass(),Eye,(Center-Eye).Rotation(),Params);
        if(MenuCamera)
        {
            MenuCamera->GetCameraComponent()->SetFieldOfView(55.f);
            PreviousViewTarget=PC->GetViewTarget();PC->SetViewTarget(MenuCamera);
            if(PC->PlayerCameraManager)PC->PlayerCameraManager->UpdateCamera(0.f);
        }
    }
}
''' + cpp[b:]
    start = cpp.index('void UAnomaliaSessionWidget::BuildLayout()')
    head, body = cpp[:start], cpp[start:]
    body = body.replace('if(Texture)', 'if(false && Texture)', 1)
    body = body.replace('FAnchors(.035f,.12f,.31f,.77f)', 'FAnchors(.68f,.15f,.97f,.85f)', 1)
    body = body.replace('TEXT("ANOMALIA")', 'TEXT("ANOMALIA’Z PRIGIMALIA")', 1)
    line = '    ModsButton=Button(TEXT("SessionMods"),TEXT("Mods")); ModsButton->OnClicked.AddDynamic(this,&UAnomaliaSessionWidget::ShowMods);'
    if body.count(line) != 1:
        raise RuntimeError('Cannot safely isolate WorkForge main-menu entry')
    body = body.replace(line, '    if(bMainMenu) { ModsButton=Button(TEXT("SessionMods"),TEXT("WORKFORGE  •  MODS")); ModsButton->OnClicked.AddDynamic(this,&UAnomaliaSessionWidget::ShowMods); }', 1)
    body = body.replace('    BuildPremiumWorkshop(Canvas);', '    if(bMainMenu) BuildPremiumWorkshop(Canvas);', 1)
    anchor = 'void UAnomaliaSessionWidget::ShowMods()\n{'
    if body.count(anchor) != 1:
        raise RuntimeError('Unexpected WorkForge callback')
    body = body.replace(anchor, anchor + '\n    if(!bMainMenu || !WorkshopFrame) return;', 1)
    return head + body


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    if root != Path(r'D:\ANOMALIAZ\01_Projet_Principal\unreal').resolve():
        raise RuntimeError('Unexpected authoritative project root')
    module = root / 'Source' / 'AnomaliaPrimeval'
    original = {name: (module/name).read_text(encoding='utf-8-sig') for name in ['AnomaliaGameMode.cpp', 'AnomaliaGameMode.h', 'AnomaliaSessionWidget.cpp']}
    cpp, header = patch_game_mode(original['AnomaliaGameMode.cpp'], original['AnomaliaGameMode.h'])
    changes = {'AnomaliaGameMode.cpp': cpp, 'AnomaliaGameMode.h': header, 'AnomaliaSessionWidget.cpp': patch_menu(original['AnomaliaSessionWidget.cpp'])}
    args.output.mkdir(parents=True, exist_ok=True)
    receipt = {'files': []}
    for name, text in changes.items():
        target = module/name
        backup = args.output/(name+'.before')
        if not backup.exists():
            shutil.copy2(target, backup)
        before = hashlib.sha256(target.read_bytes()).hexdigest()
        if target.read_text(encoding='utf-8-sig') != text:
            target.write_text(text, encoding='utf-8')
        receipt['files'].append({'path': str(target), 'before': before, 'after': hashlib.sha256(target.read_bytes()).hexdigest()})
    for name in ['AnomaliaAuthenticGameProbe.h', 'AnomaliaAuthenticGameProbe.cpp']:
        target = module/name
        source = Path(__file__).with_name(name)
        if target.exists() and target.read_bytes()!=source.read_bytes():
            shutil.copy2(target, args.output/(name+'.before'))
        if not target.exists() or target.read_bytes()!=source.read_bytes():
            shutil.copyfile(source, target)
            target.touch()
    (args.output/'source-install.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
