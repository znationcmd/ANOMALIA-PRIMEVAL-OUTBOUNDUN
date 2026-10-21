#include "AnomaliaLootSubsystem.h"
#include "AnomaliaLootPickup.h"
#include "AnomaliaSurvivor.h"
#include "AnomaliaInventoryComponent.h"
#include "AnomaliaEconomySubsystem.h"
#include "AnomaliaConfigLibrary.h"
#include "Dom/JsonObject.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerStart.h"
#include "Misc/DateTime.h"
#include "Misc/Guid.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/SecureHash.h"
#include "HAL/FileManager.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

namespace
{
    bool SafeId(const FString& Id)
    {
        if (Id.IsEmpty() || Id.Len() > 64) return false;
        for (TCHAR C : Id) if (C > 127 || !(FChar::IsAlnum(C) || C == '-' || C == '_')) return false;
        return true;
    }
    bool Parse(const FString& Text, TSharedPtr<FJsonObject>& Out)
    {
        return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text), Out) && Out.IsValid();
    }
    FString Json(const TSharedPtr<FJsonObject>& Root)
    {
        FString Text;
        FJsonSerializer::Serialize(Root.ToSharedRef(), TJsonWriterFactory<>::Create(&Text));
        return Text;
    }
    bool Read(const FString& File, TSharedPtr<FJsonObject>& Out, FString& Error)
    {
        FString Text;
        const int64 Bytes = IFileManager::Get().FileSize(*File);
        if (Bytes < 0 || Bytes > 1024*1024 || !FFileHelper::LoadFileToString(Text, *File) || !Parse(Text, Out))
        { Error = TEXT("Missing, oversized or malformed loot JSON: ") + File; return false; }
        double Schema = 0;
        if (!Out->TryGetNumberField(TEXT("schemaVersion"), Schema) || Schema != 1)
        { Error = TEXT("Unsupported loot schema: ") + File; return false; }
        return true;
    }
    bool Number(const TSharedPtr<FJsonObject>& Row, const TCHAR* Key, double& Out, double Min, double Max, bool Integer = false)
    {
        return Row->TryGetNumberField(Key, Out) && FMath::IsFinite(Out) && Out >= Min && Out <= Max &&
            (!Integer || Out == FMath::FloorToDouble(Out));
    }
    const TMap<FString, TArray<FString>>& CategoryGroups()
    {
        static const TMap<FString, TArray<FString>> Groups = {
            {TEXT("rp_common"), {TEXT("rp_cash"), TEXT("rp_valuables")}},
            {TEXT("rp_rare"), {TEXT("rp_precious_metals"), TEXT("rp_gemstones")}},
            {TEXT("food"), {TEXT("canned_food"), TEXT("fresh_food"), TEXT("cooking")}},
            {TEXT("water"), {TEXT("drinks")}},
            {TEXT("clothing"), {TEXT("tops"), TEXT("pants"), TEXT("shoes_gloves"), TEXT("headwear"), TEXT("backpacks")}},
            {TEXT("medical_basic"), {TEXT("medical_supplies")}},
            {TEXT("tools_basic"), {TEXT("tools"), TEXT("hygiene"), TEXT("navigation"), TEXT("power_lighting")}},
            {TEXT("medical"), {TEXT("medical_supplies"), TEXT("medicine")}},
            {TEXT("vehicle_parts"), {TEXT("vehicle_engine_parts"), TEXT("vehicle_body_parts")}},
            {TEXT("tools"), {TEXT("tools"), TEXT("cooking"), TEXT("power_lighting")}},
            {TEXT("medical_advanced"), {TEXT("medical_supplies"), TEXT("medicine")}},
            {TEXT("industrial"), {TEXT("craft_materials"), TEXT("power_lighting"), TEXT("camping_storage")}},
            {TEXT("equipment"), {TEXT("weapon_accessories"), TEXT("camping_storage"), TEXT("navigation"), TEXT("backpacks")}},
            {TEXT("military"), {TEXT("assault_weapons"), TEXT("hunting_precision_weapons"), TEXT("handguns_smg_shotguns"), TEXT("ammunition"), TEXT("weapon_accessories")}},
            {TEXT("protection"), {TEXT("vests"), TEXT("headwear")}},
            {TEXT("rare_parts"), {TEXT("vehicle_engine_parts"), TEXT("vehicle_body_parts"), TEXT("craft_materials")}},
            {TEXT("rare_medical"), {TEXT("medicine"), TEXT("medical_supplies")}},
            {TEXT("special_equipment"), {TEXT("power_lighting"), TEXT("navigation"), TEXT("weapon_accessories")}}
        };
        return Groups;
    }
    double Now() { return static_cast<double>(FDateTime::UtcNow().ToUnixTimestamp()); }
    FString DataFile(const FString& ServerId, const TCHAR* Name)
    {
        const FString Override = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Servers"), ServerId, Name);
        return IFileManager::Get().FileExists(*Override) ? Override :
            FPaths::Combine(FPaths::ProjectContentDir(), TEXT("Anomalia/Data"), Name);
    }
}

