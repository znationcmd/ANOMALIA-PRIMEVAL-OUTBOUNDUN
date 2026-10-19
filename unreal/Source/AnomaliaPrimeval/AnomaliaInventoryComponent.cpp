#include "AnomaliaInventoryComponent.h"
#include "AnomaliaConfigLibrary.h"
#include "Dom/JsonObject.h"
#include "GameFramework/Actor.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "Net/UnrealNetwork.h"

UAnomaliaInventoryComponent::UAnomaliaInventoryComponent()
{
    SetIsReplicatedByDefault(true);
    FAnomaliaInventoryCompartment Pockets;
    Pockets.Id = TEXT("pockets");
    Pockets.Width = 6;
    Pockets.Height = 4;
    Compartments.Add(Pockets);
}

bool UAnomaliaInventoryComponent::GetItemRules(FName ItemId, float& OutWeightKg, int32& OutMaxStack, FIntPoint& OutSize)
{
    static const TMap<FName, float> Weights = {
        {TEXT("key_alpha"), .03f}, {TEXT("key_red"), .03f}, {TEXT("key_omega"), .03f},
        {TEXT("key_abyss"), .03f}, {TEXT("key_blue"), .03f}, {TEXT("key_bunker_alpha"), .03f},
        {TEXT("key_bunker_zero"), .03f}, {TEXT("key_container"), .03f},
        {TEXT("kibble_basic"), .3f}, {TEXT("kibble_simple"), .3f}, {TEXT("kibble_regular"), .3f},
        {TEXT("kibble_superior"), .3f}, {TEXT("kibble_exceptional"), .3f}, {TEXT("kibble_extraordinary"), .3f},
        {TEXT("honey"), .3f}, {TEXT("rare_flower"), .05f}, {TEXT("sap"), .1f}, {TEXT("vegetable"), .2f},
        {TEXT("water"), .8f}, {TEXT("food"), .45f}, {TEXT("bandage"), .15f},
        {TEXT("wood"), .65f}, {TEXT("stone"), 1.5f}, {TEXT("berry"), .08f},
        {TEXT("rifle_ammo"), .035f}, {TEXT("ammo"), .025f}, {TEXT("pistol"), 1.2f},
        {TEXT("rifle"), 4.5f}, {TEXT("fishing_rod"), 1.2f}, {TEXT("medicine"), .2f},
        {TEXT("scrap"), .55f}, {TEXT("cloth"), .3f}, {TEXT("saddle"), 5.f},
        {TEXT("kibble_herbivore"), .35f}, {TEXT("kibble_carnivore"), .35f}, {TEXT("tranq_dart"), .1f},
        {TEXT("medkit"), .6f}, {TEXT("raw_meat"), .6f}, {TEXT("raw_fish"), .48f},
        {TEXT("cooked_meat"), .55f}, {TEXT("cooked_fish"), .43f}, {TEXT("hide"), .6f},
        {TEXT("feather"), .07f}, {TEXT("egg"), .22f}, {TEXT("meat"), .5f},
        {TEXT("headlamp"), .4f}, {TEXT("fiber"), .1f}, {TEXT("jacket"), 2.f}, {TEXT("coat"), 3.4f},
        {TEXT("shirt"), .45f}, {TEXT("pants"), 1.4f}, {TEXT("jeans"), .8f}, {TEXT("boots"), 1.6f},
        {TEXT("helmet"), 1.9f}, {TEXT("backpack"), 2.6f}, {TEXT("bag"), 1.2f}, {TEXT("vest"), 2.2f}
    };
    const float* Weight = Weights.Find(ItemId);
    if (!Weight) return false;
    OutWeightKg = *Weight;
    OutSize = FIntPoint(1, 1);
    OutMaxStack = 20;
    if (ItemId == TEXT("rifle") || ItemId == TEXT("pistol") || ItemId == TEXT("saddle") ||
        ItemId == TEXT("fishing_rod") || ItemId == TEXT("headlamp") || ItemId == TEXT("medkit") ||
        ItemId == TEXT("jacket") || ItemId == TEXT("coat") || ItemId == TEXT("shirt") || ItemId == TEXT("pants") ||
        ItemId == TEXT("jeans") || ItemId == TEXT("boots") || ItemId == TEXT("helmet") ||
        ItemId == TEXT("backpack") || ItemId == TEXT("bag") || ItemId == TEXT("vest")) OutMaxStack = 1;
    if (ItemId == TEXT("wood")) OutSize = FIntPoint(1, 3);
    else if (ItemId == TEXT("rifle") || ItemId == TEXT("fishing_rod")) OutSize = FIntPoint(2, 5);
    else if (ItemId == TEXT("saddle")) OutSize = FIntPoint(3, 3);
    else if (ItemId == TEXT("rifle") || ItemId == TEXT("pistol")) OutSize = FIntPoint(2, 2);
    else if (ItemId == TEXT("jacket") || ItemId == TEXT("coat") || ItemId == TEXT("shirt") || ItemId == TEXT("pants") ||
        ItemId == TEXT("jeans") || ItemId == TEXT("boots") || ItemId == TEXT("helmet") || ItemId == TEXT("backpack") ||
        ItemId == TEXT("bag") || ItemId == TEXT("vest")) OutSize = FIntPoint(2, 2);
    if (ItemId == TEXT("ammo") || ItemId == TEXT("rifle_ammo") || ItemId == TEXT("tranq_dart") ||
        ItemId == TEXT("wood") || ItemId == TEXT("stone") || ItemId == TEXT("scrap") || ItemId == TEXT("cloth") ||
        ItemId == TEXT("honey") || ItemId == TEXT("rare_flower") || ItemId == TEXT("sap") || ItemId == TEXT("vegetable") ||
        ItemId == TEXT("hide") || ItemId == TEXT("feather") || ItemId == TEXT("fiber")) OutMaxStack = 50;
    return true;
}

