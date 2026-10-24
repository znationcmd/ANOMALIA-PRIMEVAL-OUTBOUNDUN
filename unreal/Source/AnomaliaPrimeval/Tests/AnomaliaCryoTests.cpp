#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "../AnomaliaCryoSubsystem.h"
#include "Engine/World.h"
#include "../AnomaliaConfigLibrary.h"
#include "HAL/FileManager.h"
#include "Misc/Guid.h"
#include "Misc/Paths.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include <limits>

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaCryoStorageTest,"Anomalia.Native.CryoStorage",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FAnomaliaCryoStorageTest::RunTest(const FString& Parameters)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    if(!TestNotNull(TEXT("Isolated test world"),World)) return false;
    auto* Storage=NewObject<UAnomaliaCryoSubsystem>(World);
    TestFalse(TEXT("An unscoped world cannot mutate default server data"),Storage->RegisterTerminal(TEXT("unscoped"),TEXT("owner"),FVector::ZeroVector));
    const FString ServerId=TEXT("cryo-test-")+FGuid::NewGuid().ToString(EGuidFormats::Digits);
    TestTrue(TEXT("Isolated persistent scope"),Storage->StartPersistentStorage(ServerId));
    TestFalse(TEXT("Reject infinite position"),Storage->RegisterTerminal(TEXT("invalid"),TEXT("owner"),
        FVector(std::numeric_limits<double>::infinity(),0,0)));
    TestFalse(TEXT("Reject NaN position"),Storage->RegisterTerminal(TEXT("nan"),TEXT("owner"),
        FVector(0,std::numeric_limits<double>::quiet_NaN(),0)));
    TestTrue(TEXT("Register finite terminal"),Storage->RegisterTerminal(TEXT("first"),TEXT("owner"),FVector::ZeroVector));
    TestTrue(TEXT("Register another terminal"),Storage->RegisterTerminal(TEXT("second"),TEXT("owner"),FVector::ZeroVector));
    FAnomaliaCryoCreature Creature;
    Creature.Id=TEXT("creature");Creature.OwnerId=TEXT("owner");Creature.bTamed=true;
    TestFalse(TEXT("Unauthorized player cannot capture"),Storage->CaptureCreature(TEXT("first"),TEXT("intruder"),false,Creature,false,0,false));
    TestTrue(TEXT("Owner captures once"),Storage->CaptureCreature(TEXT("first"),TEXT("owner"),false,Creature,false,0,false));
    TestFalse(TEXT("Prevent duplication across terminals"),Storage->CaptureCreature(TEXT("second"),TEXT("owner"),false,Creature,false,0,false));
    FAnomaliaCryoCreature Released;
    TestFalse(TEXT("Unauthorized player cannot release"),Storage->ReleaseCreature(TEXT("first"),Creature.Id,TEXT("intruder"),false,true,Released));
    TestFalse(TEXT("Failed spawn preserves stored creature"),Storage->ReleaseCreature(TEXT("first"),Creature.Id,TEXT("owner"),false,false,Released));
    TestTrue(TEXT("Validated spawn releases creature"),Storage->ReleaseCreature(TEXT("first"),Creature.Id,TEXT("owner"),false,true,Released));
    TestFalse(TEXT("Released creature is no longer stored"),Released.bStored);
    TestFalse(TEXT("Cannot release twice"),Storage->ReleaseCreature(TEXT("first"),Creature.Id,TEXT("owner"),false,true,Released));
    IFileManager::Get().DeleteDirectory(*FPaths::Combine(FPaths::ProjectSavedDir(),TEXT("Servers"),ServerId),false,true);
    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaCryoPersistenceTest,"Anomalia.Native.CryoMetadataPersistence",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FAnomaliaCryoPersistenceTest::RunTest(const FString& Parameters)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    if(!TestNotNull(TEXT("Isolated persistence world"),World))return false;
    const FString ServerId=TEXT("vault-test-")+FGuid::NewGuid().ToString(EGuidFormats::Digits);
    const FString Directory=FPaths::Combine(FPaths::ProjectSavedDir(),TEXT("Servers"),ServerId);
    const FString File=FPaths::Combine(Directory,TEXT("World"),TEXT("creature-vault-metadata.json"));
    const FString Backup=File+TEXT(".test-backup");
    auto* Store=NewObject<UAnomaliaCryoSubsystem>(World);
    TestTrue(TEXT("Initialize durable metadata"),Store->StartPersistentStorage(ServerId));
    TestTrue(TEXT("Register terminal"),Store->RegisterTerminal(TEXT("terminal"),TEXT("owner"),FVector(10,20,30)));
    TestTrue(TEXT("Configure terminal"),Store->ConfigureTerminal(TEXT("terminal"),TEXT("owner"),false,42,3,false));
    FAnomaliaCryoCreature Creature;
    Creature.Id=TEXT("unique-creature");Creature.OwnerId=TEXT("owner");Creature.Species=TEXT("test-species");Creature.bTamed=true;
    TestTrue(TEXT("Capture metadata durably"),Store->CaptureCreature(TEXT("terminal"),TEXT("owner"),false,Creature,true,20,false));

    // A fresh subsystem restores disk state rather than inheriting an in-memory map.
    auto* Reloaded=NewObject<UAnomaliaCryoSubsystem>(World);
    TestTrue(TEXT("Restore after subsystem restart"),Reloaded->StartPersistentStorage(ServerId));
    FAnomaliaCryoTerminal Terminal;
    TestTrue(TEXT("Restored terminal exists"),Reloaded->GetTerminal(TEXT("terminal"),Terminal));
    TestEqual(TEXT("Stored creature restored"),Terminal.Creatures.Num(),1);
    TestEqual(TEXT("Capacity restored"),Terminal.Capacity,3);
    TestEqual(TEXT("Range restored"),Terminal.Range,42.f);
    TestFalse(TEXT("Hybrid policy restored"),Terminal.bAllowHybrids);
    TestFalse(TEXT("Restored uniqueness index prevents recapture"),Reloaded->CaptureCreature(TEXT("terminal"),TEXT("owner"),false,Creature,false,0,false));

    // Block the target file using a directory. No permissions or global paths are changed.
    const bool bMoved=IFileManager::Get().Move(*Backup,*File,true,true);
    TestTrue(TEXT("Preserve existing test save"),bMoved);
    if(bMoved)
    {
        TestTrue(TEXT("Create deterministic write obstruction"),IFileManager::Get().MakeDirectory(*File));
        FAnomaliaCryoCreature Out;
        Out.Id=TEXT("unchanged-output");
        TestFalse(TEXT("Failed durable release reports failure"),Reloaded->ReleaseCreature(TEXT("terminal"),Creature.Id,TEXT("owner"),false,true,Out));
        TestEqual(TEXT("Failed release leaves output untouched"),Out.Id,FString(TEXT("unchanged-output")));
        TestFalse(TEXT("Failed durable config reports failure"),Reloaded->ConfigureTerminal(TEXT("terminal"),TEXT("owner"),false,80,9,true));
        auto Other=Creature;Other.Id=TEXT("other-creature");
        TestFalse(TEXT("Failed durable capture reports failure"),Reloaded->CaptureCreature(TEXT("terminal"),TEXT("owner"),false,Other,false,0,false));
        Reloaded->GetTerminal(TEXT("terminal"),Terminal);
        TestEqual(TEXT("Failed operations preserve creature"),Terminal.Creatures.Num(),1);
        TestEqual(TEXT("Failed config rolls back"),Terminal.Capacity,3);
        IFileManager::Get().DeleteDirectory(*File);
        TestTrue(TEXT("Restore preserved test save"),IFileManager::Get().Move(*File,*Backup,true,true));
        TestTrue(TEXT("Rolled-back uniqueness index permits retry"),Reloaded->CaptureCreature(TEXT("terminal"),TEXT("owner"),false,Other,false,0,false));
    }
    FAnomaliaCryoCreature Out;
    TestTrue(TEXT("Durable release succeeds after recovery"),Reloaded->ReleaseCreature(TEXT("terminal"),Creature.Id,TEXT("owner"),false,true,Out));
    auto* AfterRelease=NewObject<UAnomaliaCryoSubsystem>(World);
    TestTrue(TEXT("Reload released state"),AfterRelease->StartPersistentStorage(ServerId));
    TestFalse(TEXT("Released metadata cannot be released after restart"),AfterRelease->ReleaseCreature(TEXT("terminal"),Creature.Id,TEXT("owner"),false,true,Out));

    FString Original,Error;
    TestTrue(TEXT("Read snapshot for corruption checks"),UAnomaliaConfigLibrary::LoadWorldState(ServerId,TEXT("creature-vault-metadata"),Original,Error));
    TSharedPtr<FJsonObject> Root;
    FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Original),Root);
    if(TestTrue(TEXT("Snapshot is structured JSON"),Root.IsValid()))
    {
        Root->SetNumberField(TEXT("schemaVersion"),999);
        FString Future;
        FJsonSerializer::Serialize(Root.ToSharedRef(),TJsonWriterFactory<>::Create(&Future));
        TestTrue(TEXT("Store future test version"),UAnomaliaConfigLibrary::SaveWorldState(ServerId,TEXT("creature-vault-metadata"),Future,Error));
        auto* Invalid=NewObject<UAnomaliaCryoSubsystem>(World);
        TestFalse(TEXT("Unsupported version fails closed"),Invalid->StartPersistentStorage(ServerId));
        TestFalse(TEXT("Recovery cannot overwrite corrupt scope"),Invalid->RegisterTerminal(TEXT("replacement"),TEXT("owner"),FVector::ZeroVector));
        FString Preserved;
        UAnomaliaConfigLibrary::LoadWorldState(ServerId,TEXT("creature-vault-metadata"),Preserved,Error);
        TestEqual(TEXT("Unsupported file remains byte-identical"),Preserved,Future);
        Root->SetNumberField(TEXT("schemaVersion"),1);
        auto Values=Root->GetArrayField(TEXT("terminals"));
        if(Values.Num()>0)Values.Add(Values[0]);
        Root->SetArrayField(TEXT("terminals"),Values);
        FString Duplicate;
        FJsonSerializer::Serialize(Root.ToSharedRef(),TJsonWriterFactory<>::Create(&Duplicate));
        UAnomaliaConfigLibrary::SaveWorldState(ServerId,TEXT("creature-vault-metadata"),Duplicate,Error);
        auto* Duplicated=NewObject<UAnomaliaCryoSubsystem>(World);
        TestFalse(TEXT("Duplicate terminal IDs rejected on load"),Duplicated->StartPersistentStorage(ServerId));
    }
    IFileManager::Get().DeleteDirectory(*Directory,false,true);
    World->DestroyWorld(false);
    return true;
}
#endif

