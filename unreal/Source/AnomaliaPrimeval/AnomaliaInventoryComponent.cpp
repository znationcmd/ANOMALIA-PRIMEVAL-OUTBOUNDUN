#include "AnomaliaInventoryComponent.h"
#include "AnomaliaLootPickup.h"
#include "AnomaliaStorageCatalog.h"
#include "AnomaliaItemEffectsComponent.h"
#include "AnomaliaConfigLibrary.h"
#include "AnomaliaLootSubsystem.h"
#include "AnomaliaSurvivor.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "AnomaliaVitalsComponent.h"
#include "AnomaliaGameMode.h"
#include "Engine/World.h"
#include "Dom/JsonObject.h"
#include "GameFramework/Actor.h"
#include "GameFramework/Controller.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "Net/UnrealNetwork.h"

UAnomaliaInventoryComponent::UAnomaliaInventoryComponent()
{
    SetIsReplicatedByDefault(true);
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickInterval = 1.f;
    FAnomaliaInventoryCompartment Pockets;
    Pockets.Id = TEXT("pockets");
    Pockets.Width = 6;
    Pockets.Height = 4;
    Compartments.Add(Pockets);
}

bool UAnomaliaInventoryComponent::GetItemRules(FName ItemId, float& OutWeightKg, int32& OutMaxStack, FIntPoint& OutSize) const
{
    FGuid KeyIdentity;
    const FString KeyName=ItemId.ToString();
    if(KeyName.StartsWith(TEXT("vehicle_key_")) && FGuid::ParseExact(KeyName.Mid(12),EGuidFormats::Digits,KeyIdentity) && KeyIdentity.IsValid())
    { OutWeightKg=.03f;OutMaxStack=1;OutSize=FIntPoint(1,1);return true; }
    static const TMap<FName, float> Weights = {
        // Storage parity with the additive JS resource catalogue; crafting is separate.
        {TEXT("tactical_belt"), .3f}, {TEXT("medical_pouch"), .25f},
        {TEXT("handheld_radio"), .3f}, {TEXT("frag_grenade"), .4f}, {TEXT("smoke_grenade"), .45f},
        {TEXT("handcuffs"), .35f}, {TEXT("pistol_holster"), .2f}, {TEXT("knife_sheath"), .1f},
        {TEXT("thatch"), 0.12f},
        {TEXT("fungal_wood"), 0.6f},
        {TEXT("flint"), 0.4f},
        {TEXT("fur"), 0.3f},
        {TEXT("wool"), 0.3f},
        {TEXT("keratin"), 0.3f},
        {TEXT("chitin"), 0.25f},
        {TEXT("metal_ore"), 1.2f},
        {TEXT("metal_ingot"), 1.f},
        {TEXT("crystal"), 0.6f},
        {TEXT("obsidian"), 0.8f},
        {TEXT("oil"), 0.8f},
        {TEXT("silica_pearls"), 0.2f},
        {TEXT("charcoal"), 0.15f},
        {TEXT("gunpowder"), 0.15f},
        {TEXT("sparkpowder"), 0.15f},
        {TEXT("cementing_paste"), 0.3f},
        {TEXT("achatina_paste"), 0.3f},
        {TEXT("electronics"), 0.2f},
        {TEXT("polymer"), 0.3f},
        {TEXT("organic_polymer"), 0.3f},
        {TEXT("gasoline"), 0.7f},
        {TEXT("absorbent_substrate"), 0.4f},
        {TEXT("black_pearls"), 0.2f},
        {TEXT("rare_mushroom"), 0.1f},
        {TEXT("angler_gel"), 0.25f},
        {TEXT("bio_toxin"), 0.2f},
        {TEXT("leech_blood"), 0.2f},
        {TEXT("woolly_rhino_horn"), 1.f},
        {TEXT("sulfur"), 0.6f},
        {TEXT("silk"), 0.15f},
        {TEXT("sand"), 0.6f},
        {TEXT("green_gem"), 0.3f},
        {TEXT("blue_gem"), 0.3f},
        {TEXT("red_gem"), 0.3f},
        {TEXT("condensed_gas"), 0.7f},
        {TEXT("element"), 0.5f},
        {TEXT("element_shard"), 0.2f},
        {TEXT("element_dust"), 0.05f},
        {TEXT("key_alpha"), .03f}, {TEXT("key_red"), .03f}, {TEXT("key_omega"), .03f},
        {TEXT("key_abyss"), .03f}, {TEXT("key_blue"), .03f}, {TEXT("key_bunker_alpha"), .03f},
        {TEXT("key_bunker_zero"), .03f}, {TEXT("key_container"), .03f},
        {TEXT("kibble_basic"), .3f}, {TEXT("kibble_simple"), .3f}, {TEXT("kibble_regular"), .3f},
        {TEXT("kibble_superior"), .3f}, {TEXT("kibble_exceptional"), .3f}, {TEXT("kibble_extraordinary"), .3f},
        {TEXT("honey"), .3f}, {TEXT("milk"), 1.f}, {TEXT("rare_flower"), .05f}, {TEXT("sap"), .1f}, {TEXT("vegetable"), .2f},
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
    if (!Weight)
    {
        const UAnomaliaLootSubsystem* Loot = GetWorld() ? GetWorld()->GetSubsystem<UAnomaliaLootSubsystem>() : nullptr;
        const FAnomaliaLootItem* Definition = Loot ? Loot->FindItem(ItemId) : nullptr;
        if (!Definition) return false;
        OutWeightKg = Definition->WeightKg;
        OutMaxStack = Definition->MaxStack;
        OutSize = Definition->Size;
        return true;
    }
    OutWeightKg = *Weight;
    OutSize = FIntPoint(1, 1);
    OutMaxStack = 20;
    if (ItemId == TEXT("rifle") || ItemId == TEXT("pistol") || ItemId == TEXT("saddle") ||
        ItemId == TEXT("fishing_rod") || ItemId == TEXT("headlamp") || ItemId == TEXT("medkit") ||
        ItemId == TEXT("jacket") || ItemId == TEXT("coat") || ItemId == TEXT("shirt") || ItemId == TEXT("pants") ||
        ItemId == TEXT("jeans") || ItemId == TEXT("boots") || ItemId == TEXT("helmet") ||
        ItemId == TEXT("backpack") || ItemId == TEXT("bag") || ItemId == TEXT("vest")) OutMaxStack = 1;
    if(ItemId==TEXT("handheld_radio")||ItemId==TEXT("frag_grenade")||ItemId==TEXT("smoke_grenade")||ItemId==TEXT("tactical_belt")||ItemId==TEXT("medical_pouch")||ItemId==TEXT("handcuffs")||ItemId==TEXT("pistol_holster")||ItemId==TEXT("knife_sheath")) {OutMaxStack=1;OutSize={2,2};}
    if (ItemId == TEXT("wood")) OutSize = FIntPoint(1, 3);
    else if (ItemId == TEXT("rifle") || ItemId == TEXT("fishing_rod")) OutSize = FIntPoint(2, 5);
    else if (ItemId == TEXT("saddle")) OutSize = FIntPoint(3, 3);
    else if (ItemId == TEXT("rifle") || ItemId == TEXT("pistol")) OutSize = FIntPoint(2, 2);
    else if (ItemId == TEXT("jacket") || ItemId == TEXT("coat") || ItemId == TEXT("shirt") || ItemId == TEXT("pants") ||
        ItemId == TEXT("jeans") || ItemId == TEXT("boots") || ItemId == TEXT("helmet") || ItemId == TEXT("backpack") ||
        ItemId == TEXT("bag") || ItemId == TEXT("vest")) OutSize = FIntPoint(2, 2);
    // Requested ANOMALIA footprints also apply to the preserved generic survival IDs.
    if(ItemId==TEXT("food")) OutSize={1,2};
    else if(ItemId==TEXT("water") || ItemId==TEXT("pistol")) OutSize={1,3};
    else if(ItemId==TEXT("rifle")) OutSize={3,3};
    else if(ItemId==TEXT("medkit")) OutSize={2,3};
    else if(ItemId==TEXT("jacket") || ItemId==TEXT("coat") || ItemId==TEXT("shirt")) OutSize={2,4};
    else if(ItemId==TEXT("pants") || ItemId==TEXT("jeans") || ItemId==TEXT("vest")) OutSize={2,3};
    else if(ItemId==TEXT("backpack") || ItemId==TEXT("bag")) OutSize={3,4};
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
    if (!GetOwner() || !GetOwner()->HasAuthority() || IsPersistenceLocked() || Id.IsNone() || Id == TEXT("hands") ||
        (Id.ToString().StartsWith(TEXT("migration_recovery_")) || Id.ToString().StartsWith(TEXT("mount_"))) || !UAnomaliaStorageCatalog::IsValidGrid(Width,Height)) return false;
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

bool UAnomaliaInventoryComponent::ConfigureCompartmentFromPreset(FName Id,FName PresetId)
{
    FIntPoint Grid;
    return UAnomaliaStorageCatalog::GetGrid(PresetId,Grid) && ConfigureCompartment(Id,Grid.X,Grid.Y);
}
FIntPoint UAnomaliaInventoryComponent::GetItemSize(FName ItemId,bool bRotated) const
{
    float Weight=0;int32 Limit=0;FIntPoint Size=FIntPoint::ZeroValue;
    if(!GetItemRules(ItemId,Weight,Limit,Size)) return FIntPoint::ZeroValue;
    if(bRotated) Swap(Size.X,Size.Y);
    return Size;
}
int32 UAnomaliaInventoryComponent::GetUsedCells(FName ContainerId) const
{
    int32 Cells=0;
    for(const auto& Stack:Stacks) if(Stack.ContainerId==ContainerId)
    { const auto Size=GetItemSize(Stack.ItemId,Stack.bRotated);Cells+=Size.X*Size.Y; }
    return Cells;
}
bool UAnomaliaInventoryComponent::IsRecoveryContainer(FName ContainerId) const
{
    const auto* Box=Compartments.FindByPredicate([&](const auto& C){return C.Id==ContainerId;});
    return Box && Box->bRecoveryOnly;
}

bool UAnomaliaInventoryComponent::CanPlace(const TArray<FAnomaliaInventoryStack>& Candidate,
    const FAnomaliaInventoryStack& Stack, FName ContainerId, int32 X, int32 Y, bool bRotate) const
{
    if(const auto* Rule=FindAttachmentRule(ContainerId))
    {
        const auto* Box=Compartments.FindByPredicate([&](const auto& B){return B.Id==ContainerId;});
        const bool Existing=Stack.ContainerId==ContainerId;
        return Box && X==0 && Y==0 && !bRotate && Stack.Count==1 && Rule->Items.Contains(Stack.ItemId) &&
            ((Existing&&Box->bRecoveryOnly)||AttachmentAvailable(Candidate,ContainerId)) &&
            !Candidate.ContainsByPredicate([&](const auto& Other){return Other.StackId!=Stack.StackId&&Other.ContainerId==ContainerId;});
    }
    if (ContainerId == TEXT("hands"))
        return !Candidate.ContainsByPredicate([&](const FAnomaliaInventoryStack& Other) { return Other.StackId != Stack.StackId && Other.ContainerId == TEXT("hands"); });
    const FAnomaliaInventoryCompartment* Box = Compartments.FindByPredicate([&](const FAnomaliaInventoryCompartment& C) { return C.Id == ContainerId; });
    float Weight = 0.f;
    int32 MaxStack = 0;
    FIntPoint Size;
    if (!Box || (Box->bRecoveryOnly && Stack.ContainerId!=ContainerId) || !GetItemRules(Stack.ItemId, Weight, MaxStack, Size)) return false;
    const FString BoxName=ContainerId.ToString();
    if(BoxName.StartsWith(TEXT("mount_"))&&BoxName.EndsWith(TEXT("_cargo")))
    {
        const FName Parent(*BoxName.LeftChop(6));
        const bool Equipped=AttachmentAvailable(Candidate,Parent)&&Candidate.ContainsByPredicate([&](const auto& S){return S.ContainerId==Parent&&S.ItemId==TEXT("medical_pouch")&&S.Count==1;});
        if(!Equipped&&!(Box->bRecoveryOnly&&Stack.ContainerId==ContainerId))return false;
    }
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

bool UAnomaliaInventoryComponent::FindPlacement(const TArray<FAnomaliaInventoryStack>& Candidate, FAnomaliaInventoryStack& Stack, bool bIncludeRecovery) const
{
    for (const FAnomaliaInventoryCompartment& Box : Compartments)
    {
        if(FindAttachmentRule(Box.Id))continue; // Automatic pickup never equips an attachment.
        if(Box.bRecoveryOnly && !bIncludeRecovery) continue;
        if(!UAnomaliaStorageCatalog::IsValidGrid(Box.Width,Box.Height)) return false;
        // One compact occupancy map per compartment. Large grids do not scan every
        // existing stack again for each candidate cell, and contain no UI widgets.
        TBitArray<> Occupied(false,Box.Width*Box.Height);
        for(const auto& Other:Candidate)
        {
            if(Other.StackId==Stack.StackId || Other.ContainerId!=Box.Id) continue;
            const auto Size=GetItemSize(Other.ItemId,Other.bRotated);
            if(Size.X<=0 || Size.Y<=0 || Other.X<0 || Other.Y<0 || Other.X+Size.X>Box.Width || Other.Y+Size.Y>Box.Height) return false;
            for(int32 Y=Other.Y;Y<Other.Y+Size.Y;++Y)
                for(int32 X=Other.X;X<Other.X+Size.X;++X) Occupied[Y*Box.Width+X]=true;
        }
        const auto OriginalSize=GetItemSize(Stack.ItemId);
        if(OriginalSize.X<=0 || OriginalSize.Y<=0) return false;
        for (int32 Y = 0; Y < Box.Height; ++Y)
            for (int32 X = 0; X < Box.Width; ++X)
                for (int32 Rotation = 0; Rotation < 2; ++Rotation)
                    {
                        auto Size=OriginalSize;if(Rotation==1) Swap(Size.X,Size.Y);
                        if(X+Size.X>Box.Width || Y+Size.Y>Box.Height) continue;
                        bool Free=true;
                        for(int32 DY=0;DY<Size.Y && Free;++DY)
                            for(int32 DX=0;DX<Size.X;++DX) if(Occupied[(Y+DY)*Box.Width+X+DX]) { Free=false;break; }
                        auto PlacementStack=Stack;
                        // Migration may place preserved items into withdrawal-only recovery;
                        // ordinary pickup and equipment requests never get this privilege.
                        if(bIncludeRecovery&&Box.bRecoveryOnly)PlacementStack.ContainerId=Box.Id;
                        if(Free && CanPlace(Candidate,PlacementStack,Box.Id,X,Y,Rotation==1))
                        {
                            Stack.ContainerId = Box.Id; Stack.X = X; Stack.Y = Y; Stack.bRotated = Rotation == 1;
                            return true;
                        }
                    }
    }
    return false;
}

void UAnomaliaInventoryComponent::Commit(TArray<FAnomaliaInventoryStack>&& Candidate)
{
    Stacks = MoveTemp(Candidate);
    if (!bSuppressNotifications) {SynchronizeAttachmentStorage();RefreshAttachmentVisuals();}
    if (bSuppressNotifications) return;
    if (GetOwner()) GetOwner()->ForceNetUpdate();
    OnInventoryChanged();
    OnInventoryUpdated.Broadcast();
}

bool UAnomaliaInventoryComponent::TryAddItem(FName ItemId, int32 Count)
{
    if (!GetOwner() || !GetOwner()->HasAuthority() || IsPersistenceLocked() || Count < 1) return false;
    float ItemWeight = 0.f;
    int32 MaxStack = 0;
    FIntPoint Size;
    if (!GetItemRules(ItemId, ItemWeight, MaxStack, Size) || GetCurrentWeightKg() + ItemWeight * Count > WeightCapacityKg + KINDA_SMALL_NUMBER) return false;
    TArray<FAnomaliaInventoryStack> Candidate = Stacks;
    int32 Remaining = Count;
    int32 CandidateNextId = NextStackId;
    for (FAnomaliaInventoryStack& Stack : Candidate)
    {
        if (Stack.ItemId != ItemId || Stack.Condition!=100.f || Stack.ContainerId == TEXT("hands") || FindAttachmentRule(Stack.ContainerId) || IsRecoveryContainer(Stack.ContainerId) || Stack.Count >= MaxStack) continue;
        const int32 Added = FMath::Min(Remaining, MaxStack - Stack.Count);
        Stack.Count += Added; Remaining -= Added;
        if (Remaining == 0) { Commit(MoveTemp(Candidate)); return true; }
    }
    while (Remaining > 0)
    {
        // Never accept live contents that the persistence reader cannot restore.
        if(Candidate.Num()>=MaxStacks) return false;
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
    if (!GetOwner() || !GetOwner()->HasAuthority() || IsPersistenceLocked() || ItemId.IsNone() || Count < 1) return false;
    int32 Available = 0;
    for (const FAnomaliaInventoryStack& Stack : Stacks)
        if (Stack.ItemId == ItemId && Stack.Count > 0 && !HasAttachmentDependents(Stack.StackId)) Available += Stack.Count;
    if (Available < Count) return false;
    TArray<FAnomaliaInventoryStack> Candidate = Stacks;
    int32 Remaining = Count;
    for (int32 Index = Candidate.Num() - 1; Index >= 0 && Remaining > 0; --Index)
    {
        FAnomaliaInventoryStack& Stack = Candidate[Index];
        if (Stack.ItemId != ItemId || HasAttachmentDependents(Stack.StackId)) continue;
        const int32 Removed = FMath::Min(Remaining, Stack.Count);
        Stack.Count -= Removed;
        Remaining -= Removed;
    }
    Candidate.RemoveAll([](const FAnomaliaInventoryStack& Stack) { return Stack.Count <= 0; });
    Commit(MoveTemp(Candidate));
    return true;
}

bool UAnomaliaInventoryComponent::TryTransferStackTo(int32 StackId,int32 ExpectedCount,UAnomaliaInventoryComponent* Destination,bool bToHands)
{
    if(!GetOwner() || !GetOwner()->HasAuthority() || IsPersistenceLocked() || !Destination || Destination==this ||
       !Destination->GetOwner() || !Destination->GetOwner()->HasAuthority() || Destination->IsPersistenceLocked() ||
       Destination->Stacks.Num()>=MaxStacks || Destination->NextStackId>=MAX_int32)return false;
    const auto* Existing=Stacks.FindByPredicate([&](const auto& Stack){return Stack.StackId==StackId;});
    if(!Existing || ExpectedCount<1 || Existing->Count!=ExpectedCount || HasAttachmentDependents(StackId))return false;
    float Weight=0;int32 Limit=0;FIntPoint Size;
    if(!GetItemRules(Existing->ItemId,Weight,Limit,Size) ||
       Destination->GetCurrentWeightKg()+Weight*Existing->Count>Destination->WeightCapacityKg+KINDA_SMALL_NUMBER)return false;
    auto Piece=*Existing;Piece.StackId=Destination->NextStackId;Piece.ContainerId=NAME_None;Piece.bRotated=false;
    auto To=Destination->Stacks;
    if(bToHands)
    {
        Piece.ContainerId=TEXT("hands");Piece.X=Piece.Y=0;
        if(!Destination->CanPlace(To,Piece,Piece.ContainerId,0,0,false))return false;
    }
    else if(!Destination->FindPlacement(To,Piece))return false;
    To.Add(Piece);auto From=Stacks;From.RemoveAll([&](const auto& Stack){return Stack.StackId==StackId;});
    ++Destination->NextStackId;Destination->Commit(MoveTemp(To));Commit(MoveTemp(From));return true;
}

bool UAnomaliaInventoryComponent::TryMoveStack(int32 StackId, FName ContainerId, int32 X, int32 Y, bool bRotate)
{
    if (!GetOwner() || !GetOwner()->HasAuthority() || IsPersistenceLocked()) return false;
    TArray<FAnomaliaInventoryStack> Candidate = Stacks;
    FAnomaliaInventoryStack* Stack = Candidate.FindByPredicate([&](const FAnomaliaInventoryStack& S) { return S.StackId == StackId; });
    if (!Stack || (Stack->ContainerId!=ContainerId && HasAttachmentDependents(StackId)) || !CanPlace(Candidate, *Stack, ContainerId, X, Y, bRotate)) return false;
    Stack->ContainerId = ContainerId; Stack->X = X; Stack->Y = Y; Stack->bRotated = bRotate;
    Commit(MoveTemp(Candidate));
    return true;
}

bool UAnomaliaInventoryComponent::TryStowStack(int32 StackId)
{
    if (!GetOwner() || !GetOwner()->HasAuthority() || IsPersistenceLocked()) return false;
    TArray<FAnomaliaInventoryStack> Candidate = Stacks;
    auto* Stack = Candidate.FindByPredicate([&](const auto& S) { return S.StackId == StackId; });
    if (!Stack || Stack->ContainerId != TEXT("hands") || !FindPlacement(Candidate, *Stack)) return false;
    Commit(MoveTemp(Candidate));
    return true;
}

bool UAnomaliaInventoryComponent::TrySplitStack(int32 StackId, int32 Count, int32& OutNewStackId)
{
    OutNewStackId = 0;
    if (!GetOwner() || !GetOwner()->HasAuthority() || IsPersistenceLocked()) return false;
    TArray<FAnomaliaInventoryStack> Candidate = Stacks;
    FAnomaliaInventoryStack* Source = Candidate.FindByPredicate([&](const FAnomaliaInventoryStack& S) { return S.StackId == StackId; });
    if (!Source || Candidate.Num()>=MaxStacks || NextStackId >= MAX_int32 || Count < 1 || Count >= Source->Count || Source->ContainerId == TEXT("hands")) return false;
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
    if (!GetOwner() || !GetOwner()->HasAuthority() || IsPersistenceLocked() || TargetStackId == SourceStackId) return false;
    TArray<FAnomaliaInventoryStack> Candidate = Stacks;
    FAnomaliaInventoryStack* Target = Candidate.FindByPredicate([&](const FAnomaliaInventoryStack& S) { return S.StackId == TargetStackId; });
    FAnomaliaInventoryStack* Source = Candidate.FindByPredicate([&](const FAnomaliaInventoryStack& S) { return S.StackId == SourceStackId; });
    if (!Target || !Source || FindAttachmentRule(Target->ContainerId) || FindAttachmentRule(Source->ContainerId) || Target->ItemId != Source->ItemId || Target->Condition!=Source->Condition || Target->ContainerId == TEXT("hands") || Source->ContainerId == TEXT("hands")) return false;
    if(IsRecoveryContainer(Target->ContainerId) && !IsRecoveryContainer(Source->ContainerId)) return false;
    float Weight = 0.f; int32 MaxStack = 0; FIntPoint Size;
    if (!GetItemRules(Target->ItemId, Weight, MaxStack, Size) || Target->Count + Source->Count > MaxStack) return false;
    Target->Count += Source->Count;
    Candidate.RemoveAll([&](const FAnomaliaInventoryStack& S) { return S.StackId == SourceStackId; });
    Commit(MoveTemp(Candidate));
    return true;
}

bool UAnomaliaInventoryComponent::SaveInventoryToPlayerProfile(const FString& ServerId, const FString& PlayerId, FString& OutError)
{
    if (!GetOwner() || !GetOwner()->HasAuthority() || IsPersistenceLocked())
    { OutError = TEXT("Inventory persistence is unavailable or locked for recovery"); return false; }
    FString Serialized;
    return BuildInventoryProfile(ServerId, PlayerId, Serialized, OutError) &&
        UAnomaliaConfigLibrary::SavePlayerProfile(ServerId, PlayerId, Serialized, OutError);
}

TSharedPtr<FJsonObject> UAnomaliaInventoryComponent::ExportInventoryObject() const
{
    TSharedPtr<FJsonObject> Inventory = MakeShared<FJsonObject>();
    Inventory->SetNumberField(TEXT("schemaVersion"), 1);
    Inventory->SetNumberField(TEXT("layoutVersion"), 2);
    Inventory->SetNumberField(TEXT("weightCapacityKg"), WeightCapacityKg);
    TArray<TSharedPtr<FJsonValue>> CompartmentRows;
    for (const FAnomaliaInventoryCompartment& Box : Compartments)
    {
        TSharedPtr<FJsonObject> Row = MakeShared<FJsonObject>();
        Row->SetStringField(TEXT("id"), Box.Id.ToString());
        Row->SetNumberField(TEXT("width"), Box.Width);
        Row->SetNumberField(TEXT("height"), Box.Height);
        Row->SetBoolField(TEXT("recoveryOnly"),Box.bRecoveryOnly);
        Row->SetNumberField(TEXT("condition"),Box.Condition);
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
        Row->SetNumberField(TEXT("condition"),Stack.Condition);
        StackRows.Add(MakeShared<FJsonValueObject>(Row));
    }
    Inventory->SetArrayField(TEXT("stacks"), StackRows);
    return Inventory;
}

bool UAnomaliaInventoryComponent::BuildInventoryProfile(const FString& ServerId, const FString& PlayerId, FString& OutJson, FString& OutError)
{
    OutJson.Empty();
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

    TSharedPtr<FJsonObject> Inventory = ExportInventoryObject();
    Profile->SetObjectField(TEXT("inventory"), Inventory);

    FString Serialized;
    const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Serialized);
    if (!FJsonSerializer::Serialize(Profile.ToSharedRef(), Writer))
    {
        OutError = TEXT("Could not serialize inventory profile");
        return false;
    }
    OutJson = MoveTemp(Serialized);
    return true;
}

bool UAnomaliaInventoryComponent::LoadInventoryFromPlayerProfile(const FString& ServerId, const FString& PlayerId, FString& OutError)
{
    OutError.Empty();
    if (!GetOwner() || !GetOwner()->HasAuthority() || bPersistenceLocked) { OutError = TEXT("Inventory persistence requires server authority"); return false; }
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
    double Layout=1;
    if(!(*InventoryPtr)->HasField(TEXT("layoutVersion")))
    {
        if(!UAnomaliaConfigLibrary::BackupInventoryLayout(ServerId,PlayerId,Raw,OutError)) return false;
    }
    else if((*InventoryPtr)->TryGetNumberField(TEXT("layoutVersion"),Layout) && Layout<2)
        if(!UAnomaliaConfigLibrary::BackupInventoryLayout(ServerId,PlayerId,Raw,OutError)) return false;
    return LoadInventoryObject(*InventoryPtr,OutError);
}

bool UAnomaliaInventoryComponent::LoadInventoryObject(const TSharedPtr<FJsonObject>& Inventory,FString& OutError)
{
    OutError.Empty();
    if(!GetOwner() || !GetOwner()->HasAuthority() || bPersistenceLocked || !Inventory.IsValid())
    { OutError=TEXT("Inventory snapshot requires available authority");return false; }
    double SchemaVersion = 0.0;
    double LayoutVersion = 1;
    if(Inventory->HasField(TEXT("layoutVersion")) &&
        (!Inventory->TryGetNumberField(TEXT("layoutVersion"),LayoutVersion) || (LayoutVersion!=1 && LayoutVersion!=2)))
    { OutError=TEXT("Unsupported inventory layout version");return false; }
    double SavedCapacity = 0.0;
    if (!Inventory->TryGetNumberField(TEXT("schemaVersion"), SchemaVersion) || SchemaVersion != 1.0 ||
        !Inventory->TryGetNumberField(TEXT("weightCapacityKg"), SavedCapacity) || !FMath::IsFinite(SavedCapacity) || SavedCapacity < 0.1 || SavedCapacity > 500.0)
    {
        OutError = TEXT("Invalid inventory capacity in profile");
        return false;
    }
    const TArray<TSharedPtr<FJsonValue>>* CompartmentRows = nullptr;
    const TArray<TSharedPtr<FJsonValue>>* StackRows = nullptr;
    if (!Inventory->TryGetArrayField(TEXT("compartments"), CompartmentRows) || !CompartmentRows || CompartmentRows->Num() < 1 || CompartmentRows->Num() > 128 ||
        !Inventory->TryGetArrayField(TEXT("stacks"), StackRows) || !StackRows || StackRows->Num() > MaxStacks)
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
            !FMath::IsFinite(Width) || !FMath::IsFinite(Height) || Width < 1 || Width > UAnomaliaStorageCatalog::MaxDimension || Height < 1 || Height > UAnomaliaStorageCatalog::MaxDimension || Width*Height>UAnomaliaStorageCatalog::MaxCells ||
            !FMath::IsNearlyEqual(Width, static_cast<double>(FMath::RoundToInt(Width))) ||
            !FMath::IsNearlyEqual(Height, static_cast<double>(FMath::RoundToInt(Height))))
        { OutError = TEXT("Invalid inventory compartment dimensions"); return false; }
        const FName Id(*IdText);
        if (Id.IsNone() || Id == TEXT("hands") || SeenCompartments.Contains(Id)) { OutError = TEXT("Duplicate or reserved inventory compartment"); return false; }
        SeenCompartments.Add(Id);
        FAnomaliaInventoryCompartment Box;
        Box.Id = Id; Box.Width = FMath::RoundToInt(Width); Box.Height = FMath::RoundToInt(Height);
        if(Row->HasField(TEXT("recoveryOnly")) && !Row->TryGetBoolField(TEXT("recoveryOnly"),Box.bRecoveryOnly))
        { OutError=TEXT("Invalid migration compartment flag");return false; }
        const bool Migration=IdText.StartsWith(TEXT("migration_recovery_"));
        const bool Worn=Box.Id==TEXT("worn_top")||Box.Id==TEXT("worn_legs")||Box.Id==TEXT("worn_back")||
            Box.Id==TEXT("worn_vest")||Box.Id==TEXT("worn_head")||Box.Id==TEXT("worn_gloves")||Box.Id==TEXT("worn_feet");
        if((Migration&&!Box.bRecoveryOnly)||(!Migration&&!Worn&&!IdText.StartsWith(TEXT("mount_"))&&Box.bRecoveryOnly))
        { OutError=TEXT("Invalid reserved migration compartment");return false; }
        double Condition=100;
        if(Row->HasField(TEXT("condition"))&&(!Row->TryGetNumberField(TEXT("condition"),Condition)||!FMath::IsFinite(Condition)||Condition<0||Condition>100||(!Worn&&Condition!=100)))
        {OutError=TEXT("Invalid compartment condition");return false;}
        Box.Condition=static_cast<float>(Condition);
        if(IdText.StartsWith(TEXT("mount_")))
        {
            const auto* Rule=FindAttachmentRule(Id);
            const bool Medical=IdText.EndsWith(TEXT("_cargo")) && FindAttachmentRule(FName(*IdText.LeftChop(6))) &&
                FindAttachmentRule(FName(*IdText.LeftChop(6)))->Items.Contains(TEXT("medical_pouch"));
            if((Rule&&(Box.Width!=16||Box.Height!=16))||(!Rule&&(!Medical||Box.Width!=4||Box.Height!=3)))
            {OutError=TEXT("Invalid reserved attachment storage");return false;}
        }
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
            X < 0 || X >= UAnomaliaStorageCatalog::MaxDimension || Y < 0 || Y >= UAnomaliaStorageCatalog::MaxDimension ||
            !FMath::IsNearlyEqual(StackId, static_cast<double>(FMath::RoundToInt(StackId))) ||
            !FMath::IsNearlyEqual(Count, static_cast<double>(FMath::RoundToInt(Count))) ||
            !FMath::IsNearlyEqual(X, static_cast<double>(FMath::RoundToInt(X))) ||
            !FMath::IsNearlyEqual(Y, static_cast<double>(FMath::RoundToInt(Y))))
        { OutError = TEXT("Invalid inventory stack fields"); return false; }
        FAnomaliaInventoryStack Stack;
        Stack.StackId = FMath::RoundToInt(StackId); Stack.Count = FMath::RoundToInt(Count); Stack.X = FMath::RoundToInt(X); Stack.Y = FMath::RoundToInt(Y);
        Stack.ItemId = FName(*ItemText); Stack.ContainerId = FName(*ContainerText); Stack.bRotated = bRotated;
        double Condition=100;
        if(Row->HasField(TEXT("condition"))&&(!Row->TryGetNumberField(TEXT("condition"),Condition)||!FMath::IsFinite(Condition)||Condition<0||Condition>100||(!SupportsItemWear(Stack.ItemId)&&Condition!=100)))
        {OutError=TEXT("Invalid item condition");return false;}
        Stack.Condition=static_cast<float>(Condition);
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
    for(auto& Box:Compartments)if(FindAttachmentRule(Box.Id)&&!AttachmentAvailable(LoadedStacks,Box.Id))Box.bRecoveryOnly=true;
    bool ValidLayout=true;
    for (const FAnomaliaInventoryStack& Stack : LoadedStacks)
    {
        if (!CanPlace(LoadedStacks, Stack, Stack.ContainerId, Stack.X, Stack.Y, Stack.bRotated))
            ValidLayout=false;
    }
    if(!ValidLayout && LayoutVersion!=1)
    {
        Compartments=PreviousCompartments;
        OutError=TEXT("Saved inventory layout overlaps or exceeds its compartments");return false;
    }
    if(!ValidLayout)
    {
        const auto* Loot=GetWorld()?GetWorld()->GetSubsystem<UAnomaliaLootSubsystem>():nullptr;
        auto LegacySize=[&](const FAnomaliaInventoryStack& S)
        {
            FIntPoint Size(1,1);
            // The previous catalogue used 1x1 definitions; generic legacy IDs
            // had a small number of larger native footprints.
            if(!(Loot && Loot->FindItem(S.ItemId)))
            {
                if(S.ItemId==TEXT("wood")) Size={1,3};
                else if(S.ItemId==TEXT("rifle") || S.ItemId==TEXT("fishing_rod")) Size={2,5};
                else if(S.ItemId==TEXT("saddle")) Size={3,3};
                else if(S.ItemId==TEXT("pistol") || S.ItemId==TEXT("jacket") || S.ItemId==TEXT("coat") ||
                    S.ItemId==TEXT("shirt") || S.ItemId==TEXT("pants") || S.ItemId==TEXT("jeans") || S.ItemId==TEXT("boots") ||
                    S.ItemId==TEXT("helmet") || S.ItemId==TEXT("backpack") || S.ItemId==TEXT("bag") || S.ItemId==TEXT("vest")) Size={2,2};
            }
            if(S.bRotated) Swap(Size.X,Size.Y);return Size;
        };
        // Migration repairs only geometry changed by this version, not corrupt
        // legacy overlaps, missing compartments or multiple held objects.
        for(int32 Index=0;Index<LoadedStacks.Num();++Index)
        {
            const auto& S=LoadedStacks[Index];const auto Size=LegacySize(S);
            const auto* Box=Compartments.FindByPredicate([&](const auto& C){return C.Id==S.ContainerId;});
            bool Valid=S.ContainerId==TEXT("hands") || (Box && S.X+Size.X<=Box->Width && S.Y+Size.Y<=Box->Height);
            for(int32 OtherIndex=0;OtherIndex<Index && Valid;++OtherIndex)
            {
                const auto& Other=LoadedStacks[OtherIndex];if(Other.ContainerId!=S.ContainerId) continue;
                const auto OtherSize=LegacySize(Other);
                if(S.ContainerId==TEXT("hands") || (S.X<Other.X+OtherSize.X && S.X+Size.X>Other.X && S.Y<Other.Y+OtherSize.Y && S.Y+Size.Y>Other.Y)) Valid=false;
            }
            if(!Valid) { Compartments=PreviousCompartments;OutError=TEXT("Malformed legacy inventory preserved without migration");return false; }
        }
        TArray<FAnomaliaInventoryStack> Repacked;
        for(auto Stack:LoadedStacks)
        {
            if(Stack.ContainerId==TEXT("hands")) { Repacked.Add(Stack);continue; }
            if(!CanPlace(Repacked,Stack,Stack.ContainerId,Stack.X,Stack.Y,Stack.bRotated) && !FindPlacement(Repacked,Stack))
            {
                if(!FindPlacement(Repacked,Stack,true))
                {
                    if(Compartments.Num()>=128) { Compartments=PreviousCompartments;OutError=TEXT("Legacy recovery compartment limit reached; profile preserved");return false; }
                    FAnomaliaInventoryCompartment Recovery;
                    int32 Index=0;do { Recovery.Id=FName(*FString::Printf(TEXT("migration_recovery_%d"),Index++)); }
                    while(Compartments.ContainsByPredicate([&](const auto& C){return C.Id==Recovery.Id;}));
                    Recovery.Width=1000;Recovery.Height=100;Recovery.bRecoveryOnly=true;
                    Compartments.Add(Recovery);
                    if(!FindPlacement(Repacked,Stack,true))
                    { Compartments=PreviousCompartments;OutError=TEXT("Unable to preserve legacy item placement");return false; }
                }
            }
            Repacked.Add(Stack);
        }
        LoadedStacks=MoveTemp(Repacked);
        UseMessage=TEXT("Ancien rangement adapté : les éventuels objets en récupération peuvent être retirés sans perte.");
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

bool UAnomaliaInventoryComponent::RequestStowStack(int32 StackId)
{
    if (!GetOwner()) return false;
    if (GetOwner()->HasAuthority()) return TryStowStack(StackId);
    ServerRequestStowStack(StackId);
    return true;
}

void UAnomaliaInventoryComponent::ServerRequestStowStack_Implementation(int32 StackId)
{
    TryStowStack(StackId);
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

FAnomaliaItemUseRule UAnomaliaInventoryComponent::GetUseRule(FName ItemId) const
{
    const auto* Loot=GetWorld()?GetWorld()->GetSubsystem<UAnomaliaLootSubsystem>():nullptr;
    if(const auto* Item=Loot?Loot->FindItem(ItemId):nullptr) return Item->Use;
    // Preserve the existing generic survival item IDs alongside the full loot catalogue.
    FAnomaliaItemUseRule Rule;
    if(ItemId==TEXT("food") || ItemId==TEXT("meat") || ItemId==TEXT("cooked_meat") || ItemId==TEXT("cooked_fish"))
    { Rule.Action=TEXT("eat");Rule.Hunger=ItemId==TEXT("food")?27.f:34.f; }
    else if(ItemId==TEXT("berry")) { Rule.Action=TEXT("eat");Rule.Hunger=7.f;Rule.Thirst=3.f; }
    else if(ItemId==TEXT("water")) { Rule.Action=TEXT("drink");Rule.Thirst=38.f; }
    else if(ItemId==TEXT("bandage") || ItemId==TEXT("medkit"))
    { Rule.Action=TEXT("heal");Rule.Health=ItemId==TEXT("medkit")?50.f:19.f; }
    return Rule;
}

FString UAnomaliaInventoryComponent::GetItemDisplayName(FName ItemId) const
{
    if(ItemId.ToString().StartsWith(TEXT("vehicle_key_")))return TEXT("Clé véhicule · ")+ItemId.ToString().Right(6);
    const auto* Loot=GetWorld()?GetWorld()->GetSubsystem<UAnomaliaLootSubsystem>():nullptr;
    const auto* Item=Loot?Loot->FindItem(ItemId):nullptr;
    if(Item)return Item->DisplayName;
    static const TMap<FName,FString> Labels={{TEXT("tactical_belt"),TEXT("Ceinture tactique")},{TEXT("medical_pouch"),TEXT("Sacoche médicale")},{TEXT("handcuffs"),TEXT("Menottes")},{TEXT("pistol_holster"),TEXT("Holster")},{TEXT("knife_sheath"),TEXT("Fourreau")},{TEXT("handheld_radio"),TEXT("Radio")},{TEXT("frag_grenade"),TEXT("Grenade")},{TEXT("smoke_grenade"),TEXT("Fumigène")},{TEXT("cloth"),TEXT("Tissu")},{TEXT("fiber"),TEXT("Fibres")},{TEXT("wood"),TEXT("Bois")},{TEXT("stone"),TEXT("Pierre")},{TEXT("bandage"),TEXT("Pansement")},{TEXT("saddle"),TEXT("Selle")}};
    const auto* Label=Labels.Find(ItemId);return Label?*Label:ItemId.ToString();
}

FString UAnomaliaInventoryComponent::GetUseActionLabel(FName ItemId) const
{
    const auto Rule=GetUseRule(ItemId);
    if(!Rule.IsUsable()) return FString();
    return Rule.Action==TEXT("eat")?TEXT("Manger") : Rule.Action==TEXT("drink")?TEXT("Boire"):
        Rule.Action==TEXT("smoke")?TEXT("Fumer (RP)"):Rule.Action==TEXT("rp")?TEXT("Utiliser (RP)"):
        Rule.Action==TEXT("purify")?TEXT("Traiter l’eau (jeu)"):TEXT("Soigner / examiner");
}

bool UAnomaliaInventoryComponent::TryUseStack(int32 StackId,int32 ExpectedCount,const FString& ServerId,const FString& PlayerId,FString& OutError)
{
    OutError.Empty();
    auto* Survivor=Cast<AAnomaliaSurvivor>(GetOwner());
    const auto* Loot=GetWorld()?GetWorld()->GetSubsystem<UAnomaliaLootSubsystem>():nullptr;
    const auto* Economy=GetWorld()?GetWorld()->GetSubsystem<UAnomaliaEconomySubsystem>():nullptr;
    if(!Survivor || !Survivor->HasAuthority() || IsPersistenceLocked() || bSuppressNotifications ||
       Survivor->Health<=0 || Survivor->bSleeping || (Loot && Loot->HasPendingPlayer(PlayerId)) ||
       (Economy && Economy->HasPendingPlayer(PlayerId)))
    { OutError=TEXT("Utilisation indisponible pendant une sauvegarde, le sommeil ou sans personnage vivant.");return false; }
    const auto* Stack=Stacks.FindByPredicate([&](const auto& S){return S.StackId==StackId;});
    if(!Stack || ExpectedCount<1 || Stack->Count!=ExpectedCount)
    { OutError=TEXT("La pile a changé : sélectionnez de nouveau l’objet.");return false; }
    const FName ItemId=Stack->ItemId;
    const auto Rule=GetUseRule(ItemId);
    if(!Rule.IsUsable()) { OutError=TEXT("Cet objet nécessite une autre interaction.");return false; }
    const auto* Mode=GetWorld()?GetWorld()->GetAuthGameMode<AAnomaliaGameMode>():nullptr;
    if(Mode && ((Rule.RestrictedGroup==TEXT("substances") && !Mode->ActiveServerSettings.bAllowRPSubstances) ||
        (Rule.RestrictedGroup==TEXT("tobacco") && !Mode->ActiveServerSettings.bAllowTobacco) ||
        (Rule.RestrictedGroup==TEXT("alcohol") && !Mode->ActiveServerSettings.bAllowAlcohol)))
    { OutError=TEXT("Cette catégorie est désactivée dans les règles de cette partie.");return false; }
    if(!Rule.RequiredItem.IsNone() && !Stacks.ContainsByPredicate([&](const auto& S)
        { return S.Count>0 && (S.ItemId==Rule.RequiredItem || (Rule.RequiredItem==TEXT("lighter") && S.ItemId==TEXT("matches"))); }))
    { OutError=TEXT("Matériel nécessaire : ")+GetItemDisplayName(Rule.RequiredItem);return false; }
    auto* Effects=Survivor->ItemEffectsComponent.Get();
    FAnomaliaItemEffectsState NextEffects;
    if(!Effects || !Effects->PreviewUse(Rule.Effect,NextEffects))
    { OutError=TEXT("État des effets invalide.");return false; }
    if(!FMath::IsFinite(Survivor->Hunger) || !FMath::IsFinite(Survivor->Thirst) || !FMath::IsFinite(Survivor->Health))
    { OutError=TEXT("État du personnage invalide.");return false; }
    const float Food=FMath::Clamp(Survivor->Hunger+Rule.Hunger,0.f,100.f);
    const float Water=FMath::Clamp(Survivor->Thirst+Rule.Thirst,0.f,100.f);
    const float HP=FMath::Clamp(Survivor->Health+Rule.Health,0.f,100.f);
    if(Food==Survivor->Hunger && Water==Survivor->Thirst && HP==Survivor->Health && !Effects->HasChange(NextEffects) && Rule.Action!=TEXT("purify"))
    { OutError=TEXT("Aucun besoin à restaurer : l’objet est conservé.");return false; }

    const auto Before=Stacks;const int32 BeforeId=NextStackId;
    auto Rollback=[&](){Stacks=Before;NextStackId=BeforeId;bSuppressNotifications=false;};
    bSuppressNotifications=true;
    auto* Selected=Stacks.FindByPredicate([&](const auto& S){return S.StackId==StackId;});
    --Selected->Count;
    Stacks.RemoveAll([](const auto& S){return S.Count<=0;});
    if(Rule.Action==TEXT("purify") && !TryRemoveItem(Rule.RequiredItem,1))
    { Rollback();OutError=TEXT("La bouteille d’eau non traitée n’est plus disponible.");return false; }
    if(!Rule.ReturnItem.IsNone() && !TryAddItem(Rule.ReturnItem,1))
    { Rollback();OutError=TEXT("Faites de la place pour le contenant vide. L’objet est conservé.");return false; }
    FString Raw;
    if(!BuildInventoryProfile(ServerId,PlayerId,Raw,OutError)) { Rollback();return false; }
    const auto After=Stacks;const int32 AfterId=NextStackId;
    Rollback();
    TSharedPtr<FJsonObject> Profile;
    if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Raw),Profile) || !Profile.IsValid())
    { OutError=TEXT("Profil de sauvegarde invalide.");return false; }
    TSharedPtr<FJsonObject> Survival=MakeShared<FJsonObject>();
    const TSharedPtr<FJsonObject>* Existing=nullptr;
    if(Profile->HasField(TEXT("survival")))
    {
        if(!Profile->TryGetObjectField(TEXT("survival"),Existing) || !Existing || !Existing->IsValid())
        { OutError=TEXT("Données de survie existantes invalides : profil conservé.");return false; }
        Survival=*Existing;
    }
    Survival->SetNumberField(TEXT("hunger"),Food);Survival->SetNumberField(TEXT("thirst"),Water);
    Survival->SetNumberField(TEXT("health"),HP);Survival->SetNumberField(TEXT("fatigue"),Survivor->Fatigue);
    if(const auto* Vitals=Survivor->VitalsComponent.Get())
    {
        Survival->SetNumberField(TEXT("stamina"),Vitals->Stamina);
        Survival->SetNumberField(TEXT("bodyTemperatureC"),Vitals->BodyTemperatureC);
    }
    Profile->SetObjectField(TEXT("survival"),Survival);
    if(!UAnomaliaItemEffectsComponent::WriteState(Survival,NextEffects,OutError)) return false;
    Raw.Empty();
    if(!FJsonSerializer::Serialize(Profile.ToSharedRef(),TJsonWriterFactory<>::Create(&Raw)) ||
       !UAnomaliaConfigLibrary::SavePlayerProfile(ServerId,PlayerId,Raw,OutError)) return false;
    // Publish both sides only after their single combined profile write succeeds.
    Survivor->Hunger=Food;Survivor->Thirst=Water;Survivor->Health=HP;
    Effects->ApplyState(NextEffects);
    NextStackId=AfterId;UseMessage=TEXT("Utilisé : ")+GetItemDisplayName(ItemId);
    if(Rule.Effect==TEXT("diagnostic"))
        UseMessage=FString::Printf(TEXT("Bilan de jeu — sang : %.0f %%, douleur : %.0f %%, infection fictive : %.0f %%"),NextEffects.Blood,NextEffects.Pain,NextEffects.Infection);
    auto Committed=After;Commit(MoveTemp(Committed));Survivor->OnSurvivalChanged();
    return true;
}

bool UAnomaliaInventoryComponent::UseFromOwningPlayer(int32 StackId,int32 ExpectedCount)
{
    const auto* Survivor=Cast<AAnomaliaSurvivor>(GetOwner());
    const auto* Mode=GetWorld()?GetWorld()->GetAuthGameMode<AAnomaliaGameMode>():nullptr;
    if(!Survivor || !Survivor->HasAuthority() || !Mode || !Survivor->GetController() ||
       Survivor->GetController()->GetPawn()!=Survivor) return false;
    const double Now=GetWorld()->GetRealTimeSeconds();
    if(Now<NextUseRequestTime) return false;
    NextUseRequestTime=Now+.2;
    FString Error;
    const bool Accepted=TryUseStack(StackId,ExpectedCount,Mode->ServerId,Mode->GetPersistentPlayerId(Survivor->GetController()),Error);
    if(!Accepted) { UseMessage=Error;OnInventoryUpdated.Broadcast();GetOwner()->ForceNetUpdate(); }
    return Accepted;
}

bool UAnomaliaInventoryComponent::RequestUseStack(int32 StackId,int32 ExpectedCount)
{
    if(!GetOwner()) return false;
    if(GetOwner()->HasAuthority()) return UseFromOwningPlayer(StackId,ExpectedCount);
    ServerRequestUseStack(StackId,ExpectedCount);return true;
}

void UAnomaliaInventoryComponent::ServerRequestUseStack_Implementation(int32 StackId,int32 ExpectedCount)
{
    UseFromOwningPlayer(StackId,ExpectedCount);
}

void UAnomaliaInventoryComponent::OnRep_Stacks() { RefreshAttachmentVisuals();OnInventoryChanged(); OnInventoryUpdated.Broadcast(); }
void UAnomaliaInventoryComponent::OnRep_Compartments() { RefreshAttachmentVisuals();OnInventoryChanged(); OnInventoryUpdated.Broadcast(); }

void UAnomaliaInventoryComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UAnomaliaInventoryComponent, Stacks);
    DOREPLIFETIME_CONDITION(UAnomaliaInventoryComponent, CashBalanceCents, COND_OwnerOnly);
    DOREPLIFETIME(UAnomaliaInventoryComponent, Compartments);
    DOREPLIFETIME(UAnomaliaInventoryComponent, WeightCapacityKg);
    DOREPLIFETIME_CONDITION(UAnomaliaInventoryComponent, BankAccountId, COND_OwnerOnly);
    DOREPLIFETIME_CONDITION(UAnomaliaInventoryComponent, BankBalanceCents, COND_OwnerOnly);
    DOREPLIFETIME_CONDITION(UAnomaliaInventoryComponent, NextBankSequence, COND_OwnerOnly);
    DOREPLIFETIME_CONDITION(UAnomaliaInventoryComponent, bBankingAvailable, COND_OwnerOnly);
    DOREPLIFETIME_CONDITION(UAnomaliaInventoryComponent, BankMessage, COND_OwnerOnly);
    DOREPLIFETIME_CONDITION(UAnomaliaInventoryComponent, UseMessage, COND_OwnerOnly);
}