float UAnomaliaInventoryComponent::GetCurrentWeightKg() const
{
    float Total = 0.f;
    for (const FAnomaliaInventoryStack& Stack : Stacks)
    {
        float Weight = 0.f;
        int32 MaxStack = 0;
        FIntPoint Size;
        if (Stack.Count > 0 && GetItemRules(Stack.ItemId, Weight, MaxStack, Size)) Total += Weight * Stack.Count;
    }
    return Total;
}

bool UAnomaliaInventoryComponent::ConfigureCompartment(FName Id, int32 Width, int32 Height)
{
    if (!GetOwner() || !GetOwner()->HasAuthority() || Id.IsNone() || Id == TEXT("hands") ||
        Width < 1 || Width > 12 || Height < 1 || Height > 20) return false;
    FAnomaliaInventoryCompartment* Existing = Compartments.FindByPredicate([&](const FAnomaliaInventoryCompartment& C) { return C.Id == Id; });
    if (Existing && (Width < Existing->Width || Height < Existing->Height)) return false;
    if (!Existing) Existing = &Compartments.AddDefaulted_GetRef();
    Existing->Id = Id;
    Existing->Width = Width;
    Existing->Height = Height;
    OnInventoryChanged();
    OnInventoryUpdated.Broadcast();
    return true;
}

bool UAnomaliaInventoryComponent::CanPlace(const TArray<FAnomaliaInventoryStack>& Candidate,
    const FAnomaliaInventoryStack& Stack, FName ContainerId, int32 X, int32 Y, bool bRotate) const
{
    if (ContainerId == TEXT("hands"))
        return !Candidate.ContainsByPredicate([&](const FAnomaliaInventoryStack& Other) { return Other.StackId != Stack.StackId && Other.ContainerId == TEXT("hands"); });
    const FAnomaliaInventoryCompartment* Box = Compartments.FindByPredicate([&](const FAnomaliaInventoryCompartment& C) { return C.Id == ContainerId; });
    float Weight = 0.f;
    int32 MaxStack = 0;
    FIntPoint Size;
    if (!Box || !GetItemRules(Stack.ItemId, Weight, MaxStack, Size)) return false;
    if (bRotate) Swap(Size.X, Size.Y);
    if (X < 0 || Y < 0 || X + Size.X > Box->Width || Y + Size.Y > Box->Height) return false;
    for (const FAnomaliaInventoryStack& Other : Candidate)
    {
        if (Other.StackId == Stack.StackId || Other.ContainerId != ContainerId) continue;
        FIntPoint OtherSize;
        float OtherWeight = 0.f;
        int32 OtherMax = 0;
        if (!GetItemRules(Other.ItemId, OtherWeight, OtherMax, OtherSize)) return false;
        if (Other.bRotated) Swap(OtherSize.X, OtherSize.Y);
        if (X < Other.X + OtherSize.X && X + Size.X > Other.X && Y < Other.Y + OtherSize.Y && Y + Size.Y > Other.Y) return false;
    }
    return true;
}

