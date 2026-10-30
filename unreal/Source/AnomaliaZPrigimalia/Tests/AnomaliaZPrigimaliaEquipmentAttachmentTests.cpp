#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "../AnomaliaZPrigimaliaSurvivor.h"
#include "../AnomaliaZPrigimaliaInventoryComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "Dom/JsonObject.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaZPrigimaliaEquipmentAttachmentsTest,"AnomaliaZPrigimalia.Native.EquipmentAttachments",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FAnomaliaZPrigimaliaEquipmentAttachmentsTest::RunTest(const FString& Parameters)
{
    auto* World=UWorld::CreateWorld(EWorldType::Game,false);
    if(!TestNotNull(TEXT("Isolated authority world"),World))return false;
    auto* User=World->SpawnActor<AAnomaliaZPrigimaliaSurvivor>();auto* Inv=User->InventoryComponent.Get();
    Inv->WeightCapacityKg=100;Inv->ConfigureCompartment(TEXT("fixture_cargo"),20,20);Inv->SynchronizeAttachmentStorage();
    auto Id=[&](FName Item){const auto* S=Inv->Stacks.FindByPredicate([&](const auto& X){return X.ItemId==Item;});return S?S->StackId:0;};
    TestTrue(TEXT("Physical belt acquired"),Inv->TryAddItem(TEXT("tactical_belt"),1));
    TestTrue(TEXT("Medical pouch acquired"),Inv->TryAddItem(TEXT("medical_pouch"),1));
    TestFalse(TEXT("Belt attachments unavailable before belt equipped"),Inv->TryMoveStack(Id(TEXT("medical_pouch")),TEXT("mount_belt_medical"),0,0,false));
    TestTrue(TEXT("Equip physical belt"),Inv->TryMoveStack(Id(TEXT("tactical_belt")),TEXT("mount_belt"),0,0,false));
    TestTrue(TEXT("Attach medical pouch"),Inv->TryMoveStack(Id(TEXT("medical_pouch")),TEXT("mount_belt_medical"),0,0,false));
    TestTrue(TEXT("Actual bandage acquired"),Inv->TryAddItem(TEXT("bandage"),1));
    TestTrue(TEXT("Bandage fits pouch cargo"),Inv->TryMoveStack(Id(TEXT("bandage")),TEXT("mount_belt_medical_cargo"),0,0,false));
    TestFalse(TEXT("Full pouch cannot disappear through move"),Inv->TryMoveStack(Id(TEXT("medical_pouch")),TEXT("hands"),0,0,false));
    TestFalse(TEXT("Full pouch cannot disappear through removal"),Inv->TryRemoveItem(TEXT("medical_pouch"),1));
    TestFalse(TEXT("Occupied belt cannot be removed"),Inv->TryMoveStack(Id(TEXT("tactical_belt")),TEXT("hands"),0,0,false));
    TestTrue(TEXT("Two actual magazines acquired"),Inv->TryAddItem(TEXT("stanag_magazine"),2));
    int32 Second=0;const int32 First=Id(TEXT("stanag_magazine"));
    TestFalse(TEXT("A pile cannot occupy one attachment slot"),Inv->TryMoveStack(First,TEXT("mount_belt_mag1"),0,0,false));
    TestTrue(TEXT("Separate magazine instances"),Inv->TrySplitStack(First,1,Second));
    TestTrue(TEXT("First magazine attached"),Inv->TryMoveStack(First,TEXT("mount_belt_mag1"),0,0,false));
    TestFalse(TEXT("Occupied slot rejects second magazine"),Inv->TryMoveStack(Second,TEXT("mount_belt_mag1"),0,0,false));
    TestTrue(TEXT("Second magazine has independent slot"),Inv->TryMoveStack(Second,TEXT("mount_belt_mag2"),0,0,false));
    TestTrue(TEXT("Physical handcuffs acquired"),Inv->TryAddItem(TEXT("handcuffs"),1));
    TestFalse(TEXT("Wrong category rejected"),Inv->TryMoveStack(Id(TEXT("handcuffs")),TEXT("mount_belt_water"),0,0,false));
    TestTrue(TEXT("Handcuffs attached"),Inv->TryMoveStack(Id(TEXT("handcuffs")),TEXT("mount_belt_cuffs"),0,0,false));
    TestFalse(TEXT("Client-shaped oversized attachment compartment rejected"),Inv->ConfigureCompartment(TEXT("mount_belt_mag1"),100,100));
    auto Snapshot=Inv->ExportInventoryObject();FString Error;
    auto* Restored=World->SpawnActor<AAnomaliaZPrigimaliaSurvivor>();
    TestTrue(TEXT("Nested equipment reloads"),Restored->InventoryComponent->LoadInventoryObject(Snapshot,Error));
    TestEqual(TEXT("No objects lost or duplicated"),Restored->InventoryComponent->Stacks.Num(),Inv->Stacks.Num());
    TestTrue(TEXT("Nested full pouch remains protected after reload"),Restored->InventoryComponent->HasAttachmentDependents(Id(TEXT("medical_pouch"))));
    TestTrue(TEXT("Bandage recovered through hands"),Inv->TryMoveStack(Id(TEXT("bandage")),TEXT("hands"),0,0,false));
    TestTrue(TEXT("Empty pouch can be stowed"),Inv->RequestStowStackIn(Id(TEXT("medical_pouch")),TEXT("fixture_cargo")));
    TestTrue(TEXT("Rifle acquired"),Inv->TryAddItem(TEXT("rifle"),1));
    TestFalse(TEXT("Cannot attach weapon without actual backpack mesh"),Inv->TryMoveStack(Id(TEXT("rifle")),TEXT("mount_back_weapon"),0,0,false));
    // Empty transient mesh is a server-rule fixture, never a playable character or shipped asset.
    User->BackpackMesh->SetSkeletalMesh(NewObject<USkeletalMesh>(User));Inv->SynchronizeAttachmentStorage();
    TestTrue(TEXT("Backpack grants its weapon attachment"),Inv->TryMoveStack(Id(TEXT("rifle")),TEXT("mount_back_weapon"),0,0,false));
    TestFalse(TEXT("Backpack with mounted weapon cannot be removed"),Inv->CanRemoveWornStorage(TEXT("Backpack")));
    User->BackpackMesh->SetSkeletalMesh(nullptr);Inv->SynchronizeAttachmentStorage();
    TestTrue(TEXT("Missing backpack preserves mounted weapon for recovery"),Inv->IsRecoveryContainer(TEXT("mount_back_weapon")));
    TestTrue(TEXT("Preserved mounted weapon remains removable"),Inv->RequestStowStackIn(Id(TEXT("rifle")),TEXT("fixture_cargo")));
    Snapshot->GetArrayField(TEXT("compartments"))[0]->AsObject()->SetNumberField(TEXT("width"),0);
    const int32 Before=Restored->InventoryComponent->Stacks.Num();
    TestFalse(TEXT("Corrupt snapshot rejected"),Restored->InventoryComponent->LoadInventoryObject(Snapshot,Error));
    TestEqual(TEXT("Rejected snapshot preserves live contents"),Restored->InventoryComponent->Stacks.Num(),Before);
    World->DestroyWorld(false);return true;
}
#endif