bool UAnomaliaLootSubsystem::DoesSupportWorldType(EWorldType::Type Type) const
{ return Type == EWorldType::Game || Type == EWorldType::PIE; }
void UAnomaliaLootSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);
    FString Error;
    // Clients use only shipped inventory definitions, never a dedicated server's files.
    if (LoadCatalog(FPaths::Combine(FPaths::ProjectContentDir(), TEXT("Anomalia/Data/loot_items_catalog.json")), Error))
        LoadCatalog(FPaths::Combine(FPaths::ProjectContentDir(), TEXT("Anomalia/Data/rp_items_catalog.json")), Error, true);
}
TStatId UAnomaliaLootSubsystem::GetStatId() const
{ RETURN_QUICK_DECLARE_CYCLE_STAT(UAnomaliaLootSubsystem, STATGROUP_Tickables); }
void UAnomaliaLootSubsystem::Tick(float DeltaTime)
{
    if (!bConfigured || !GetWorld() || GetWorld()->GetNetMode() == NM_Client) return;
    Accumulator += DeltaTime;
    if (Accumulator < 1.f) return;
    Accumulator = 0;
    FString Error;
    if (!RecoverPending(Error)) return; // Keep inventory and point locked until durable completion.
    if (bReady && GetWorld()->HasBegunPlay()) RefreshLoot();
}