bool UAnomaliaInventoryComponent::FindPlacement(const TArray<FAnomaliaInventoryStack>& Candidate, FAnomaliaInventoryStack& Stack) const
{
    for (const FAnomaliaInventoryCompartment& Box : Compartments)
        for (int32 Y = 0; Y < Box.Height; ++Y)
            for (int32 X = 0; X < Box.Width; ++X)
                for (int32 Rotation = 0; Rotation < 2; ++Rotation)
                    if (CanPlace(Candidate, Stack, Box.Id, X, Y, Rotation == 1))
                    {
                        Stack.ContainerId = Box.Id; Stack.X = X; Stack.Y = Y; Stack.bRotated = Rotation == 1;
                        return true;
                    }
    return false;
}

void UAnomaliaInventoryComponent::Commit(TArray<FAnomaliaInventoryStack>&& Candidate)
{
    Stacks = MoveTemp(Candidate);
    if (GetOwner()) GetOwner()->ForceNetUpdate();
    OnInventoryChanged();
    OnInventoryUpdated.Broadcast();
}

bool UAnomaliaInventoryComponent::TryAddItem(FName ItemId, int32 Count)
{
    if (!GetOwner() || !GetOwner()->HasAuthority() || Count < 1) return false;
    float ItemWeight = 0.f;
    int32 MaxStack = 0;
    FIntPoint Size;
    if (!GetItemRules(ItemId, ItemWeight, MaxStack, Size) || GetCurrentWeightKg() + ItemWeight * Count > WeightCapacityKg + KINDA_SMALL_NUMBER) return false;
    TArray<FAnomaliaInventoryStack> Candidate = Stacks;
    int32 Remaining = Count;
    int32 CandidateNextId = NextStackId;
    for (FAnomaliaInventoryStack& Stack : Candidate)
    {
        if (Stack.ItemId != ItemId || Stack.ContainerId == TEXT("hands") || Stack.Count >= MaxStack) continue;
        const int32 Added = FMath::Min(Remaining, MaxStack - Stack.Count);
        Stack.Count += Added; Remaining -= Added;
        if (Remaining == 0) { Commit(MoveTemp(Candidate)); return true; }
    }
    while (Remaining > 0)
    {
        FAnomaliaInventoryStack NewStack;
        if (CandidateNextId >= MAX_int32) return false;
        NewStack.StackId = CandidateNextId++;
        NewStack.ItemId = ItemId;
        NewStack.Count = FMath::Min(Remaining, MaxStack);
        if (!FindPlacement(Candidate, NewStack)) return false;
        Candidate.Add(NewStack);
        Remaining -= NewStack.Count;
    }
    NextStackId = CandidateNextId;
    Commit(MoveTemp(Candidate));
    return true;
}

bool UAnomaliaInventoryComponent::TryRemoveItem(FName ItemId, int32 Count)
{
    if (!GetOwner() || !GetOwner()->HasAuthority() || ItemId.IsNone() || Count < 1) return false;
    int32 Available = 0;
    for (const FAnomaliaInventoryStack& Stack : Stacks)
        if (Stack.ItemId == ItemId && Stack.Count > 0) Available += Stack.Count;
    if (Available < Count) return false;
    TArray<FAnomaliaInventoryStack> Candidate = Stacks;
    int32 Remaining = Count;
    for (int32 Index = Candidate.Num() - 1; Index >= 0 && Remaining > 0; --Index)
    {
        FAnomaliaInventoryStack& Stack = Candidate[Index];
        if (Stack.ItemId != ItemId) continue;
        const int32 Removed = FMath::Min(Remaining, Stack.Count);
        Stack.Count -= Removed;
        Remaining -= Removed;
    }
    Candidate.RemoveAll([](const FAnomaliaInventoryStack& Stack) { return Stack.Count <= 0; });
    Commit(MoveTemp(Candidate));
    return true;
}

