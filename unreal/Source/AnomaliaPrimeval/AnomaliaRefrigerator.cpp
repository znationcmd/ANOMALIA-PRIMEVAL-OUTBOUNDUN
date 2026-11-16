#include "AnomaliaRefrigerator.h"
#include "AnomaliaPowerGenerator.h"
#include "AnomaliaFoodPreservation.h"
#include "AnomaliaGameMode.h"
#include "AnomaliaInventoryComponent.h"
#include "AnomaliaSurvivor.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Dom/JsonObject.h"
#include "HAL/FileManager.h"
#include "Misc/DateTime.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Net/UnrealNetwork.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

AAnomaliaRefrigerator::AAnomaliaRefrigerator()
{
    bReplicates = true;
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.TickInterval = 1.f;
    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    RootComponent = SceneRoot;
    VisualMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("VisualMesh"));
    VisualMesh->SetupAttachment(SceneRoot);
}

bool AAnomaliaRefrigerator::ValidScopeId(const FString& Text)
{
    if (Text.IsEmpty() || Text.Len() > 64) return false;
    for (const TCHAR C : Text)
        if (C > 127 || !(FChar::IsAlnum(C) || C == TEXT('_') || C == TEXT('-'))) return false;
    return true;
}

bool AAnomaliaRefrigerator::CanStore(FName ItemId)
{
    // Only edible/drinkable items: not an extra 40-slot weapon stash.
    return AnomaliaFoodPreservation::IsPerishable(ItemId) ||
        ItemId == TEXT("food") || ItemId == TEXT("water");
}

int32 AAnomaliaRefrigerator::GetUsedCapacity() const
{
    int32 Total = 0;
    for (const FAnomaliaRefrigeratorItem& Item : Contents) Total += Item.Count;
    return Total;
}

bool AAnomaliaRefrigerator::IsPlayerInReach(const AAnomaliaSurvivor* Player) const
{
    return HasAuthority() && IsValid(Player) && Player->GetWorld() == GetWorld() &&
        Player->Health > 0.f && IsValid(Player->InventoryComponent) &&
        FVector::DistSquared(Player->GetActorLocation(), GetActorLocation()) <= FMath::Square(300.f);
}

void AAnomaliaRefrigerator::NotifyChanged()
{
    ForceNetUpdate();
    OnRefrigeratorUpdated.Broadcast();
}

bool AAnomaliaRefrigerator::SetSwitchedOnServer(bool bOn)
{
    if (!HasAuthority()) return false;
    bSwitchedOn = bOn;
    NotifyChanged();
    return true;
}

bool AAnomaliaRefrigerator::DepositOnServer(AAnomaliaSurvivor* Player, FName ItemId, int32 Count)
{
    if (!IsPlayerInReach(Player) || !CanStore(ItemId) || Count < 1 || Count > 40 ||
        Count > GetMaxCapacity() - GetUsedCapacity()) return false;

    float Freshness = 1.f;
    if (!Player->InventoryComponent->TryRemoveItemWithFreshness(ItemId, Count, Freshness)) return false;
    FAnomaliaRefrigeratorItem* Existing = Contents.FindByPredicate(
        [&](const FAnomaliaRefrigeratorItem& Item) { return Item.ItemId == ItemId; });
    if (Existing)
    {
        Existing->Freshness01 = (Existing->Freshness01 * Existing->Count + Freshness * Count) /
            (Existing->Count + Count);
        Existing->Count += Count;
    }
    else
    {
        FAnomaliaRefrigeratorItem NewItem;
        NewItem.ItemId = ItemId;
        NewItem.Count = Count;
        NewItem.Freshness01 = Freshness;
        Contents.Add(NewItem);
    }
    NotifyChanged();
    return true;
}

bool AAnomaliaRefrigerator::WithdrawOnServer(AAnomaliaSurvivor* Player, FName ItemId, int32 Count)
{
    if (!IsPlayerInReach(Player) || Count < 1 || Count > 40) return false;
    const int32 Index = Contents.IndexOfByPredicate(
        [&](const FAnomaliaRefrigeratorItem& Item) { return Item.ItemId == ItemId && Item.Count >= Count; });
    if (Index == INDEX_NONE) return false;
    // First reserve capacity in player inventory; if it fails the fridge is unchanged.
    if (!Player->InventoryComponent->TryAddItemWithFreshness(ItemId, Count, Contents[Index].Freshness01)) return false;
    Contents[Index].Count -= Count;
    if (Contents[Index].Count == 0) Contents.RemoveAt(Index);
    NotifyChanged();
    return true;
}