void UAnomaliaInventoryComponent::SetProfileRecoveryPending(bool Pending)
{
    if (GetOwner() && GetOwner()->HasAuthority()) bProfileRecoveryPending = Pending;
}
void UAnomaliaInventoryComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* TickFunction)
{
    Super::TickComponent(DeltaTime, TickType, TickFunction);
    RefreshAttachmentVisuals();
    if (!GetOwner() || !GetOwner()->HasAuthority() || !GetWorld()) return;
    const auto* Survivor = Cast<AAnomaliaSurvivor>(GetOwner());
    const auto* Mode = GetWorld()->GetAuthGameMode<AAnomaliaGameMode>();
    auto* Economy = GetWorld()->GetSubsystem<UAnomaliaEconomySubsystem>();
    SynchronizeWornStorage();
    if(Survivor)
    {
        const FVector Location=Survivor->GetActorLocation();
        if(bHasWearLocation){const float Distance=FVector::Dist2D(Location,LastWearLocation);if(Distance>1.f&&Distance<2500.f&&Survivor->GetCharacterMovement()->IsMovingOnGround()&&Survivor->Health>0&&!Survivor->bSleeping)ApplyWornWear(Distance*.00002f);}
        LastWearLocation=Location;bHasWearLocation=true;
    }
    if (Survivor && Mode && Economy && Survivor->GetController())
    {
        Economy->RefreshAccount(this, Mode->GetPersistentPlayerId(Survivor->GetController()));
        int64 Cash=0;for(const auto& Stack:Stacks)Cash+=Economy->GetDenomination(Stack.ItemId)*Stack.Count;
        if(CashBalanceCents!=Cash){CashBalanceCents=Cash;GetOwner()->ForceNetUpdate();OnInventoryUpdated.Broadcast();}
    }
}
void UAnomaliaInventoryComponent::RequestBankOperation(EAnomaliaBankAction Action, FName NoteId, const FString& RecipientId, int64 AmountCents)
{
    if (!GetOwner()) return;
    if (GetOwner()->HasAuthority()) ServerBankOperation_Implementation(Action, NoteId, RecipientId, AmountCents, NextBankSequence);
    else ServerBankOperation(Action, NoteId, RecipientId, AmountCents, NextBankSequence);
}
void UAnomaliaInventoryComponent::ServerBankOperation_Implementation(EAnomaliaBankAction Action, FName NoteId, const FString& RecipientId, int64 AmountCents, int64 Sequence)
{
    const auto* Survivor = Cast<AAnomaliaSurvivor>(GetOwner());
    const auto* Mode = GetWorld() ? GetWorld()->GetAuthGameMode<AAnomaliaGameMode>() : nullptr;
    auto* Economy = GetWorld() ? GetWorld()->GetSubsystem<UAnomaliaEconomySubsystem>() : nullptr;
    if (!GetOwner() || !GetOwner()->HasAuthority() || !Survivor || !Mode || !Economy || !Survivor->GetController() || RecipientId.Len() > 64) return;
    const double RequestTime = GetWorld()->GetRealTimeSeconds();
    if (RequestTime < NextBankRequestTime) return;
    NextBankRequestTime = RequestTime + .2;
    FString Error;
    const bool Accepted = Economy->Execute(this, Mode->GetPersistentPlayerId(Survivor->GetController()), Action, NoteId, RecipientId, AmountCents, Sequence, Error);
    BankMessage = Accepted ? (IsPersistenceLocked() ? TEXT("Transaction enregistrée ; reprise en cours.") : TEXT("Transaction enregistrée.")) : Error;
    OnInventoryUpdated.Broadcast(); GetOwner()->ForceNetUpdate();
}