bool UAnomaliaInventoryComponent::TryMoveStack(int32 StackId, FName ContainerId, int32 X, int32 Y, bool bRotate)
{
    if (!GetOwner() || !GetOwner()->HasAuthority()) return false;
    TArray<FAnomaliaInventoryStack> Candidate = Stacks;
    FAnomaliaInventoryStack* Stack = Candidate.FindByPredicate([&](const FAnomaliaInventoryStack& S) { return S.StackId == StackId; });
    if (!Stack || !CanPlace(Candidate, *Stack, ContainerId, X, Y, bRotate)) return false;
    Stack->ContainerId = ContainerId; Stack->X = X; Stack->Y = Y; Stack->bRotated = bRotate;
    Commit(MoveTemp(Candidate));
    return true;
}

bool UAnomaliaInventoryComponent::TrySplitStack(int32 StackId, int32 Count, int32& OutNewStackId)
{
    OutNewStackId = 0;
    if (!GetOwner() || !GetOwner()->HasAuthority()) return false;
    TArray<FAnomaliaInventoryStack> Candidate = Stacks;
    FAnomaliaInventoryStack* Source = Candidate.FindByPredicate([&](const FAnomaliaInventoryStack& S) { return S.StackId == StackId; });
    if (!Source || NextStackId >= MAX_int32 || Count < 1 || Count >= Source->Count || Source->ContainerId == TEXT("hands")) return false;
    Source->Count -= Count;
    FAnomaliaInventoryStack Piece = *Source;
    Piece.StackId = NextStackId;
    Piece.Count = Count;
    Piece.ContainerId = NAME_None;
    if (!FindPlacement(Candidate, Piece)) return false;
    Candidate.Add(Piece);
    OutNewStackId = NextStackId++;
    Commit(MoveTemp(Candidate));
    return true;
}

bool UAnomaliaInventoryComponent::TryMergeStacks(int32 TargetStackId, int32 SourceStackId)
{
    if (!GetOwner() || !GetOwner()->HasAuthority() || TargetStackId == SourceStackId) return false;
    TArray<FAnomaliaInventoryStack> Candidate = Stacks;
    FAnomaliaInventoryStack* Target = Candidate.FindByPredicate([&](const FAnomaliaInventoryStack& S) { return S.StackId == TargetStackId; });
    FAnomaliaInventoryStack* Source = Candidate.FindByPredicate([&](const FAnomaliaInventoryStack& S) { return S.StackId == SourceStackId; });
    if (!Target || !Source || Target->ItemId != Source->ItemId || Target->ContainerId == TEXT("hands") || Source->ContainerId == TEXT("hands")) return false;
    float Weight = 0.f; int32 MaxStack = 0; FIntPoint Size;
    if (!GetItemRules(Target->ItemId, Weight, MaxStack, Size) || Target->Count + Source->Count > MaxStack) return false;
    Target->Count += Source->Count;
    Candidate.RemoveAll([&](const FAnomaliaInventoryStack& S) { return S.StackId == SourceStackId; });
    Commit(MoveTemp(Candidate));
    return true;
}

