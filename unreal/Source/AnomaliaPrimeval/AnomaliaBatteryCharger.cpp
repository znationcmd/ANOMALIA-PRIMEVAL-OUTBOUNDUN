#include "AnomaliaBatteryCharger.h"
#include "AnomaliaPowerGenerator.h"
#include "AnomaliaGameMode.h"
#include "AnomaliaInventoryComponent.h"
#include "AnomaliaSurvivor.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/PointLightComponent.h"
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
bool ValidApplianceId(const FString& Id)
{
    if (Id.IsEmpty() || Id.Len() > 64) return false;
    for (const TCHAR C : Id)
        if (C > 127 || !(FChar::IsAlnum(C) || C == TEXT('-') || C == TEXT('_'))) return false;
    return true;
}
}

AAnomaliaBatteryCharger::AAnomaliaBatteryCharger()
{
    bReplicates = true;
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.TickInterval = 1.f;
    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    RootComponent = SceneRoot;
    VisualMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("VisualMesh"));
    VisualMesh->SetupAttachment(SceneRoot);
    StatusLED = CreateDefaultSubobject<UPointLightComponent>(TEXT("ChargingLED"));
    StatusLED->SetupAttachment(SceneRoot);
    StatusLED->SetRelativeLocation(FVector(0, 0, 18));
    StatusLED->SetIntensity(150.f);
    StatusLED->SetAttenuationRadius(75.f);
    StatusLED->SetLightColor(FLinearColor(0.08f, 1.f, 0.16f));
    StatusLED->SetVisibility(false);
}

bool AAnomaliaBatteryCharger::IsPlayerInReach(const AAnomaliaSurvivor* Player) const
{
    return HasAuthority() && IsValid(Player) && Player->GetWorld() == GetWorld() &&
        Player->Health > 0.f && IsValid(Player->InventoryComponent) &&
        FVector::DistSquared(GetActorLocation(), Player->GetActorLocation()) <= FMath::Square(300.f);
}

bool AAnomaliaBatteryCharger::InsertBatteryOnServer(AAnomaliaSurvivor* Player)
{
    if (!IsPlayerInReach(Player) || bHasBattery) return false;
    float Freshness = 1.f, Charge = 1.f;
    if (!Player->InventoryComponent->TryRemoveItemWithState(TEXT("car_battery"), 1, Freshness, Charge)) return false;
    BatteryCharge01 = Charge;
    bHasBattery = true;
    ForceNetUpdate();
    return true;
}

bool AAnomaliaBatteryCharger::RemoveBatteryOnServer(AAnomaliaSurvivor* Player)
{
    if (!IsPlayerInReach(Player) || !bHasBattery) return false;
    // Do not clear the charger's slot unless the player's inventory accepted the battery.
    if (!Player->InventoryComponent->TryAddItemWithState(TEXT("car_battery"), 1, 1.f, BatteryCharge01)) return false;
    bHasBattery = false;
    bCharging = false;
    BatteryCharge01 = 0.f;
    ForceNetUpdate();
    return true;
}

bool AAnomaliaBatteryCharger::SetSwitchedOnServer(bool bOn)
{
    if (!HasAuthority()) return false;
    bSwitchedOn = bOn;
    ForceNetUpdate();
    return true;
}

bool AAnomaliaBatteryCharger::GetSavePath(FString& OutFile) const
{
    OutFile.Empty();
    const AAnomaliaGameMode* Game = GetWorld() ? Cast<AAnomaliaGameMode>(GetWorld()->GetAuthGameMode()) : nullptr;
    if (!Game || !ValidApplianceId(Game->ServerId) || !ValidApplianceId(PersistentId)) return false;
    OutFile = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Servers"), Game->ServerId,
        TEXT("battery-chargers"), PersistentId + TEXT(".json"));
    return true;
}