bool UAnomaliaLootSubsystem::LoadCatalog(const FString& File, FString& Error, bool Append)
{
    TSharedPtr<FJsonObject> Root;
    if (!Read(File, Root, Error)) return false;
    const TArray<TSharedPtr<FJsonValue>>* Rows = nullptr;
    if (!Root->TryGetArrayField(TEXT("items"), Rows) || !Rows || Rows->Num() < 1 || Rows->Num() > 4096)
    { Error = TEXT("Invalid loot catalogue size"); return false; }
    TMap<FName, FAnomaliaLootItem> Candidate;
    for (const auto& Value : *Rows)
    {
        const auto Row = Value.IsValid() && Value->Type == EJson::Object ? Value->AsObject() : nullptr;
        FString Id; FAnomaliaLootItem Item;
        double Min = 0, Max = 0, Quantity = 0, Nominal = 0, Minimum = 0;
        if (!Row.IsValid() || !Row->TryGetStringField(TEXT("id"), Id) || !SafeId(Id) ||
            (Append && Items.Contains(FName(*Id))) || !Row->TryGetStringField(TEXT("displayName"), Item.DisplayName) ||
            Item.DisplayName.IsEmpty() || Item.DisplayName.Len() > 128 ||
            !Row->TryGetStringField(TEXT("category"), Item.Category) || !SafeId(Item.Category) ||
            !Row->TryGetBoolField(TEXT("enabled"), Item.bEnabled) ||
            !Number(Row, TEXT("minTier"), Min, 1, 5, true) || !Number(Row, TEXT("maxTier"), Max, Min, 5, true) ||
            !Number(Row, TEXT("quantity"), Quantity, 1, 100, true) || !Number(Row, TEXT("nominal"), Nominal, 0, 10000, true) ||
            !Number(Row, TEXT("min"), Minimum, 0, Nominal, true) ||
            !Number(Row, TEXT("restockSeconds"), Item.RestockSeconds, 1, 2592000) ||
            !Number(Row, TEXT("lifetimeSeconds"), Item.LifetimeSeconds, 1, 2592000))
        { Error = TEXT("Invalid or duplicate loot item: ") + Id; return false; }
        Item.Id = FName(*Id); Item.MinTier = static_cast<int32>(Min); Item.MaxTier = static_cast<int32>(Max);
        Item.Quantity = static_cast<int32>(Quantity); Item.Nominal = static_cast<int32>(Nominal); Item.Minimum = static_cast<int32>(Minimum);
        // Explicit physical metadata is optional; no fabricated weapon behaviour is implied.
        double Weight = 1, Stack = 20, Width = 1, Height = 1;
        if ((Row->HasField(TEXT("weightKg")) && !Number(Row, TEXT("weightKg"), Weight, .001, 500)) ||
            (Row->HasField(TEXT("maxStack")) && !Number(Row, TEXT("maxStack"), Stack, 1, 100, true)) ||
            (Row->HasField(TEXT("inventoryWidth")) && !Number(Row, TEXT("inventoryWidth"), Width, 1, 12, true)) ||
            (Row->HasField(TEXT("inventoryHeight")) && !Number(Row, TEXT("inventoryHeight"), Height, 1, 20, true)))
        { Error = TEXT("Invalid loot inventory metadata: ") + Id; return false; }
        Item.WeightKg = static_cast<float>(Weight); Item.MaxStack = static_cast<int32>(Stack);
        Item.Size = FIntPoint(static_cast<int32>(Width), static_cast<int32>(Height));
        if (Item.Quantity > Item.MaxStack) { Error = TEXT("Loot quantity exceeds stack limit"); return false; }
        Item.Categories.Add(Item.Category);
        if (auto* Existing = Candidate.Find(Item.Id))
        {
            // One existing battery is listed in both lighting and engine-parts categories.
            // Preserve both categories as one physical item; conflicting data must fail closed.
            if (Existing->DisplayName != Item.DisplayName || Existing->MinTier != Item.MinTier || Existing->MaxTier != Item.MaxTier ||
                Existing->Quantity != Item.Quantity || Existing->Nominal != Item.Nominal || Existing->Minimum != Item.Minimum ||
                Existing->RestockSeconds != Item.RestockSeconds || Existing->LifetimeSeconds != Item.LifetimeSeconds ||
                Existing->WeightKg != Item.WeightKg || Existing->MaxStack != Item.MaxStack || Existing->Size != Item.Size ||
                Existing->bEnabled != Item.bEnabled)
            { Error = TEXT("Conflicting duplicate loot definition: ")+Id; return false; }
            Existing->Categories.Add(Item.Category);
        }
        else Candidate.Add(Item.Id, Item);
    }
    if (Append) Items.Append(Candidate);
    else Items = MoveTemp(Candidate);
    return true;
}