bool UAnomaliaInventoryComponent::SaveInventoryToPlayerProfile(const FString& ServerId, const FString& PlayerId, FString& OutError)
{
    OutError.Empty();
    if (!GetOwner() || !GetOwner()->HasAuthority()) { OutError = TEXT("Inventory persistence requires server authority"); return false; }

    FString ExistingJson;
    FString LoadError;
    TSharedPtr<FJsonObject> Profile = MakeShared<FJsonObject>();
    if (UAnomaliaConfigLibrary::LoadPlayerProfile(ServerId, PlayerId, ExistingJson, LoadError))
    {
        const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ExistingJson);
        if (!FJsonSerializer::Deserialize(Reader, Profile) || !Profile.IsValid())
        {
            OutError = TEXT("Existing player profile is malformed; inventory was not saved");
            return false;
        }
    }
    else if (LoadError != TEXT("Profile not found"))
    {
        OutError = LoadError;
        return false;
    }

    TSharedPtr<FJsonObject> Inventory = MakeShared<FJsonObject>();
    Inventory->SetNumberField(TEXT("schemaVersion"), 1);
    Inventory->SetNumberField(TEXT("weightCapacityKg"), WeightCapacityKg);
    TArray<TSharedPtr<FJsonValue>> CompartmentRows;
    for (const FAnomaliaInventoryCompartment& Box : Compartments)
    {
        TSharedPtr<FJsonObject> Row = MakeShared<FJsonObject>();
        Row->SetStringField(TEXT("id"), Box.Id.ToString());
        Row->SetNumberField(TEXT("width"), Box.Width);
        Row->SetNumberField(TEXT("height"), Box.Height);
        CompartmentRows.Add(MakeShared<FJsonValueObject>(Row));
    }
    Inventory->SetArrayField(TEXT("compartments"), CompartmentRows);
    TArray<TSharedPtr<FJsonValue>> StackRows;
    for (const FAnomaliaInventoryStack& Stack : Stacks)
    {
        TSharedPtr<FJsonObject> Row = MakeShared<FJsonObject>();
        Row->SetNumberField(TEXT("stackId"), Stack.StackId);
        Row->SetStringField(TEXT("itemId"), Stack.ItemId.ToString());
        Row->SetNumberField(TEXT("count"), Stack.Count);
        Row->SetStringField(TEXT("containerId"), Stack.ContainerId.ToString());
        Row->SetNumberField(TEXT("x"), Stack.X);
        Row->SetNumberField(TEXT("y"), Stack.Y);
        Row->SetBoolField(TEXT("rotated"), Stack.bRotated);
        StackRows.Add(MakeShared<FJsonValueObject>(Row));
    }
    Inventory->SetArrayField(TEXT("stacks"), StackRows);
    Profile->SetObjectField(TEXT("inventory"), Inventory);

    FString Serialized;
    const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Serialized);
    if (!FJsonSerializer::Serialize(Profile.ToSharedRef(), Writer))
    {
        OutError = TEXT("Could not serialize inventory profile");
        return false;
    }
    return UAnomaliaConfigLibrary::SavePlayerProfile(ServerId, PlayerId, Serialized, OutError);
}