FName UAnomaliaInventoryComponent::WornContainerId(FName MeshSlot)
{
    if(MeshSlot==TEXT("Jacket"))return TEXT("worn_top");
    if(MeshSlot==TEXT("Pants"))return TEXT("worn_legs");
    if(MeshSlot==TEXT("Backpack"))return TEXT("worn_back");
    if(MeshSlot==TEXT("Vest"))return TEXT("worn_vest");
    if(MeshSlot==TEXT("Headgear"))return TEXT("worn_head");
    if(MeshSlot==TEXT("Gloves"))return TEXT("worn_gloves");
    if(MeshSlot==TEXT("Boots"))return TEXT("worn_feet");
    return NAME_None;
}

bool UAnomaliaInventoryComponent::CanRemoveWornStorage(FName MeshSlot) const
{
    const FName Id=WornContainerId(MeshSlot);
    return !IsPersistenceLocked()&&!Id.IsNone()&&!Stacks.ContainsByPredicate([&](const auto& S){
        const auto* Rule=FindAttachmentRule(S.ContainerId);
        if(S.ContainerId==Id || (Rule&&Rule->Parent==Id))return true;
        if(Rule){const auto* Parent=FindAttachmentRule(Rule->Parent);return Parent&&Parent->Parent==Id;}
        return false;
    });
}

