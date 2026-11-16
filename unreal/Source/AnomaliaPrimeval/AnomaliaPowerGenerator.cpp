#include "AnomaliaPowerGenerator.h"
#include "AnomaliaGameMode.h"
#include "AnomaliaSurvivor.h"
#include "Components/PrimitiveComponent.h"
#include "Engine/World.h"
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
    SetReplicateMovement(true);
    PrimaryActorTick.bCanEverTick = true;
    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    RootComponent = SceneRoot;
    VisualMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("VisualMesh"));
    VisualMesh->SetupAttachment(SceneRoot);
    VisualMesh->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
}

bool AAnomaliaPowerGenerator::TryPickupOnServer(AAnomaliaSurvivor* Player)
{
    if (!HasAuthority() || !IsValid(Player) || Player->Health <= 0.f ||
        IsValid(Carrier) || bRunning || Player->GetWorld() != GetWorld() ||
        FVector::DistSquared(Player->GetActorLocation(), GetActorLocation()) > FMath::Square(300.f)) return false;
    Carrier = Player;
    SetActorEnableCollision(false);
    AttachToComponent(Player->GetRootComponent(), FAttachmentTransformRules::KeepWorldTransform);
    SetActorRelativeLocation(FVector(45.f, 65.f, 60.f));
    ForceNetUpdate();
    return true;
}

bool AAnomaliaPowerGenerator::TryPlaceOnServer(AAnomaliaSurvivor* Player)
{
    if (!HasAuthority() || !IsValid(Player) || Carrier != Player || !GetWorld()) return false;
    const FVector Ahead = Player->GetActorLocation() + Player->GetActorForwardVector() * 160.f;
    FHitResult Ground;
    FCollisionQueryParams Params(SCENE_QUERY_STAT(PortableGeneratorGround), false, Player);
    Params.AddIgnoredActor(this);
    if (!GetWorld()->LineTraceSingleByChannel(Ground, Ahead + FVector(0, 0, 160.f),
            Ahead - FVector(0, 0, 300.f), ECC_Visibility, Params) ||
        !Ground.ImpactNormal.Equals(FVector::UpVector, .35f)) return false;
    DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);
    const FVector Location = Ground.ImpactPoint + FVector(0, 0, 35.f);
    Carrier = nullptr;
    SetActorLocation(Location, false);
    SetActorRotation(FRotator(0.f, Player->GetActorRotation().Yaw, 0.f));
    SetActorEnableCollision(true);
    ForceNetUpdate();
    return true;
}

void AAnomaliaPowerGenerator::OnRep_Carrier()
{
    SetActorEnableCollision(!IsValid(Carrier));
}

bool AAnomaliaPowerGenerator::SetRunningOnServer(bool bStart)
{
    if (!HasAuthority() || (bStart && (FuelLitres <= 0.f || IsValid(Carrier)))) return false;
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
        !IsValid(Carrier) && bRunning && FuelLitres > 0.f &&
        FVector::DistSquared(Target->GetActorLocation(), GetActorLocation()) <= FMath::Square(MaxCableDistanceCm);
}

void AAnomaliaPowerGenerator::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!HasAuthority() || !FMath::IsFinite(DeltaSeconds) || DeltaSeconds <= 0.f) return;
    if (IsValid(Carrier) && (Carrier->Health <= 0.f || !IsValid(Carrier->GetController())))
    {
        DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);
        Carrier = nullptr;
        SetActorEnableCollision(true);
        ForceNetUpdate();
    }
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
    // Legacy save compatibility. Newer saves also store final ground location.
    const TSharedPtr<FJsonObject>* PositionPtr = nullptr;
    if (Root->TryGetObjectField(TEXT("position"), PositionPtr))
    {
        if (!PositionPtr || !PositionPtr->IsValid()) return false;
        double X=0, Y=0, Z=0, Yaw=0;
        if (!(*PositionPtr)->TryGetNumberField(TEXT("x"), X) ||
            !(*PositionPtr)->TryGetNumberField(TEXT("y"), Y) ||
            !(*PositionPtr)->TryGetNumberField(TEXT("z"), Z) ||
            !(*PositionPtr)->TryGetNumberField(TEXT("yaw"), Yaw) ||
            !FMath::IsFinite(X) || !FMath::IsFinite(Y) ||
            !FMath::IsFinite(Z) || !FMath::IsFinite(Yaw) ||
            FMath::Abs(X) > 2400000 || FMath::Abs(Y) > 2400000 || FMath::Abs(Z) > 2400000) return false;
        SetActorLocationAndRotation(FVector(X, Y, Z), FRotator(0.f, static_cast<float>(Yaw), 0.f));
    }
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
    if (!IsValid(Carrier))
    {
        TSharedRef<FJsonObject> Position = MakeShared<FJsonObject>();
        const FVector P = GetActorLocation();
        Position->SetNumberField(TEXT("x"), P.X);
        Position->SetNumberField(TEXT("y"), P.Y);
        Position->SetNumberField(TEXT("z"), P.Z);
        Position->SetNumberField(TEXT("yaw"), GetActorRotation().Yaw);
        Root->SetObjectField(TEXT("position"), Position);
    }
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
    DOREPLIFETIME(AAnomaliaPowerGenerator, Carrier);
}