bool UAnomaliaInventoryComponent::LoadInventoryFromPlayerProfile(const FString& ServerId, const FString& PlayerId, FString& OutError)
{
    OutError.Empty();
    if (!GetOwner() || !GetOwner()->HasAuthority()) { OutError = TEXT("Inventory persistence requires server authority"); return false; }
    FString Raw;
    if (!UAnomaliaConfigLibrary::LoadPlayerProfile(ServerId, PlayerId, Raw, OutError)) return false;
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Raw);
    TSharedPtr<FJsonObject> Profile;
    if (!FJsonSerializer::Deserialize(Reader, Profile) || !Profile.IsValid()) { OutError = TEXT("Malformed player profile"); return false; }
    const TSharedPtr<FJsonObject>* InventoryPtr = nullptr;
    if (!Profile->TryGetObjectField(TEXT("inventory"), InventoryPtr) || !InventoryPtr || !InventoryPtr->IsValid())
    {
        OutError = TEXT("Player profile has no saved inventory");
        return false;
    }
    const TSharedPtr<FJsonObject>& Inventory = *InventoryPtr;
    double SchemaVersion = 0.0;
    double SavedCapacity = 0.0;
    if (!Inventory->TryGetNumberField(TEXT("schemaVersion"), SchemaVersion) || SchemaVersion != 1.0 ||
        !Inventory->TryGetNumberField(TEXT("weightCapacityKg"), SavedCapacity) || !FMath::IsFinite(SavedCapacity) || SavedCapacity < 0.1 || SavedCapacity > 500.0)
    {
        OutError = TEXT("Invalid inventory capacity in profile");
        return false;
    }
    const TArray<TSharedPtr<FJsonValue>>* CompartmentRows = nullptr;
    const TArray<TSharedPtr<FJsonValue>>* StackRows = nullptr;
    if (!Inventory->TryGetArrayField(TEXT("compartments"), CompartmentRows) || !CompartmentRows || CompartmentRows->Num() < 1 || CompartmentRows->Num() > 64 ||
        !Inventory->TryGetArrayField(TEXT("stacks"), StackRows) || !StackRows || StackRows->Num() > 512)
    {
        OutError = TEXT("Invalid inventory arrays in profile");
        return false;
    }

    TArray<FAnomaliaInventoryCompartment> LoadedCompartments;
    TSet<FName> SeenCompartments;
    for (const TSharedPtr<FJsonValue>& Value : *CompartmentRows)
    {
        const TSharedPtr<FJsonObject> Row = Value.IsValid() ? Value->AsObject() : nullptr;
        if (!Row.IsValid()) { OutError = TEXT("Malformed inventory compartment"); return false; }
        FString IdText;
        double Width = 0.0, Height = 0.0;
        if (!Row->TryGetStringField(TEXT("id"), IdText) || !Row->TryGetNumberField(TEXT("width"), Width) || !Row->TryGetNumberField(TEXT("height"), Height) ||
            !FMath::IsFinite(Width) || !FMath::IsFinite(Height) || Width < 1 || Width > 12 || Height < 1 || Height > 20 ||
            !FMath::IsNearlyEqual(Width, static_cast<double>(FMath::RoundToInt(Width))) ||
            !FMath::IsNearlyEqual(Height, static_cast<double>(FMath::RoundToInt(Height))))
        { OutError = TEXT("Invalid inventory compartment dimensions"); return false; }
        const FName Id(*IdText);
        if (Id.IsNone() || Id == TEXT("hands") || SeenCompartments.Contains(Id)) { OutError = TEXT("Duplicate or reserved inventory compartment"); return false; }
        SeenCompartments.Add(Id);
        FAnomaliaInventoryCompartment Box;
        Box.Id = Id; Box.Width = FMath::RoundToInt(Width); Box.Height = FMath::RoundToInt(Height);
        LoadedCompartments.Add(Box);
    }

    TArray<FAnomaliaInventoryStack> LoadedStacks;
    TSet<int32> SeenStackIds;
    int32 MaxSeenStackId = 0;
    double TotalWeight = 0.0;
    for (const TSharedPtr<FJsonValue>& Value : *StackRows)
    {
        const TSharedPtr<FJsonObject> Row = Value.IsValid() ? Value->AsObject() : nullptr;
        if (!Row.IsValid()) { OutError = TEXT("Malformed inventory stack"); return false; }
        double StackId = 0.0, Count = 0.0, X = 0.0, Y = 0.0;
        FString ItemText, ContainerText;
        bool bRotated = false;
        if (!Row->TryGetNumberField(TEXT("stackId"), StackId) || !Row->TryGetNumberField(TEXT("count"), Count) ||
            !Row->TryGetNumberField(TEXT("x"), X) || !Row->TryGetNumberField(TEXT("y"), Y) ||
            !Row->TryGetStringField(TEXT("itemId"), ItemText) || !Row->TryGetStringField(TEXT("containerId"), ContainerText) ||
            !Row->TryGetBoolField(TEXT("rotated"), bRotated) || !FMath::IsFinite(StackId) || !FMath::IsFinite(Count) ||
            !FMath::IsFinite(X) || !FMath::IsFinite(Y) || StackId < 1 || StackId >= MAX_int32 || Count < 1 || Count > 100000 ||
            X < 0 || X > 12 || Y < 0 || Y > 20 ||
            !FMath::IsNearlyEqual(StackId, static_cast<double>(FMath::RoundToInt(StackId))) ||
            !FMath::IsNearlyEqual(Count, static_cast<double>(FMath::RoundToInt(Count))) ||
            !FMath::IsNearlyEqual(X, static_cast<double>(FMath::RoundToInt(X))) ||
            !FMath::IsNearlyEqual(Y, static_cast<double>(FMath::RoundToInt(Y))))
        { OutError = TEXT("Invalid inventory stack fields"); return false; }
        FAnomaliaInventoryStack Stack;
        Stack.StackId = FMath::RoundToInt(StackId); Stack.Count = FMath::RoundToInt(Count); Stack.X = FMath::RoundToInt(X); Stack.Y = FMath::RoundToInt(Y);
        Stack.ItemId = FName(*ItemText); Stack.ContainerId = FName(*ContainerText); Stack.bRotated = bRotated;
        float ItemWeight = 0.f; int32 MaxStack = 0; FIntPoint Size;
        if (SeenStackIds.Contains(Stack.StackId) || !GetItemRules(Stack.ItemId, ItemWeight, MaxStack, Size) || Stack.Count > MaxStack)
        { OutError = TEXT("Duplicate stack or unsupported item in inventory profile"); return false; }
        SeenStackIds.Add(Stack.StackId); MaxSeenStackId = FMath::Max(MaxSeenStackId, Stack.StackId);
        TotalWeight += static_cast<double>(ItemWeight) * Stack.Count;
        LoadedStacks.Add(Stack);
    }
    if (TotalWeight > SavedCapacity + KINDA_SMALL_NUMBER)
    { OutError = TEXT("Saved inventory exceeds its weight limit"); return false; }

    const TArray<FAnomaliaInventoryCompartment> PreviousCompartments = Compartments;
    Compartments = LoadedCompartments;
    for (const FAnomaliaInventoryStack& Stack : LoadedStacks)
    {
        if (!CanPlace(LoadedStacks, Stack, Stack.ContainerId, Stack.X, Stack.Y, Stack.bRotated))
        {
            Compartments = PreviousCompartments;
            OutError = TEXT("Saved inventory layout overlaps or exceeds its compartments");
            return false;
        }
    }
    WeightCapacityKg = static_cast<float>(SavedCapacity);
    NextStackId = MaxSeenStackId + 1;
    Commit(MoveTemp(LoadedStacks));
    return true;
}