void UAnomaliaInventoryComponent::SynchronizeWornStorage()
{
    auto* Survivor=Cast<AAnomaliaSurvivor>(GetOwner());
    if(!Survivor||!Survivor->HasAuthority()||!GetWorld()||!GetWorld()->IsGameWorld()||IsPersistenceLocked()||bSuppressNotifications)return;
    struct FWornRow{FName Slot;USkeletalMeshComponent* Mesh;FName Preset;FIntPoint Fallback;};
    const FWornRow Rows[]={
        {TEXT("Jacket"),Survivor->JacketMesh,TEXT("jacket_light"),{1,1}},
        {TEXT("Pants"),Survivor->PantsMesh,TEXT("pants"),{1,1}},
        {TEXT("Backpack"),Survivor->BackpackMesh,TEXT("backpack_small"),{1,1}},
        {TEXT("Vest"),Survivor->VestMesh,TEXT("vest_tactical"),{1,1}},
        {TEXT("Headgear"),Survivor->HeadgearMesh,NAME_None,{2,1}},
        {TEXT("Gloves"),Survivor->GlovesMesh,NAME_None,{2,1}},
        {TEXT("Boots"),Survivor->BootsMesh,NAME_None,{2,2}}
    };
    bool Changed=false;
    for(const auto& Row:Rows)
    {
        const FName Id=WornContainerId(Row.Slot);
        auto* Box=Compartments.FindByPredicate([&](const auto& B){return B.Id==Id;});
        const bool Worn=Row.Mesh&&Row.Mesh->GetSkeletalMeshAsset();
        if(Worn)
        {
            FIntPoint Grid=Row.Fallback;if(!Row.Preset.IsNone()&&!UAnomaliaStorageCatalog::GetGrid(Row.Preset,Grid))continue;
            if(!Box){if(Compartments.Num()>=128)continue;Box=&Compartments.AddDefaulted_GetRef();Box->Id=Id;Box->Width=Grid.X;Box->Height=Grid.Y;Changed=true;}
            if(Box->Width<Grid.X||Box->Height<Grid.Y){Box->Width=FMath::Max(Box->Width,Grid.X);Box->Height=FMath::Max(Box->Height,Grid.Y);Changed=true;}
            if(Box->bRecoveryOnly){Box->bRecoveryOnly=false;Changed=true;}
        }
        else if(Box)
        {
            if(Box->Condition<100.f||Stacks.ContainsByPredicate([&](const auto& S){return S.ContainerId==Id;}))
            {if(!Box->bRecoveryOnly){Box->bRecoveryOnly=true;Changed=true;}}
            else{Compartments.RemoveAll([&](const auto& B){return B.Id==Id;});Changed=true;}
        }
    }
    SynchronizeAttachmentStorage();
    if(Changed){GetOwner()->ForceNetUpdate();OnInventoryChanged();OnInventoryUpdated.Broadcast();}
}