bool AAnomaliaBatteryCharger::LoadServerState()
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
    double Schema = 0, Charge = 0;
    bool bSavedOn = false, bSavedBattery = false;
    if (!Root->TryGetNumberField(TEXT("schemaVersion"), Schema) || Schema != 1 ||
        !Root->TryGetBoolField(TEXT("switchedOn"), bSavedOn) ||
        !Root->TryGetBoolField(TEXT("hasBattery"), bSavedBattery) ||
        !Root->TryGetNumberField(TEXT("charge01"), Charge) ||
        !FMath::IsFinite(Charge) || Charge < 0 || Charge > 1) return false;
    bSwitchedOn = bSavedOn;
    bHasBattery = bSavedBattery;
    BatteryCharge01 = bHasBattery ? static_cast<float>(Charge) : 0.f;
    ForceNetUpdate();
    return true;
}

bool AAnomaliaBatteryCharger::SaveServerState() const
{
    FString File;
    if (!HasAuthority() || !GetSavePath(File)) return false;
    TSharedRef<FJsonObject> Root = MakeShared<FJsonObject>();
    Root->SetNumberField(TEXT("schemaVersion"), 1);
    Root->SetBoolField(TEXT("switchedOn"), bSwitchedOn);
    Root->SetBoolField(TEXT("hasBattery"), bHasBattery);
    Root->SetNumberField(TEXT("charge01"), BatteryCharge01);
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

void AAnomaliaBatteryCharger::BeginPlay()
{
    Super::BeginPlay();
    if (HasAuthority())
    {
        bPersistenceEnabled = LoadServerState();
        if (!bPersistenceEnabled)
            UE_LOG(LogTemp, Warning, TEXT("ANOMALIA battery charger '%s': persistence disabled"), *PersistentId);
    }
}

void AAnomaliaBatteryCharger::EndPlay(const EEndPlayReason::Type Reason)
{
    if (HasAuthority() && bPersistenceEnabled && !SaveServerState())
        UE_LOG(LogTemp, Warning, TEXT("ANOMALIA battery charger '%s': save failed"), *PersistentId);
    Super::EndPlay(Reason);
}

void AAnomaliaBatteryCharger::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!FMath::IsFinite(DeltaSeconds) || DeltaSeconds <= 0.f) return;
    if (HasAuthority())
    {
        const bool bPowered = bSwitchedOn && bHasBattery && BatteryCharge01 < 1.f &&
            IsValid(PowerGenerator) && PowerGenerator->IsSupplyingActor(this);
        if (bCharging != bPowered)
        {
            bCharging = bPowered;
            ForceNetUpdate();
        }
        if (bCharging)
        {
            const float Before = BatteryCharge01;
            BatteryCharge01 = FMath::Min(1.f, BatteryCharge01 + (ChargePercentPerHour / 100.f) *
                DeltaSeconds / 3600.f);
            if (BatteryCharge01 >= 1.f) bCharging = false;
            if (!FMath::IsNearlyEqual(Before, BatteryCharge01, 0.001f)) ForceNetUpdate();
        }
        SaveElapsedSeconds += DeltaSeconds;
        if (bPersistenceEnabled && SaveElapsedSeconds >= 60.f)
        {
            SaveElapsedSeconds = 0.f;
            if (!SaveServerState()) UE_LOG(LogTemp, Warning, TEXT("ANOMALIA battery charger '%s': autosave failed"), *PersistentId);
        }
    }
    if (IsValid(StatusLED)) StatusLED->SetVisibility(bCharging);
}

void AAnomaliaBatteryCharger::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AAnomaliaBatteryCharger, PowerGenerator);
    DOREPLIFETIME(AAnomaliaBatteryCharger, bSwitchedOn);
    DOREPLIFETIME(AAnomaliaBatteryCharger, bHasBattery);
    DOREPLIFETIME(AAnomaliaBatteryCharger, BatteryCharge01);
    DOREPLIFETIME(AAnomaliaBatteryCharger, bCharging);
}