bool UAnomaliaLootSubsystem::Configure(const FString& InServerId, const FString& InMapName, FString& Error)
{
    Error.Empty();
    if (bConfigured || !GetWorld() || GetWorld()->GetNetMode() == NM_Client || !SafeId(InServerId))
    { Error = TEXT("Loot configuration requires an unconfigured authority world and valid server ID"); return false; }
    ServerId = InServerId;
    MapName = FPaths::GetBaseFilename(InMapName);
    if (MapName.StartsWith(TEXT("UEDPIE_")))
    {
        int32 Split = INDEX_NONE;
        if (MapName.FindChar(TEXT('_'), Split))
        { Split = MapName.Find(TEXT("_"), ESearchCase::CaseSensitive, ESearchDir::FromStart, Split+1); if (Split >= 0) MapName.RightChopInline(Split+1); }
    }
    FTCHARToUTF8 Encoded(*MapName);
    StateId = TEXT("loot-") + FSHA1::HashBuffer(Encoded.Get(), Encoded.Length()).ToString().ToLower();
    if (!LoadCatalog(DataFile(ServerId, TEXT("loot_items_catalog.json")), Error) ||
        !LoadCatalog(DataFile(ServerId, TEXT("rp_items_catalog.json")), Error, true)) return false;
    TSharedPtr<FJsonObject> Tiers;
    if (!Read(DataFile(ServerId, TEXT("loot_tiers.json")), Tiers, Error)) return false;
    bool Enabled = false;
    const TArray<TSharedPtr<FJsonValue>>* TierRows = nullptr;
    if (!Tiers->TryGetBoolField(TEXT("enabled"), Enabled) ||
        !Number(Tiers, TEXT("restockSeconds"), DefaultRestock, 1, 2592000) ||
        !Tiers->TryGetArrayField(TEXT("tiers"), TierRows) || !TierRows || TierRows->Num() != 5)
    { Error = TEXT("Invalid loot tiers"); return false; }
    for (const auto& Value : *TierRows)
    {
        const auto Row = Value.IsValid() && Value->Type == EJson::Object ? Value->AsObject() : nullptr;
        double Tier = 0, Chance = 0;
        const TArray<TSharedPtr<FJsonValue>>* Buildings = nullptr;
        if (!Row.IsValid() || !Number(Row, TEXT("tier"), Tier, 1, 5, true) || Rarity.Contains(static_cast<int32>(Tier)) ||
            !Number(Row, TEXT("rarityMultiplier"), Chance, 0, 1) ||
            !Row->TryGetArrayField(TEXT("buildings"), Buildings) || !Buildings)
        { Error = TEXT("Invalid tier row"); return false; }
        const TArray<TSharedPtr<FJsonValue>>* Categories = nullptr;
        if (!Row->TryGetArrayField(TEXT("categories"), Categories) || !Categories || Categories->IsEmpty())
        { Error = TEXT("Missing tier category groups"); return false; }
        auto& Allowed = TierCategories.FindOrAdd(static_cast<int32>(Tier));
        for (const auto& Category : *Categories)
        {
            FString Group;
            if (!Category.IsValid() || !Category->TryGetString(Group) || !CategoryGroups().Contains(Group))
            { Error = TEXT("Unknown tier category group"); return false; }
            for (const auto& Name : CategoryGroups()[Group]) Allowed.Add(Name);
        }
        Rarity.Add(static_cast<int32>(Tier), Chance);
        for (const auto& Building : *Buildings)
        {
            FString Kind;
            if (!Building.IsValid() || !Building->TryGetString(Kind) || !SafeId(Kind) || BuildingTiers.Contains(Kind))
            { Error = TEXT("Invalid or duplicate tier building"); return false; }
            BuildingTiers.Add(Kind, static_cast<int32>(Tier));
        }
    }
    TSharedPtr<FJsonObject> Layout;
    if (!Read(DataFile(ServerId, TEXT("loot_spawns.json")), Layout, Error)) return false;
    const TArray<TSharedPtr<FJsonValue>>* Points = nullptr;
    if (!Layout->TryGetArrayField(TEXT("spawns"), Points) || !Points || Points->Num() > 512)
    { Error = TEXT("Invalid loot spawn list"); return false; }
    TSet<FString> Ids;
    for (const auto& Value : *Points)
    {
        const auto Row = Value.IsValid() && Value->Type == EJson::Object ? Value->AsObject() : nullptr;
        FAnomaliaLootSpawn Spawn; FString Map;
        double X = 0, Y = 0, Z = 0;
        if (!Row.IsValid() || !Row->TryGetStringField(TEXT("map"), Map) || !SafeId(Map) ||
            !Row->TryGetStringField(TEXT("id"), Spawn.Id) || !SafeId(Spawn.Id) ||
            !Row->TryGetStringField(TEXT("buildingType"), Spawn.BuildingType) || !BuildingTiers.Contains(Spawn.BuildingType) ||
            !Number(Row, TEXT("x"), X, -2400000, 2400000) || !Number(Row, TEXT("y"), Y, -2400000, 2400000) ||
            !Number(Row, TEXT("z"), Z, -2400000, 2400000))
        { Error = TEXT("Invalid loot spawn"); return false; }
        const FString Unique = Map + TEXT(":") + Spawn.Id;
        if (Ids.Contains(Unique)) { Error = TEXT("Duplicate loot spawn identity"); return false; }
        Ids.Add(Unique);
        const TArray<TSharedPtr<FJsonValue>>* Categories = nullptr;
        if (Row->HasField(TEXT("categories")))
        {
            if (!Row->TryGetArrayField(TEXT("categories"), Categories) || !Categories)
            { Error = TEXT("Invalid loot category filter"); return false; }
            for (const auto& Category : *Categories)
            {
                FString Name;
                if (!Category.IsValid() || !Category->TryGetString(Name) || !SafeId(Name))
                { Error = TEXT("Invalid loot category filter"); return false; }
                bool Found = false;
                for (const auto& Pair : Items) if (Pair.Value.Categories.Contains(Name)) { Found = true; break; }
                if (!Found) { Error = TEXT("Unknown loot category filter"); return false; }
                Spawn.Categories.Add(Name);
            }
        }
        if (Row->HasField(TEXT("anchor")))
        {
            FString Anchor;
            if (!Row->TryGetStringField(TEXT("anchor"), Anchor) || Anchor != TEXT("player_start"))
            { Error = TEXT("Unknown loot placement anchor"); return false; }
            Spawn.bPlayerStartRelative = true;
        }
        Spawn.Location = FVector(X, Y, Z); Spawn.Tier = BuildingTiers[Spawn.BuildingType];
        if (Map == MapName && Enabled) Spawns.Add(Spawn);
    }
    FString Raw;
    if (UAnomaliaConfigLibrary::LoadWorldState(ServerId, StateId, Raw, Error))
    {
        if (!Parse(Raw, State)) return false;
        double Schema = 0; FString SavedMap;
        const TSharedPtr<FJsonObject>* PointsObject = nullptr;
        if (!Number(State, TEXT("schemaVersion"), Schema, 1, 1, true) ||
            !State->TryGetStringField(TEXT("map"), SavedMap) || SavedMap != MapName ||
            !State->TryGetObjectField(TEXT("points"), PointsObject) || !PointsObject || !PointsObject->IsValid())
        { Error = TEXT("Invalid loot persistence; existing data left untouched"); return false; }
    }
    else if (Error == TEXT("World state not found"))
    {
        Error.Empty(); State = MakeShared<FJsonObject>();
        State->SetNumberField(TEXT("schemaVersion"), 1); State->SetStringField(TEXT("map"), MapName);
        State->SetObjectField(TEXT("points"), MakeShared<FJsonObject>());
    }
    else return false;
    const auto SavedPoints = State->GetObjectField(TEXT("points"));
    for (const auto& Pair : SavedPoints->Values)
    {
        const auto Row = Pair.Value.IsValid() && Pair.Value->Type == EJson::Object ? Pair.Value->AsObject() : nullptr;
        FString Id, Generation; double Count = 0, Available = 0, Expires = 0;
        if (!SafeId(Pair.Key) || !Row.IsValid() || !Row->TryGetStringField(TEXT("itemId"), Id) ||
            (!Id.IsEmpty() && !Items.Contains(FName(*Id))) || !Row->TryGetStringField(TEXT("generation"), Generation) ||
            (!Generation.IsEmpty() && !SafeId(Generation)) ||
            !Number(Row, TEXT("count"), Count, 0, 100, true) ||
            !Number(Row, TEXT("availableAt"), Available, 0, 1e12) || !Number(Row, TEXT("expiresAt"), Expires, 0, 1e12) ||
            (Id.IsEmpty() != (Count == 0)) || (!Id.IsEmpty() && (Generation.IsEmpty() || Count > Items[FName(*Id)].MaxStack)))
        { Error = TEXT("Invalid saved loot point; recovery stopped without overwriting it"); bConfigured = false; return false; }
    }
    for (const auto& Spawn : Spawns)
        if (!SavedPoints->HasField(Spawn.Id))
        {
            auto Row = MakeShared<FJsonObject>();
            Row->SetStringField(TEXT("itemId"), TEXT("")); Row->SetStringField(TEXT("generation"), TEXT(""));
            Row->SetNumberField(TEXT("count"), 0); Row->SetNumberField(TEXT("availableAt"), 0); Row->SetNumberField(TEXT("expiresAt"), 0);
            SavedPoints->SetObjectField(Spawn.Id, Row);
        }
    bConfigured = true;
    if (!RecoverPending(Error)) return false;
    bReady = Persist(Error);
    return bReady;
}