bool UAnomaliaInventoryComponent::StowStackInOnServer(int32 StackId,FName ContainerId)
{
    if(!GetOwner()||!GetOwner()->HasAuthority()||IsPersistenceLocked()||ContainerId==TEXT("hands")||IsRecoveryContainer(ContainerId))return false;
    const auto* Box=Compartments.FindByPredicate([&](const auto& B){return B.Id==ContainerId;});
    const auto* Selected=Stacks.FindByPredicate([&](const auto& S){return S.StackId==StackId;});
    if(!Box||!Selected||HasAttachmentDependents(StackId))return false;
    if(FindAttachmentRule(ContainerId))return TryMoveStack(StackId,ContainerId,0,0,false);
    auto Candidate=Stacks;auto* Moving=Candidate.FindByPredicate([&](const auto& S){return S.StackId==StackId;});
    for(bool Rotated:{Moving->bRotated,!Moving->bRotated})
    {
        const auto Size=GetItemSize(Moving->ItemId,Rotated);
        for(int32 Y=0;Y<=Box->Height-Size.Y;++Y)for(int32 X=0;X<=Box->Width-Size.X;++X)
            if(CanPlace(Candidate,*Moving,ContainerId,X,Y,Rotated))
            {Moving->ContainerId=ContainerId;Moving->X=X;Moving->Y=Y;Moving->bRotated=Rotated;Commit(MoveTemp(Candidate));return true;}
    }
    UseMessage=TEXT("Pas de place dans ce rangement.");OnInventoryUpdated.Broadcast();return false;
}
bool UAnomaliaInventoryComponent::RequestStowStackIn(int32 StackId,FName ContainerId)
{
    if(!GetOwner())return false;
    if(GetOwner()->HasAuthority())return StowStackInOnServer(StackId,ContainerId);
    ServerRequestStowStackIn(StackId,ContainerId);return true;
}
void UAnomaliaInventoryComponent::ServerRequestStowStackIn_Implementation(int32 StackId,FName ContainerId)
{StowStackInOnServer(StackId,ContainerId);}

