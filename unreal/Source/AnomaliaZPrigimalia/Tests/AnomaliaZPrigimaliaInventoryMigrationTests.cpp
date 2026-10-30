#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "../AnomaliaZPrigimaliaSurvivor.h"
#include "../AnomaliaZPrigimaliaInventoryComponent.h"
#include "../AnomaliaZPrigimaliaConfigLibrary.h"
#include "Engine/World.h"
#include "Misc/Guid.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "HAL/FileManager.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaZPrigimaliaInventoryMigrationTest,"AnomaliaZPrigimalia.Native.InventoryLayoutMigration",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FAnomaliaZPrigimaliaInventoryMigrationTest::RunTest(const FString& Parameters)
{
    const FString Server=TEXT("mig-")+FGuid::NewGuid().ToString(EGuidFormats::Digits).Left(16);
    auto Root=MakeShared<FJsonObject>();auto Inventory=MakeShared<FJsonObject>();auto Box=MakeShared<FJsonObject>();
    Root->SetStringField(TEXT("extension"),TEXT("preserve-me"));Inventory->SetNumberField(TEXT("schemaVersion"),1);Inventory->SetNumberField(TEXT("weightCapacityKg"),500);
    Box->SetStringField(TEXT("id"),TEXT("pockets"));Box->SetNumberField(TEXT("width"),6);Box->SetNumberField(TEXT("height"),4);
    TArray<TSharedPtr<FJsonValue>> Boxes;Boxes.Add(MakeShared<FJsonValueObject>(Box));
    Inventory->SetArrayField(TEXT("compartments"),Boxes);
    TArray<TSharedPtr<FJsonValue>> Rows;
    for(int32 Index=0;Index<24;++Index)
    {
        auto Row=MakeShared<FJsonObject>();Row->SetNumberField(TEXT("stackId"),Index+1);
        Row->SetStringField(TEXT("itemId"),Index<12?TEXT("canned_beans"):TEXT("canned_peaches"));
        Row->SetNumberField(TEXT("count"),Index<12?20:1);Row->SetStringField(TEXT("containerId"),TEXT("pockets"));
        Row->SetNumberField(TEXT("x"),Index%6);Row->SetNumberField(TEXT("y"),Index/6);Row->SetBoolField(TEXT("rotated"),false);
        Rows.Add(MakeShared<FJsonValueObject>(Row));
    }
    Inventory->SetArrayField(TEXT("stacks"),Rows);Root->SetObjectField(TEXT("inventory"),Inventory);
    FString Raw,Error;FJsonSerializer::Serialize(Root,TJsonWriterFactory<>::Create(&Raw));
    TestTrue(TEXT("Seed real legacy profile"),UAnomaliaZPrigimaliaConfigLibrary::SavePlayerProfile(Server,TEXT("old"),Raw,Error));
    auto* World=UWorld::CreateWorld(EWorldType::Game,false);
    if(!TestNotNull(TEXT("Migration test world"),World)) return false;
    auto* Survivor=World->SpawnActor<AAnomaliaZPrigimaliaSurvivor>();auto* Items=Survivor->InventoryComponent.Get();
    TestTrue(TEXT("Changed footprints migrate without losing old stacks"),Items->LoadInventoryFromPlayerProfile(Server,TEXT("old"),Error));
    TestEqual(TEXT("Every legacy stack survives"),Items->Stacks.Num(),24);
    auto Units=[Items](){int32 Count=0;for(const auto& S:Items->Stacks) Count+=S.Count;return Count;};
    TestEqual(TEXT("No quantities lost or duplicated during repacking"),Units(),252);
    const auto* Recovery=Items->Compartments.FindByPredicate([](const auto& C){return C.bRecoveryOnly;});
    if(TestNotNull(TEXT("Oversized legacy contents have withdrawal-only recovery storage"),Recovery))
    {
        const FName RecoveryId=Recovery->Id;
        TestFalse(TEXT("Fresh items cannot merge into withdrawal-only recovery"),Items->TryAddItem(TEXT("canned_peaches"),1));
        TestFalse(TEXT("Manual movement cannot add to recovery storage"),Items->TryMoveStack(1,RecoveryId,50,50,false));
        TestTrue(TEXT("A preserved item can leave recovery through hands"),Items->TryMoveStack(13,TEXT("hands"),0,0,false));
    }
    FString OriginalOnDisk;TestTrue(TEXT("Legacy profile remains readable"),UAnomaliaZPrigimaliaConfigLibrary::LoadPlayerProfile(Server,TEXT("old"),OriginalOnDisk,Error));
    TestEqual(TEXT("Loading alone preserves the original file"),OriginalOnDisk,Raw);
    TArray<FString> Backups;IFileManager::Get().FindFilesRecursive(Backups,*FPaths::Combine(FPaths::ProjectSavedDir(),TEXT("Servers"),Server,TEXT("ib")),TEXT("*.json"),true,false);
    TestEqual(TEXT("Immutable pre-migration backup exists"),Backups.Num(),1);
    if(Backups.Num()==1) { FString Backup;FFileHelper::LoadFileToString(Backup,*Backups[0]);TestEqual(TEXT("Backup matches exact original profile"),Backup,Raw); }
    Survivor->RestoreSurvival(10,10,100);
    TestTrue(TEXT("Migrated held food remains genuinely usable"),Items->TryUseStack(13,1,Server,TEXT("old"),Error));
    TestEqual(TEXT("One use consumes exactly one preserved unit"),Units(),251);
    auto* Restart=World->SpawnActor<AAnomaliaZPrigimaliaSurvivor>();
    TestTrue(TEXT("New layout and withdrawal-only recovery survive restart"),Restart->InventoryComponent->LoadInventoryFromPlayerProfile(Server,TEXT("old"),Error));
    int32 Restored=0;for(const auto& S:Restart->InventoryComponent->Stacks) Restored+=S.Count;
    TestEqual(TEXT("Restart restores all remaining units exactly once"),Restored,251);
    TestTrue(TEXT("Legacy backup can be requested again without overwriting it"),UAnomaliaZPrigimaliaConfigLibrary::BackupInventoryLayout(Server,TEXT("old"),Raw,Error));
    Rows[1]->AsObject()->SetNumberField(TEXT("x"),0);Rows[1]->AsObject()->SetNumberField(TEXT("y"),0);
    FString Corrupt;FJsonSerializer::Serialize(Root,TJsonWriterFactory<>::Create(&Corrupt));
    TestTrue(TEXT("Seed corrupt legacy geometry in a separate profile"),UAnomaliaZPrigimaliaConfigLibrary::SavePlayerProfile(Server,TEXT("corrupt"),Corrupt,Error));
    TestFalse(TEXT("Migration does not accept pre-existing legacy overlaps"),Items->LoadInventoryFromPlayerProfile(Server,TEXT("corrupt"),Error));
    TestEqual(TEXT("Rejected legacy corruption preserves the live inventory"),Units(),251);

    auto* ShapeOwner=World->SpawnActor<AAnomaliaZPrigimaliaSurvivor>();auto* Shape=ShapeOwner->InventoryComponent.Get();Shape->Compartments.Reset();
    TestTrue(TEXT("Prepare a six-cell grid"),Shape->ConfigureCompartment(TEXT("test"),3,2));
    TestTrue(TEXT("Requested 2x3 shovel rotates into 3x2 space"),Shape->TryAddItem(TEXT("shovel"),1));
    TestEqual(TEXT("Shovel occupies all six adjacent cells"),Shape->GetUsedCells(TEXT("test")),6);
    TestFalse(TEXT("No room remains for a one-cell fruit"),Shape->TryAddItem(TEXT("apple"),1));
    World->DestroyWorld(false);return true;
}
#endif