bool UAnomaliaLootSubsystem::Persist(FString& Error)
{ return UAnomaliaConfigLibrary::SaveWorldState(ServerId, StateId, Json(State), Error); }

bool UAnomaliaLootSubsystem::HasPendingPlayer(const FString& PlayerId) const
{
    const TSharedPtr<FJsonObject>* Pending = nullptr;
    FString Id;
    return State.IsValid() && State->TryGetObjectField(TEXT("pending"), Pending) && Pending && Pending->IsValid() &&
        (*Pending)->TryGetStringField(TEXT("playerId"), Id) && Id == PlayerId;
}

bool UAnomaliaLootSubsystem::RecoverPending(FString& Error)
{
    if (!State.IsValid() || !State->HasField(TEXT("pending"))) return true;
    const TSharedPtr<FJsonObject>* PendingPtr = nullptr;
    if (!State->TryGetObjectField(TEXT("pending"), PendingPtr) || !PendingPtr || !PendingPtr->IsValid())
    { Error = TEXT("Malformed pending loot transaction"); return false; }
    const auto Pending = *PendingPtr;
    FString PlayerId, ProfileJson;
    if (!Pending->TryGetStringField(TEXT("playerId"), PlayerId) || !SafeId(PlayerId) ||
        !Pending->TryGetStringField(TEXT("profileAfter"), ProfileJson))
    { Error = TEXT("Invalid pending loot transaction"); return false; }
    // Intent already contains the consumed point and the complete post-pickup profile.
    // Replaying this exact snapshot before unlocking is idempotent, including after a crash.
    if (!UAnomaliaConfigLibrary::SavePlayerProfile(ServerId, PlayerId, ProfileJson, Error)) return false;
    State->RemoveField(TEXT("pending"));
    if (!Persist(Error)) { State->SetObjectField(TEXT("pending"), Pending); return false; }
    if (PendingInventory.IsValid())
    {
        PendingInventory->bPersistenceLocked = false;
        PendingInventory->Commit(TArray<FAnomaliaInventoryStack>(PendingInventory->Stacks));
        PendingInventory.Reset();
    }
    bReady = true;
    return true;
}