bool UAnomaliaInventoryComponent::RequestCollectNearby(AAnomaliaLootPickup* Pickup)
{
    if(!GetOwner())return false;
    if(GetOwner()->HasAuthority())return CollectNearbyOnServer(Pickup);
    ServerRequestCollectNearby(Pickup);return true;
}
void UAnomaliaInventoryComponent::ServerRequestCollectNearby_Implementation(AAnomaliaLootPickup* Pickup)
{CollectNearbyOnServer(Pickup);}
bool UAnomaliaInventoryComponent::CollectNearbyOnServer(AAnomaliaLootPickup* Pickup)
{
    auto* User=Cast<AAnomaliaSurvivor>(GetOwner());
    auto* World=GetWorld();auto* Mode=World?World->GetAuthGameMode<AAnomaliaGameMode>():nullptr;
    auto* Loot=World?World->GetSubsystem<UAnomaliaLootSubsystem>():nullptr;
    if(!User||!User->HasAuthority()||!Mode||!Loot||!User->GetController()||User->GetController()->GetPawn()!=User)return false;
    const double Now=World->GetRealTimeSeconds();if(Now<NextCollectRequestTime)return false;NextCollectRequestTime=Now+.2;
    FString Error;const bool Accepted=Loot->TryCollect(Pickup,User,Mode->GetPersistentPlayerId(User->GetController()),Error);
    UseMessage=Accepted?TEXT("Objet ramassé."):(Error.IsEmpty()?TEXT("Objet indisponible ou hors de portée."):Error);
    OnInventoryUpdated.Broadcast();User->ForceNetUpdate();return Accepted;
}