bool AAnomaliaRefrigerator::GetSavePath(FString& OutFile) const
{
    OutFile.Empty();
    const AAnomaliaGameMode* Game = GetWorld() ? Cast<AAnomaliaGameMode>(GetWorld()->GetAuthGameMode()) : nullptr;
    if (!Game || !ValidScopeId(Game->ServerId) || !ValidScopeId(PersistentId)) return false;
    OutFile = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Servers"), Game->ServerId,
        TEXT("refrigerators"), PersistentId + TEXT(".json"));
    return true;
}

bool AAnomaliaRefrigerator::LoadServerState()
{
    FString File;
    if (!GetSavePath(File)) return false;
    if (!IFileManager::Get().FileExists(*File)) return true;
    const int64 Bytes = IFileManager::Get().FileSize(*File);
    if (Bytes < 0 || Bytes > 65536) return false;
    FString Raw;
    if (!FFileHelper::LoadFileToString(Raw, *File)) return false;
    TSharedPtr<FJsonObject> Root;
    if (!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Raw), Root) || !Root.IsValid()) return false;
    double Schema = 0, Temperature = 0, SavedAt = 0;
    bool bSavedOn = false;
    const TArray<TSharedPtr<FJsonValue>>* Rows = nullptr;
    if (!Root->TryGetNumberField(TEXT("schemaVersion"), Schema) || Schema != 1 ||
        !Root->TryGetNumberField(TEXT("temperatureC"), Temperature) || !FMath::IsFinite(Temperature) ||
        Temperature < -20 || Temperature > 60 ||
        !Root->TryGetNumberField(TEXT("savedAtUnix"), SavedAt) || !FMath::IsFinite(SavedAt) ||
        SavedAt < 0 || SavedAt > 4102444800.0 ||
        !Root->TryGetBoolField(TEXT("switchedOn"), bSavedOn) ||
        !Root->TryGetArrayField(TEXT("contents"), Rows) || !Rows || Rows->Num() > 40) return false;

    TArray<FAnomaliaRefrigeratorItem> Loaded;
    int32 Total = 0;
    TSet<FName> Seen;
    for (const TSharedPtr<FJsonValue>& Value : *Rows)
    {
        const TSharedPtr<FJsonObject> Row = Value.IsValid() ? Value->AsObject() : nullptr;
        if (!Row.IsValid()) return false;
        FString Id;
        double Count = 0, Freshness = 0;
        if (!Row->TryGetStringField(TEXT("id"), Id) ||
            !Row->TryGetNumberField(TEXT("count"), Count) ||
            !Row->TryGetNumberField(TEXT("freshness01"), Freshness) ||
            !FMath::IsFinite(Count) || Count < 1 || Count > 40 ||
            Count != FMath::FloorToDouble(Count) ||
            !FMath::IsFinite(Freshness) || Freshness < 0 || Freshness > 1) return false;
        const FName ItemId(*Id);
        if (!CanStore(ItemId) || Seen.Contains(ItemId)) return false;
        Seen.Add(ItemId);
        Total += static_cast<int32>(Count);
        if (Total > 40) return false;
        FAnomaliaRefrigeratorItem Item;
        Item.ItemId = ItemId;
        Item.Count = static_cast<int32>(Count);
        // On restart, treat elapsed offline time as unpowered: never invent generator uptime.
        const double ElapsedHours = FMath::Clamp(
            (static_cast<double>(FDateTime::UtcNow().ToUnixTimestamp()) - SavedAt) / 3600.0, 0.0, 24.0 * 365.0);
        Item.Freshness01 = AnomaliaFoodPreservation::Advance(ItemId, static_cast<float>(Freshness),
            static_cast<float>(ElapsedHours), AmbientTemperatureC);
        Loaded.Add(Item);
    }
    Contents = MoveTemp(Loaded);
    InternalTemperatureC = static_cast<float>(Temperature);
    bSwitchedOn = bSavedOn;
    NotifyChanged();
    return true;
}