void UAnomaliaLootSubsystem::RefreshLoot()
{
    if (!bReady || !GetWorld() || GetWorld()->GetNetMode() == NM_Client || State->HasField(TEXT("pending"))) return;
    const auto Points = State->GetObjectField(TEXT("points"));
    bool Changed = false;
    const double Time = Now();
    for (const auto& Spawn : Spawns)
    {
        const auto Row = Points->GetObjectField(Spawn.Id);
        const FString Current = Row->GetStringField(TEXT("itemId"));
        if (!Current.IsEmpty() && Time >= Row->GetNumberField(TEXT("expiresAt")))
        {
            const auto* Item = FindItem(FName(*Current));
            Row->SetStringField(TEXT("itemId"), TEXT("")); Row->SetNumberField(TEXT("count"), 0);
            Row->SetNumberField(TEXT("availableAt"), Time + (Item ? Item->RestockSeconds : DefaultRestock));
            Changed = true; continue;
        }
        if (!Current.IsEmpty() || Time < Row->GetNumberField(TEXT("availableAt"))) continue;
        TArray<const FAnomaliaLootItem*> Candidates, BelowMinimum;
        for (const auto& Pair : Items)
        {
            const auto& Item = Pair.Value;
            if (!Item.bEnabled || Item.Nominal < 1 || Spawn.Tier < Item.MinTier || Spawn.Tier > Item.MaxTier ||
                !Item.MatchesAnyCategory(TierCategories[Spawn.Tier]) ||
                (Spawn.Categories.Num() && !Item.MatchesAnyCategory(Spawn.Categories))) continue;
            int32 Existing = 0;
            for (const auto& Saved : Points->Values)
                if (Saved.Value->AsObject()->GetStringField(TEXT("itemId")) == Item.Id.ToString())
                    Existing += static_cast<int32>(Saved.Value->AsObject()->GetNumberField(TEXT("count")));
            if (Existing + Item.Quantity <= Item.Nominal)
            {
                Candidates.Add(&Item);
                if (Existing < Item.Minimum) BelowMinimum.Add(&Item);
            }
        }
        if (BelowMinimum.Num()) Candidates = MoveTemp(BelowMinimum);
        // Sort to make seeded native tests and server diagnostics reproducible.
        Candidates.Sort([](const FAnomaliaLootItem& A, const FAnomaliaLootItem& B) { return A.Id.LexicalLess(B.Id); });
        Row->SetNumberField(TEXT("availableAt"), Time + DefaultRestock);
        if (Candidates.Num() && (Rarity[Spawn.Tier] >= 1.0 || FMath::FRand() < Rarity[Spawn.Tier]))
        {
            const auto* Item = Candidates[FMath::RandRange(0, Candidates.Num()-1)];
            Row->SetStringField(TEXT("itemId"), Item->Id.ToString());
            Row->SetStringField(TEXT("generation"), FGuid::NewGuid().ToString(EGuidFormats::Digits));
            Row->SetNumberField(TEXT("count"), Item->Quantity);
            Row->SetNumberField(TEXT("expiresAt"), Time + Item->LifetimeSeconds);
        }
        Changed = true;
    }
    FString Error;
    if (Changed && !Persist(Error))
    { bReady = false; UE_LOG(LogTemp, Error, TEXT("ANOMALIA loot suspended: %s"), *Error); return; }
    SyncActors();
}