bool UAnomaliaInventoryComponent::RequestMoveStack(int32 StackId, FName ContainerId, int32 X, int32 Y, bool bRotate)
{
    if (!GetOwner()) return false;
    if (GetOwner()->HasAuthority()) return TryMoveStack(StackId, ContainerId, X, Y, bRotate);
    ServerRequestMoveStack(StackId, ContainerId, X, Y, bRotate);
    return true;
}

bool UAnomaliaInventoryComponent::RequestSplitStack(int32 StackId, int32 Count)
{
    if (!GetOwner()) return false;
    if (GetOwner()->HasAuthority()) { int32 NewStackId = 0; return TrySplitStack(StackId, Count, NewStackId); }
    ServerRequestSplitStack(StackId, Count);
    return true;
}

bool UAnomaliaInventoryComponent::RequestMergeStacks(int32 TargetStackId, int32 SourceStackId)
{
    if (!GetOwner()) return false;
    if (GetOwner()->HasAuthority()) return TryMergeStacks(TargetStackId, SourceStackId);
    ServerRequestMergeStacks(TargetStackId, SourceStackId);
    return true;
}

void UAnomaliaInventoryComponent::ServerRequestMoveStack_Implementation(int32 StackId, FName ContainerId, int32 X, int32 Y, bool bRotate)
{
    TryMoveStack(StackId, ContainerId, X, Y, bRotate);
}

void UAnomaliaInventoryComponent::ServerRequestSplitStack_Implementation(int32 StackId, int32 Count)
{
    int32 NewStackId = 0;
    TrySplitStack(StackId, Count, NewStackId);
}

void UAnomaliaInventoryComponent::ServerRequestMergeStacks_Implementation(int32 TargetStackId, int32 SourceStackId)
{
    TryMergeStacks(TargetStackId, SourceStackId);
}

void UAnomaliaInventoryComponent::OnRep_Stacks() { OnInventoryChanged(); OnInventoryUpdated.Broadcast(); }
void UAnomaliaInventoryComponent::OnRep_Compartments() { OnInventoryChanged(); OnInventoryUpdated.Broadcast(); }

void UAnomaliaInventoryComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UAnomaliaInventoryComponent, Stacks);
    DOREPLIFETIME(UAnomaliaInventoryComponent, Compartments);
    DOREPLIFETIME(UAnomaliaInventoryComponent, WeightCapacityKg);
}