const TArray<FAnomaliaHandcraftRecipe>& UAnomaliaInventoryComponent::GetHandcraftRecipes()
{
    static const TArray<FAnomaliaHandcraftRecipe> Recipes={
        {TEXT("cloth_bandage"),TEXT("Pansement en tissu"),TEXT("bandage"),1,{{TEXT("cloth"),2}}},
        {TEXT("rag_rope"),TEXT("Corde en chiffons"),TEXT("rope"),1,{{TEXT("rags"),6}}},
        {TEXT("field_splint"),TEXT("Attelle de fortune"),TEXT("splint"),1,{{TEXT("wood"),2},{TEXT("rags"),4}}},
        // Same resource cost as the original ANOMALIA prototype recipe.
        {TEXT("saddle"),TEXT("Selle"),TEXT("saddle"),1,{{TEXT("fiber"),6},{TEXT("cloth"),4}}}
    };
    return Recipes;
}
bool UAnomaliaInventoryComponent::HasCraftMaterials(FName RecipeId) const
{
    const auto* Recipe=GetHandcraftRecipes().FindByPredicate([&](const auto& R){return R.Id==RecipeId;});
    if(!Recipe||IsPersistenceLocked())return false;
    for(const auto& M:Recipe->Materials)
    {int32 Count=0;for(const auto& S:Stacks)if(S.ItemId==M.Key&&!IsRecoveryContainer(S.ContainerId))Count+=S.Count;if(Count<M.Value)return false;}
    return true;
}
bool UAnomaliaInventoryComponent::TryCraftRecipe(FName RecipeId,const FString& ServerId,const FString& PlayerId,FString& OutError)
{
    OutError.Empty();auto* Survivor=Cast<AAnomaliaSurvivor>(GetOwner());
    const auto* Loot=GetWorld()?GetWorld()->GetSubsystem<UAnomaliaLootSubsystem>():nullptr;
    const auto* Economy=GetWorld()?GetWorld()->GetSubsystem<UAnomaliaEconomySubsystem>():nullptr;
    if(!Survivor||!Survivor->HasAuthority()||Survivor->Health<=0||Survivor->bSleeping||IsPersistenceLocked()||bSuppressNotifications||
       (Loot&&Loot->HasPendingPlayer(PlayerId))||(Economy&&Economy->HasPendingPlayer(PlayerId)))
    {OutError=TEXT("Fabrication indisponible pendant la récupération, une sauvegarde ou le sommeil.");return false;}
    const auto* Recipe=GetHandcraftRecipes().FindByPredicate([&](const auto& R){return R.Id==RecipeId;});
    if(!Recipe||!HasCraftMaterials(RecipeId)){OutError=TEXT("Plan inconnu ou matériaux insuffisants.");return false;}
    const auto Before=Stacks;const int32 BeforeId=NextStackId;auto Candidate=Stacks;
    for(const auto& M:Recipe->Materials)
    {int32 Remaining=M.Value;for(int32 I=Candidate.Num()-1;I>=0&&Remaining>0;--I){auto& S=Candidate[I];if(S.ItemId!=M.Key||IsRecoveryContainer(S.ContainerId))continue;const int32 Taken=FMath::Min(Remaining,S.Count);S.Count-=Taken;Remaining-=Taken;}}
    Candidate.RemoveAll([](const auto& S){return S.Count<=0;});
    Stacks=MoveTemp(Candidate);bSuppressNotifications=true;
    auto Rollback=[&](){Stacks=Before;NextStackId=BeforeId;bSuppressNotifications=false;};
    if(!TryAddItem(Recipe->Output,Recipe->OutputCount)){Rollback();OutError=TEXT("Poids ou espace insuffisant : matériaux conservés.");return false;}
    FString Raw;
    if(!BuildInventoryProfile(ServerId,PlayerId,Raw,OutError)){Rollback();return false;}
    auto After=Stacks;const int32 AfterId=NextStackId;Rollback();
    if(!UAnomaliaConfigLibrary::SavePlayerProfile(ServerId,PlayerId,Raw,OutError))return false;
    NextStackId=AfterId;UseMessage=TEXT("Fabriqué : ")+Recipe->Label;Commit(MoveTemp(After));return true;
}
bool UAnomaliaInventoryComponent::CraftFromOwningPlayer(FName RecipeId)
{
    const auto* Survivor=Cast<AAnomaliaSurvivor>(GetOwner());
    const auto* Mode=GetWorld()?GetWorld()->GetAuthGameMode<AAnomaliaGameMode>():nullptr;
    if(!Survivor||!Survivor->HasAuthority()||!Mode||!Survivor->GetController()||Survivor->GetController()->GetPawn()!=Survivor)return false;
    const double Now=GetWorld()->GetRealTimeSeconds();if(Now<NextCraftRequestTime)return false;NextCraftRequestTime=Now+.25;
    FString Error;const bool Accepted=TryCraftRecipe(RecipeId,Mode->ServerId,Mode->GetPersistentPlayerId(Survivor->GetController()),Error);
    if(!Accepted){UseMessage=Error;OnInventoryUpdated.Broadcast();GetOwner()->ForceNetUpdate();}return Accepted;
}
bool UAnomaliaInventoryComponent::RequestCraftRecipe(FName RecipeId)
{
    if(!GetOwner())return false;if(GetOwner()->HasAuthority())return CraftFromOwningPlayer(RecipeId);
    ServerRequestCraftRecipe(RecipeId);return true;
}
void UAnomaliaInventoryComponent::ServerRequestCraftRecipe_Implementation(FName RecipeId)
{CraftFromOwningPlayer(RecipeId);}



bool UAnomaliaInventoryComponent::SupportsItemWear(FName Id) const
{
    static const TSet<FName> Legacy={TEXT("tactical_belt"),TEXT("medical_pouch"),TEXT("handcuffs"),TEXT("pistol_holster"),TEXT("knife_sheath"),TEXT("rifle"),TEXT("pistol"),TEXT("shotgun"),TEXT("knife"),TEXT("hunting_knife"),TEXT("combat_knife"),TEXT("machete"),TEXT("hatchet"),TEXT("jacket"),TEXT("coat"),TEXT("shirt"),TEXT("pants"),TEXT("jeans"),TEXT("boots"),TEXT("gloves"),TEXT("helmet"),TEXT("vest"),TEXT("backpack"),TEXT("bag")};
    if(Legacy.Contains(Id))return true;
    const auto* Loot=GetWorld()?GetWorld()->GetSubsystem<UAnomaliaLootSubsystem>():nullptr;
    const auto* Item=Loot?Loot->FindItem(Id):nullptr;if(!Item)return false;
    for(const TCHAR* Category:{TEXT("assault_weapons"),TEXT("hunting_precision_weapons"),TEXT("handguns_smg_shotguns"),TEXT("tops"),TEXT("pants"),TEXT("shoes_gloves"),TEXT("headwear"),TEXT("backpacks"),TEXT("vests")})
        if(Item->Categories.Contains(FString(Category)))return true;
    return false;
}
bool UAnomaliaInventoryComponent::ApplyItemWear(int32 StackId,float Wear)
{
    if(!GetOwner()||!GetOwner()->HasAuthority()||IsPersistenceLocked()||bSuppressNotifications||!FMath::IsFinite(Wear)||Wear<=0||Wear>100)return false;
    const auto* Existing=Stacks.FindByPredicate([&](const auto& S){return S.StackId==StackId;});
    if(!Existing||Existing->Count!=1||!SupportsItemWear(Existing->ItemId))return false;
    auto Candidate=Stacks;auto* Item=Candidate.FindByPredicate([&](const auto& S){return S.StackId==StackId;});
    Item->Condition=FMath::Max(0.f,Item->Condition-Wear);Commit(MoveTemp(Candidate));return true;
}
bool UAnomaliaInventoryComponent::ApplyWornWear(float Wear)
{
    auto* User=Cast<AAnomaliaSurvivor>(GetOwner());
    if(!User||!User->HasAuthority()||IsPersistenceLocked()||bSuppressNotifications||!FMath::IsFinite(Wear)||Wear<=0||Wear>100)return false;
    struct FPart{FName Slot;USkeletalMeshComponent* Mesh;};
    const FPart Parts[]={{TEXT("Jacket"),User->JacketMesh},{TEXT("Pants"),User->PantsMesh},{TEXT("Backpack"),User->BackpackMesh},{TEXT("Vest"),User->VestMesh},{TEXT("Headgear"),User->HeadgearMesh},{TEXT("Gloves"),User->GlovesMesh},{TEXT("Boots"),User->BootsMesh}};
    bool Changed=false;
    for(const auto& Part:Parts)
    {
        if(!Part.Mesh||!Part.Mesh->GetSkeletalMeshAsset())continue;
        const FName Id=WornContainerId(Part.Slot);auto* Box=Compartments.FindByPredicate([&](const auto& B){return B.Id==Id;});
        if(!Box||Box->bRecoveryOnly||Box->Condition<=0)continue;
        Box->Condition=FMath::Max(0.f,Box->Condition-Wear);Changed=true;
    }
    if(Changed){OnInventoryChanged();OnInventoryUpdated.Broadcast();User->ForceNetUpdate();}
    return Changed;
}