void UAnomaliaLootSubsystem::SyncActors()
{
    const auto Points = State->GetObjectField(TEXT("points"));
    for (const auto& Spawn : Spawns)
    {
        const auto Row = Points->GetObjectField(Spawn.Id);
        const FName Id(*Row->GetStringField(TEXT("itemId")));
        auto& Weak = Pickups.FindOrAdd(Spawn.Id);
        const auto* Item = FindItem(Id);
        if (Weak.IsValid() && (Id.IsNone() || Weak->Generation != Row->GetStringField(TEXT("generation"))))
        { Weak->Destroy(); Weak.Reset(); }
        if (Id.IsNone() || !Item || Weak.IsValid()) continue;
        FVector Location = Spawn.Location;
        if (Spawn.bPlayerStartRelative)
        {
            APlayerStart* Start = nullptr;
            APlayerStart* Only = nullptr;
            int32 Count = 0, Tagged = 0;
            for (TActorIterator<APlayerStart> It(GetWorld()); It; ++It)
            {
                Only = *It; ++Count;
                if (It->Tags.Contains(TEXT("AnomaliaLootAnchor"))) { Start = *It; ++Tagged; }
            }
            if (Tagged == 0 && Count == 1) Start = Only;
            // Multiple starts require exactly one explicit AnomaliaLootAnchor tag.
            if (!Start || Tagged > 1) continue;
            Location += Start->GetActorLocation();
            FHitResult Ground;
            if (!GetWorld()->LineTraceSingleByChannel(Ground, Location+FVector(0,0,100),
                Location-FVector(0,0,2000), ECC_WorldStatic)) continue;
            Location.Z = Ground.ImpactPoint.Z + 10;
        }
        FActorSpawnParameters Params;
        Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
        auto* Actor = GetWorld()->SpawnActor<AAnomaliaLootPickup>(Location, FRotator::ZeroRotator, Params);
        if (!Actor) continue;
        Actor->SpawnId = Spawn.Id; Actor->Generation = Row->GetStringField(TEXT("generation"));
        Actor->Configure(Id, static_cast<int32>(Row->GetNumberField(TEXT("count"))), Item->DisplayName);
        Weak = Actor;
    }
}