bool AAnomaliaRefrigerator::SaveServerState() const
{
    FString File;
    if (!HasAuthority() || !GetSavePath(File)) return false;
    TSharedRef<FJsonObject> Root = MakeShared<FJsonObject>();
    Root->SetNumberField(TEXT("schemaVersion"), 1);
    Root->SetNumberField(TEXT("savedAtUnix"), static_cast<double>(FDateTime::UtcNow().ToUnixTimestamp()));
    Root->SetNumberField(TEXT("temperatureC"), InternalTemperatureC);
    Root->SetBoolField(TEXT("switchedOn"), bSwitchedOn);
    TArray<TSharedPtr<FJsonValue>> Rows;
    for (const FAnomaliaRefrigeratorItem& Item : Contents)
    {
        TSharedRef<FJsonObject> Row = MakeShared<FJsonObject>();
        Row->SetStringField(TEXT("id"), Item.ItemId.ToString());
        Row->SetNumberField(TEXT("count"), Item.Count);
        Row->SetNumberField(TEXT("freshness01"), Item.Freshness01);
        Rows.Add(MakeShared<FJsonValueObject>(Row));
    }
    Root->SetArrayField(TEXT("contents"), Rows);
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

void AAnomaliaRefrigerator::BeginPlay()
{
    Super::BeginPlay();
    if (!HasAuthority()) return;
    InternalTemperatureC = AmbientTemperatureC;
    bPersistenceEnabled = LoadServerState();
    if (!bPersistenceEnabled)
        UE_LOG(LogTemp, Warning, TEXT("ANOMALIA fridge '%s': invalid persistence ID or save; automatic writes disabled"), *PersistentId);
}

void AAnomaliaRefrigerator::EndPlay(const EEndPlayReason::Type Reason)
{
    if (HasAuthority() && bPersistenceEnabled && !SaveServerState())
        UE_LOG(LogTemp, Warning, TEXT("ANOMALIA fridge '%s': shutdown save failed"), *PersistentId);
    Super::EndPlay(Reason);
}

void AAnomaliaRefrigerator::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!HasAuthority() || !FMath::IsFinite(DeltaSeconds) || DeltaSeconds <= 0.f) return;
    bCoolingActive = bSwitchedOn && IsValid(PowerGenerator) && PowerGenerator->IsSupplyingActor(this);
    const float DesiredTemperature = bCoolingActive ? FMath::Clamp(SetPointC, 0.f, 12.f) : AmbientTemperatureC;
    const float PreviousTemperature = InternalTemperatureC;
    InternalTemperatureC = FMath::FInterpConstantTo(InternalTemperatureC, DesiredTemperature,
        DeltaSeconds, bCoolingActive ? 0.15f : 0.05f);

    AgingSeconds += DeltaSeconds;
    if (AgingSeconds >= 30.f)
    {
        const float Hours = AgingSeconds / 3600.f;
        AgingSeconds = 0.f;
        bool bAged = false;
        for (FAnomaliaRefrigeratorItem& Item : Contents)
        {
            const float Freshness = AnomaliaFoodPreservation::Advance(Item.ItemId,
                Item.Freshness01, Hours, InternalTemperatureC);
            if (Freshness < Item.Freshness01) { Item.Freshness01 = Freshness; bAged = true; }
        }
        if (bAged) NotifyChanged();
    }
    UnsavedSeconds += DeltaSeconds;
    if (bPersistenceEnabled && UnsavedSeconds >= 60.f)
    {
        UnsavedSeconds = 0.f;
        if (!SaveServerState()) UE_LOG(LogTemp, Warning, TEXT("ANOMALIA fridge '%s': autosave failed"), *PersistentId);
    }
    if (FMath::Abs(PreviousTemperature - InternalTemperatureC) > 0.001f) ForceNetUpdate();
}

void AAnomaliaRefrigerator::OnRep_Contents() { OnRefrigeratorUpdated.Broadcast(); }

void AAnomaliaRefrigerator::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AAnomaliaRefrigerator, PowerGenerator);
    DOREPLIFETIME(AAnomaliaRefrigerator, InternalTemperatureC);
    DOREPLIFETIME(AAnomaliaRefrigerator, bSwitchedOn);
    DOREPLIFETIME(AAnomaliaRefrigerator, bCoolingActive);
    DOREPLIFETIME(AAnomaliaRefrigerator, Contents);
}
