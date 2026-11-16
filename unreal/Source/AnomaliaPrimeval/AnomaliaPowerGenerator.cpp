#include "AnomaliaPowerGenerator.h"
#include "AnomaliaGameMode.h"
#include "Dom/JsonObject.h"
#include "HAL/FileManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Net/UnrealNetwork.h"

AAnomaliaPowerGenerator::AAnomaliaPowerGenerator()
{
    bReplicates = true;
    PrimaryActorTick.bCanEverTick = true;
    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    RootComponent = SceneRoot;
    VisualMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("VisualMesh"));
    VisualMesh->SetupAttachment(SceneRoot);
}

bool AAnomaliaPowerGenerator::SetRunningOnServer(bool bStart)
{
    if (!HasAuthority() || (bStart && FuelLitres <= 0.f)) return false;
    bRunning = bStart;
    ForceNetUpdate();
    return true;
}

bool AAnomaliaPowerGenerator::RefuelOnServer(float Litres)
{
    if (!HasAuthority() || !FMath::IsFinite(Litres) || Litres <= 0.f || Litres > 30.f) return false;
    FuelLitres = FMath::Clamp(FuelLitres + Litres, 0.f, 30.f);
    ForceNetUpdate();
    return true;
}

bool AAnomaliaPowerGenerator::IsSupplyingActor(const AActor* Target) const
{
    return IsValid(Target) && Target->GetWorld() == GetWorld() &&
        bRunning && FuelLitres > 0.f &&
        FVector::DistSquared(Target->GetActorLocation(), GetActorLocation()) <= FMath::Square(MaxCableDistanceCm);
}

void AAnomaliaPowerGenerator::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!HasAuthority() || !FMath::IsFinite(DeltaSeconds) || DeltaSeconds <= 0.f) return;
    if (bRunning)
    {
        FuelLitres = FMath::Max(0.f, FuelLitres - DeltaSeconds * LitresPerHour / 3600.f);
        if (FuelLitres <= 0.f) bRunning = false;
    }
    SaveElapsedSeconds += DeltaSeconds;
    if (bPersistenceEnabled && SaveElapsedSeconds >= 60.f)
    {
        SaveElapsedSeconds = 0.f;
        if (!SaveServerState()) UE_LOG(LogTemp, Warning, TEXT("ANOMALIA generator %s: autosave failed"), *PersistentId);
    }
}


static bool AnomaliaValidGeneratorId(const FString& Id)
{
    if (Id.IsEmpty() || Id.Len() > 64) return false;
    for (TCHAR C : Id)
        if (C > 127 || !(FChar::IsAlnum(C) || C == TEXT('_') || C == TEXT('-'))) return false;
    return true;
}

bool AAnomaliaPowerGenerator::GetSavePath(FString& OutFile) const
{
    OutFile.Empty();
    const AAnomaliaGameMode* Mode = GetWorld() ? Cast<AAnomaliaGameMode>(GetWorld()->GetAuthGameMode()) : nullptr;
    if (!Mode || !AnomaliaValidGeneratorId(Mode->ServerId) || !AnomaliaValidGeneratorId(PersistentId)) return false;
    OutFile = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Servers"), Mode->ServerId,
        TEXT("generators"), PersistentId + TEXT(".json"));
    return true;
}

bool AAnomaliaPowerGenerator::LoadServerState()
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
    double Schema = 0, Fuel = 0;
    bool bWasRunning = false;
    if (!Root->TryGetNumberField(TEXT("schemaVersion"), Schema) || Schema != 1 ||
        !Root->TryGetNumberField(TEXT("fuelLitres"), Fuel) || !FMath::IsFinite(Fuel) || Fuel < 0 || Fuel > 30 ||
        !Root->TryGetBoolField(TEXT("running"), bWasRunning)) return false;
    FuelLitres = static_cast<float>(Fuel);
    bRunning = bWasRunning && FuelLitres > 0.f;
    ForceNetUpdate();
    return true;
}

bool AAnomaliaPowerGenerator::SaveServerState() const
{
    FString File;
    if (!HasAuthority() || !GetSavePath(File)) return false;
    TSharedRef<FJsonObject> Root = MakeShared<FJsonObject>();
    Root->SetNumberField(TEXT("schemaVersion"), 1);
    Root->SetNumberField(TEXT("fuelLitres"), FuelLitres);
    Root->SetBoolField(TEXT("running"), bRunning);
    FString Text;
    if (!FJsonSerializer::Serialize(Root, TJsonWriterFactory<>::Create(&Text))) return false;
    if (!IFileManager::Get().MakeDirectory(*FPaths::GetPath(File), true)) return false;
    const FString Tmp = File + TEXT(".tmp");
    if (!FFileHelper::SaveStringToFile(Text, *Tmp, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM)) return false;
    if (!IFileManager::Get().Move(*File, *Tmp, true, true))
    {
        IFileManager::Get().Delete(*Tmp);
        return false;
    }
    return true;
}

void AAnomaliaPowerGenerator::BeginPlay()
{
    Super::BeginPlay();
    if (!HasAuthority()) return;
    bPersistenceEnabled = LoadServerState();
    if (!bPersistenceEnabled)
        UE_LOG(LogTemp, Warning, TEXT("ANOMALIA generator '%s': invalid persistence ID or save; writes disabled"), *PersistentId);
}

void AAnomaliaPowerGenerator::EndPlay(const EEndPlayReason::Type Reason)
{
    if (HasAuthority() && bPersistenceEnabled && !SaveServerState())
        UE_LOG(LogTemp, Warning, TEXT("ANOMALIA generator '%s': shutdown save failed"), *PersistentId);
    Super::EndPlay(Reason);
}

void AAnomaliaPowerGenerator::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AAnomaliaPowerGenerator, bRunning);
    DOREPLIFETIME(AAnomaliaPowerGenerator, FuelLitres);
}