bool UAnomaliaLootSubsystem::TryCollect(AAnomaliaLootPickup* Pickup, AAnomaliaSurvivor* Survivor, const FString& PlayerId, FString& Error)
{
    Error.Empty();
    if (!bReady || !IsValid(Pickup) || !IsValid(Survivor) || !Survivor->HasAuthority() ||
        Pickup->GetWorld() != GetWorld() || Survivor->GetWorld() != GetWorld() || !SafeId(PlayerId) ||
        Survivor->Health <= 0 || Survivor->bSleeping || State->HasField(TEXT("pending")) ||
        FVector::DistSquared(Pickup->GetActorLocation(), Survivor->GetActorLocation()) > FMath::Square(250.f))
    { Error = TEXT("Loot pickup is unavailable"); return false; }
    const auto* Registered = Pickups.Find(Pickup->SpawnId);
    if (!Registered || Registered->Get() != Pickup) return false;
    FHitResult Hit;
    FCollisionQueryParams Query(SCENE_QUERY_STAT(AnomaliaLootVisibility), false, Survivor);
    Query.AddIgnoredActor(Pickup);
    if (GetWorld()->LineTraceSingleByChannel(Hit, Survivor->GetActorLocation()+FVector(0,0,50),
        Pickup->GetActorLocation(), ECC_Visibility, Query)) return false;
    auto* Inventory = Survivor->InventoryComponent.Get();
    const auto* Economy = GetWorld()->GetSubsystem<UAnomaliaEconomySubsystem>();
    if (!Inventory || Inventory->IsPersistenceLocked() || (Economy && Economy->HasPendingPlayer(PlayerId))) return false;
    const auto Point = State->GetObjectField(TEXT("points"))->GetObjectField(Pickup->SpawnId);
    const auto* Item = FindItem(Pickup->ItemId);
    if (!Item || Point->GetStringField(TEXT("itemId")) != Pickup->ItemId.ToString() ||
        Point->GetStringField(TEXT("generation")) != Pickup->Generation ||
        Point->GetNumberField(TEXT("count")) != Pickup->Count || Now() >= Point->GetNumberField(TEXT("expiresAt"))) return false;
    const auto Before = Inventory->Stacks;
    const int32 BeforeId = Inventory->NextStackId;
    const FString StateBefore = Json(State);
    Inventory->bSuppressNotifications = true;
    if (!Inventory->TryAddItem(Pickup->ItemId, Pickup->Count))
    { Inventory->bSuppressNotifications = false; Error = TEXT("Inventory capacity exceeded"); return false; }
    FString ProfileAfter;
    if (!Inventory->BuildInventoryProfile(ServerId, PlayerId, ProfileAfter, Error))
    {
        Inventory->Stacks = Before; Inventory->NextStackId = BeforeId; Inventory->bSuppressNotifications = false;
        return false;
    }
    Point->SetStringField(TEXT("itemId"), TEXT("")); Point->SetNumberField(TEXT("count"), 0);
    Point->SetNumberField(TEXT("availableAt"), Now()+Item->RestockSeconds);
    auto Pending = MakeShared<FJsonObject>();
    Pending->SetStringField(TEXT("playerId"), PlayerId); Pending->SetStringField(TEXT("profileAfter"), ProfileAfter);
    State->SetObjectField(TEXT("pending"), Pending);
    if (!Persist(Error))
    {
        Parse(StateBefore, State);
        Inventory->Stacks = Before; Inventory->NextStackId = BeforeId; Inventory->bSuppressNotifications = false;
        return false;
    }
    // Durable intent exists: never roll this transaction back or allow subsequent profile writes until finished.
    Inventory->bPersistenceLocked = true; Inventory->bSuppressNotifications = false;
    PendingInventory = Inventory; bReady = false;
    Pickup->Destroy(); Pickups.Remove(Pickup->SpawnId);
    if (!RecoverPending(Error))
        UE_LOG(LogTemp, Error, TEXT("ANOMALIA loot transaction retained for recovery: %s"), *Error);
    return true;
}
