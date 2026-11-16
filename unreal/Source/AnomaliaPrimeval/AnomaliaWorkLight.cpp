#include "AnomaliaWorkLight.h"
#include "AnomaliaPowerGenerator.h"
#include "AnomaliaGameMode.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SpotLightComponent.h"
#include "Engine/World.h"
#include "Dom/JsonObject.h"
#include "HAL/FileManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Net/UnrealNetwork.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

namespace
{
bool IsValidWorkLightId(const FString& Id)
{
    if (Id.IsEmpty() || Id.Len() > 64) return false;
    for (const TCHAR C : Id)
        if (C > 127 || !(FChar::IsAlnum(C) || C == TEXT('-') || C == TEXT('_'))) return false;
    return true;
}
}

AAnomaliaWorkLight::AAnomaliaWorkLight()
{
    bReplicates = true;
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.TickInterval = .25f;
    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    RootComponent = SceneRoot;
    VisualMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("VisualMesh"));
    VisualMesh->SetupAttachment(SceneRoot);
    FloodBeam = CreateDefaultSubobject<USpotLightComponent>(TEXT("ConstructionSpotlight"));
    FloodBeam->SetupAttachment(SceneRoot);
    FloodBeam->SetRelativeLocation(FVector(0.f, 0.f, 160.f));
    FloodBeam->SetRelativeRotation(FRotator(-35.f, 0.f, 0.f));
    FloodBeam->SetMobility(EComponentMobility::Movable);
    FloodBeam->SetIntensity(90000.f);
    FloodBeam->SetAttenuationRadius(2200.f);
    FloodBeam->SetInnerConeAngle(25.f);
    FloodBeam->SetOuterConeAngle(40.f);
    FloodBeam->SetVisibility(false);
}

bool AAnomaliaWorkLight::SetSwitchedOnServer(bool bOn)
{
    if (!HasAuthority()) return false;
    bSwitchedOn = bOn;
    bIsLit = bSwitchedOn && IsValid(PowerGenerator) && PowerGenerator->IsSupplyingActor(this);
    OnRep_Lit();
    ForceNetUpdate();
    return true;
}

bool AAnomaliaWorkLight::GetSavePath(FString& OutFile) const
{
    OutFile.Empty();
    const AAnomaliaGameMode* Mode = GetWorld() ? Cast<AAnomaliaGameMode>(GetWorld()->GetAuthGameMode()) : nullptr;
    if (!Mode || !IsValidWorkLightId(Mode->ServerId) || !IsValidWorkLightId(PersistentId)) return false;
    OutFile = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Servers"), Mode->ServerId,
        TEXT("construction-lights"), PersistentId + TEXT(".json"));
    return true;
}

bool AAnomaliaWorkLight::LoadServerState()
{
    FString File;
    if (!GetSavePath(File)) return false;
    if (!IFileManager::Get().FileExists(*File)) return true;
    const int64 Bytes = IFileManager::Get().FileSize(*File);
    if (Bytes < 0 || Bytes > 4096) return false;
    FString Raw;
    if (!FFileHelper::LoadFileToString(Raw, *File)) return false;
    TSharedPtr<FJsonObject> Root;
    if (!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Raw), Root) || !Root.IsValid()) return false;
    double Version = 0;
    bool bOn = false;
    if (!Root->TryGetNumberField(TEXT("schemaVersion"), Version) || Version != 1 ||
        !Root->TryGetBoolField(TEXT("switchedOn"), bOn)) return false;
    bSwitchedOn = bOn;
    ForceNetUpdate();
    return true;
}

bool AAnomaliaWorkLight::SaveServerState() const
{
    FString File;
    if (!HasAuthority() || !GetSavePath(File)) return false;
    TSharedRef<FJsonObject> Root = MakeShared<FJsonObject>();
    Root->SetNumberField(TEXT("schemaVersion"), 1);
    Root->SetBoolField(TEXT("switchedOn"), bSwitchedOn);
    FString Text;
    if (!FJsonSerializer::Serialize(Root, TJsonWriterFactory<>::Create(&Text))) return false;
    if (!IFileManager::Get().MakeDirectory(*FPaths::GetPath(File), true)) return false;
    const FString Temp = File + TEXT(".tmp");
    if (!FFileHelper::SaveStringToFile(Text, *Temp, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM)) return false;
    if (!IFileManager::Get().Move(*File, *Temp, true, true))
    {
        IFileManager::Get().Delete(*Temp);
        return false;
    }
    return true;
}

void AAnomaliaWorkLight::BeginPlay()
{
    Super::BeginPlay();
    if (!HasAuthority()) return;
    bPersistenceEnabled = LoadServerState();
    if (!bPersistenceEnabled)
        UE_LOG(LogTemp, Warning, TEXT("ANOMALIA work light '%s': persistence disabled"), *PersistentId);
}

void AAnomaliaWorkLight::EndPlay(const EEndPlayReason::Type Reason)
{
    if (HasAuthority() && bPersistenceEnabled && !SaveServerState())
        UE_LOG(LogTemp, Warning, TEXT("ANOMALIA work light '%s': save failed"), *PersistentId);
    Super::EndPlay(Reason);
}

void AAnomaliaWorkLight::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (HasAuthority())
    {
        const bool bNextLit = bSwitchedOn && IsValid(PowerGenerator) &&
            PowerGenerator->IsSupplyingActor(this);
        if (bNextLit != bIsLit)
        {
            bIsLit = bNextLit;
            ForceNetUpdate();
        }
        if (FMath::IsFinite(DeltaSeconds) && DeltaSeconds > 0.f)
        {
            SaveElapsedSeconds += DeltaSeconds;
            if (bPersistenceEnabled && SaveElapsedSeconds >= 60.f)
            {
                SaveElapsedSeconds = 0.f;
                if (!SaveServerState())
                    UE_LOG(LogTemp, Warning, TEXT("ANOMALIA work light '%s': autosave failed"), *PersistentId);
            }
        }
    }
    OnRep_Lit();
}

void AAnomaliaWorkLight::OnRep_Lit()
{
    if (IsValid(FloodBeam)) FloodBeam->SetVisibility(bIsLit);
}

void AAnomaliaWorkLight::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AAnomaliaWorkLight, PowerGenerator);
    DOREPLIFETIME(AAnomaliaWorkLight, bSwitchedOn);
    DOREPLIFETIME(AAnomaliaWorkLight, bIsLit);
}