const TArray<FAnomaliaAttachmentRule>& UAnomaliaInventoryComponent::GetAttachmentRules()
{
    static const TArray<FAnomaliaAttachmentRule> Rules={
        {TEXT("mount_belt"),NAME_None,TEXT("Ceinture"),{TEXT("tactical_belt")}},
        {TEXT("mount_belt_holster"),TEXT("mount_belt"),TEXT("Holster"),{TEXT("pistol_holster")}},
        {TEXT("mount_belt_pistol"),TEXT("mount_belt_holster"),TEXT("Pistolet"),{TEXT("pistol"),TEXT("mlock91"),TEXT("kolt1911"),TEXT("fx45"),TEXT("ij70"),TEXT("cr75"),TEXT("deagle"),TEXT("p1"),TEXT("derringer"),TEXT("amphibias")}},
        {TEXT("mount_belt_sheath"),TEXT("mount_belt"),TEXT("Fourreau"),{TEXT("knife_sheath")}},
        {TEXT("mount_belt_knife"),TEXT("mount_belt_sheath"),TEXT("Couteau"),{TEXT("hunting_knife"),TEXT("kitchen_knife"),TEXT("bone_knife")}},
        {TEXT("mount_belt_water"),TEXT("mount_belt"),TEXT("Gourde"),{TEXT("military_canteen"),TEXT("empty_military_canteen"),TEXT("filter_canteen"),TEXT("empty_filter_canteen")}},
        {TEXT("mount_belt_medical"),TEXT("mount_belt"),TEXT("Sacoche médicale"),{TEXT("medical_pouch")}},
        {TEXT("mount_belt_mag1"),TEXT("mount_belt"),TEXT("Chargeur 1"),{TEXT("stanag_magazine"),TEXT("ak_magazine")}},
        {TEXT("mount_belt_mag2"),TEXT("mount_belt"),TEXT("Chargeur 2"),{TEXT("stanag_magazine"),TEXT("ak_magazine")}},
        {TEXT("mount_belt_cuffs"),TEXT("mount_belt"),TEXT("Menottes"),{TEXT("handcuffs")}},
        {TEXT("mount_back_weapon"),TEXT("worn_back"),TEXT("Arme latérale"),{TEXT("rifle"),TEXT("akm"),TEXT("m4a1"),TEXT("mosin_9130"),TEXT("bk133"),TEXT("ak74"),TEXT("aks74u"),TEXT("fal_lar"),TEXT("ka101"),TEXT("m16a2"),TEXT("aug_a1"),TEXT("aug_ax"),TEXT("famas")}},
        {TEXT("mount_back_sleep"),TEXT("worn_back"),TEXT("Sac de couchage"),{TEXT("sleeping_bag")}},
        {TEXT("mount_back_water"),TEXT("worn_back"),TEXT("Bouteille / gourde"),{TEXT("water_bottle"),TEXT("empty_water_bottle"),TEXT("dirty_water_bottle"),TEXT("military_canteen"),TEXT("empty_military_canteen"),TEXT("filter_canteen"),TEXT("empty_filter_canteen")}},
        {TEXT("mount_back_medical"),TEXT("worn_back"),TEXT("Sacoche médicale"),{TEXT("medical_pouch")}},
        {TEXT("mount_back_radio"),TEXT("worn_back"),TEXT("Radio"),{TEXT("handheld_radio")}},
        {TEXT("mount_back_light"),TEXT("worn_back"),TEXT("Bâton lumineux"),{TEXT("chemlight")}},
        {TEXT("mount_vest_medical"),TEXT("worn_vest"),TEXT("Sacoche médicale"),{TEXT("medical_pouch")}},
        {TEXT("mount_vest_mag_left"),TEXT("worn_vest"),TEXT("Chargeur gauche"),{TEXT("stanag_magazine"),TEXT("ak_magazine")}},
        {TEXT("mount_vest_mag_right"),TEXT("worn_vest"),TEXT("Chargeur droit"),{TEXT("stanag_magazine"),TEXT("ak_magazine")}},
        {TEXT("mount_vest_grenade1"),TEXT("worn_vest"),TEXT("Grenade 1"),{TEXT("frag_grenade"),TEXT("smoke_grenade")}},
        {TEXT("mount_vest_grenade2"),TEXT("worn_vest"),TEXT("Grenade 2"),{TEXT("frag_grenade"),TEXT("smoke_grenade")}},
        {TEXT("mount_vest_holster"),TEXT("worn_vest"),TEXT("Holster"),{TEXT("pistol_holster")}},
        {TEXT("mount_vest_pistol"),TEXT("mount_vest_holster"),TEXT("Pistolet"),{TEXT("pistol"),TEXT("mlock91"),TEXT("kolt1911"),TEXT("fx45"),TEXT("ij70"),TEXT("cr75"),TEXT("deagle"),TEXT("p1"),TEXT("derringer"),TEXT("amphibias")}}
    };
    return Rules;
}
const FAnomaliaAttachmentRule* UAnomaliaInventoryComponent::FindAttachmentRule(FName Id)
{return GetAttachmentRules().FindByPredicate([&](const auto& Rule){return Rule.Id==Id;});}
bool UAnomaliaInventoryComponent::AttachmentAvailable(const TArray<FAnomaliaInventoryStack>& Candidate,FName Id) const
{
    const auto* Rule=FindAttachmentRule(Id);if(!Rule)return false;
    const auto* User=Cast<AAnomaliaSurvivor>(GetOwner());if(!User)return false;
    if(Rule->Parent.IsNone())return true;
    if(Rule->Parent==TEXT("worn_back"))return User->BackpackMesh&&User->BackpackMesh->GetSkeletalMeshAsset();
    if(Rule->Parent==TEXT("worn_vest"))return User->VestMesh&&User->VestMesh->GetSkeletalMeshAsset();
    const auto* Parent=FindAttachmentRule(Rule->Parent);
    return Parent&&AttachmentAvailable(Candidate,Parent->Id)&&Candidate.ContainsByPredicate([&](const auto& S){return S.ContainerId==Parent->Id&&S.Count==1&&Parent->Items.Contains(S.ItemId);});
}
bool UAnomaliaInventoryComponent::IsAttachmentAvailable(FName Id) const
{return AttachmentAvailable(Stacks,Id);}
bool UAnomaliaInventoryComponent::CanAttachStack(int32 StackId,FName SlotId) const
{
    const auto* Stack=Stacks.FindByPredicate([&](const auto& S){return S.StackId==StackId;});
    return FindAttachmentRule(SlotId)&&Stack&&!HasAttachmentDependents(StackId)&&CanPlace(Stacks,*Stack,SlotId,0,0,false);
}
bool UAnomaliaInventoryComponent::HasAttachmentDependents(int32 StackId) const
{
    const auto* Stack=Stacks.FindByPredicate([&](const auto& S){return S.StackId==StackId;});
    if(!Stack||!FindAttachmentRule(Stack->ContainerId))return false;
    const FName Cargo(*(Stack->ContainerId.ToString()+TEXT("_cargo")));
    return Stacks.ContainsByPredicate([&](const auto& Other){
        const auto* Rule=FindAttachmentRule(Other.ContainerId);
        return Other.ContainerId==Cargo||(Rule&&Rule->Parent==Stack->ContainerId);
    });
}
void UAnomaliaInventoryComponent::SynchronizeAttachmentStorage()
{
    if(!GetOwner()||!GetOwner()->HasAuthority()||!Cast<AAnomaliaSurvivor>(GetOwner())||IsPersistenceLocked()||bSuppressNotifications)return;
    bool Changed=false;
    auto Sync=[&](FName Id,int32 W,int32 H,bool Available){
        auto* Box=Compartments.FindByPredicate([&](const auto& B){return B.Id==Id;});
        const bool Occupied=Stacks.ContainsByPredicate([&](const auto& S){return S.ContainerId==Id;});
        if(!Available&&!Occupied){if(Box){Compartments.RemoveAll([&](const auto& B){return B.Id==Id;});Changed=true;}return;}
        if(!Box){if(Compartments.Num()>=128)return;Box=&Compartments.AddDefaulted_GetRef();Box->Id=Id;Box->Width=W;Box->Height=H;Changed=true;}
        if(Box->bRecoveryOnly==Available){Box->bRecoveryOnly=!Available;Changed=true;}
    };
    for(const auto& Rule:GetAttachmentRules())
    {
        Sync(Rule.Id,16,16,AttachmentAvailable(Stacks,Rule.Id));
        if(Rule.Items.Contains(TEXT("medical_pouch")))
        {
            const bool Equipped=AttachmentAvailable(Stacks,Rule.Id)&&Stacks.ContainsByPredicate([&](const auto& S){return S.ContainerId==Rule.Id&&S.ItemId==TEXT("medical_pouch")&&S.Count==1;});
            Sync(FName(*(Rule.Id.ToString()+TEXT("_cargo"))),4,3,Equipped);
        }
    }
    if(Changed)GetOwner()->ForceNetUpdate();
}

void UAnomaliaInventoryComponent::RefreshAttachmentVisuals()
{
    auto* User=Cast<AAnomaliaSurvivor>(GetOwner());
    if(!User||!GetWorld()||!GetWorld()->IsGameWorld()||GetWorld()->GetNetMode()==NM_DedicatedServer)return;
    TSet<int32> Wanted;
    for(const auto& Stack:Stacks)
    {
        // Only this exact local mesh has been validated. Other items never borrow an unrelated model.
        if(Stack.ContainerId!=TEXT("mount_back_weapon")||Stack.ItemId!=TEXT("rifle")||!IsAttachmentAvailable(Stack.ContainerId))continue;
        auto* Parent=User->BackpackMesh.Get();if(!Parent)continue;
        FName Bone=NAME_None;for(const FName Candidate:{FName(TEXT("spine_03")),FName(TEXT("spine_02")),FName(TEXT("spine"))})
            if(Parent->DoesSocketExist(Candidate)){Bone=Candidate;break;}
        if(Bone.IsNone())continue;
        Wanted.Add(Stack.StackId);
        if(AttachmentVisuals.Contains(Stack.StackId))continue;
        auto* Mesh=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/QuantumCharacter/Mesh/Rifle/SM_Rifle_Olive.SM_Rifle_Olive"));if(!Mesh)continue;
        auto* Part=NewObject<UStaticMeshComponent>(User);User->AddInstanceComponent(Part);
        Part->SetStaticMesh(Mesh);Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);Part->SetGenerateOverlapEvents(false);
        Part->SetCanEverAffectNavigation(false);Part->RegisterComponent();Part->AttachToComponent(Parent,FAttachmentTransformRules::SnapToTargetNotIncludingScale,Bone);
        const auto Bounds=Mesh->GetBounds();const FVector Extent=Bounds.BoxExtent;
        const FVector LongAxis=Extent.X>=Extent.Y&&Extent.X>=Extent.Z?FVector::ForwardVector:Extent.Y>=Extent.Z?FVector::RightVector:FVector::UpVector;
        const FVector ThinAxis=Extent.X<=Extent.Y&&Extent.X<=Extent.Z?FVector::ForwardVector:Extent.Y<=Extent.Z?FVector::RightVector:FVector::UpVector;
        const float LongSize=FMath::Max3(Extent.X,Extent.Y,Extent.Z)*2.f;
        const float Scale=LongSize>1.f?110.f/LongSize:1.f;
        const FQuat Upright=FQuat::FindBetweenNormals(LongAxis,FVector::UpVector);
        const FVector Normal=Upright.RotateVector(ThinAxis),Forward=User->GetActorForwardVector();
        const float Twist=FMath::Atan2(Forward.Y,Forward.X)-FMath::Atan2(Normal.Y,Normal.X);
        const FQuat Rotation=FQuat(FVector::UpVector,Twist)*Upright;
        const FVector Center=User->GetActorLocation()-Forward*28.f+User->GetActorRightVector()*29.f+FVector(0,0,15);
        // Set the actual mesh centre in world space, then retain that transform relative
        // to the animated spine socket. Imported pivots and bone axes may differ.
        Part->SetWorldScale3D(FVector(Scale));Part->SetWorldRotation(Rotation);
        Part->SetWorldLocation(Center-Rotation.RotateVector(Bounds.Origin*Scale));
        AttachmentVisuals.Add(Stack.StackId,Part);
    }
    TArray<int32> Remove;for(const auto& Pair:AttachmentVisuals)if(!Wanted.Contains(Pair.Key))Remove.Add(Pair.Key);
    for(const int32 Id:Remove){if(auto* Part=AttachmentVisuals.FindRef(Id).Get())Part->DestroyComponent();AttachmentVisuals.Remove(Id);}
}
