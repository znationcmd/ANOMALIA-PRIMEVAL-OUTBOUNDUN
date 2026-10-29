#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "../AnomaliaSurvivor.h"
#include "../AnomaliaInventoryComponent.h"
#include "../AnomaliaConfigLibrary.h"
#include "Engine/World.h"
#include "Misc/Guid.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaSelectedCraftTest,"Anomalia.Native.SelectedCraftTransaction",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FAnomaliaSelectedCraftTest::RunTest(const FString& Parameters)
{
    const FString Server=TEXT("selected-craft-test-")+FGuid::NewGuid().ToString(EGuidFormats::Digits);
    auto* World=UWorld::CreateWorld(EWorldType::Game,false);
    if(!TestNotNull(TEXT("Isolated craft transaction world"),World))return false;
    auto* User=World->SpawnActor<AAnomaliaSurvivor>();
    if(!User){World->DestroyWorld(false);return false;}
    auto* Inventory=User->InventoryComponent.Get();
    Inventory->Compartments.Reset();Inventory->ConfigureCompartment(TEXT("pockets"),10,10);
    if(!TestTrue(TEXT("Seed wood"),Inventory->TryAddItem(TEXT("wood"),2)) ||
       !TestTrue(TEXT("Seed independent rag supply"),Inventory->TryAddItem(TEXT("rags"),8)))
    {World->DestroyWorld(false);return false;}
    const int32 Wood=Inventory->Stacks.FindByPredicate([](const auto& S){return S.ItemId==TEXT("wood");})->StackId;
    auto* RagStack=Inventory->Stacks.FindByPredicate([](const auto& S){return S.ItemId==TEXT("rags")&&S.Count>=4;});
    if(!TestNotNull(TEXT("A selectable four-rag stack"),RagStack)){World->DestroyWorld(false);return false;}
    if(RagStack->Count>4)
    {
        const int32 Split=RagStack->StackId;
        TestTrue(TEXT("Split exact selected ingredients"),Inventory->RequestSplitStack(Split,4));
    }
    RagStack=Inventory->Stacks.FindByPredicate([](const auto& S){return S.ItemId==TEXT("rags")&&S.Count==4;});
    if(!TestNotNull(TEXT("Exactly four selected rags"),RagStack)){World->DestroyWorld(false);return false;}
    const int32 Selected=RagStack->StackId;
    const auto SelectedCopy=*RagStack;
    // Put selected rags before unrelated ones: the old reverse global-material
    // consumption would now spend the wrong physical stack.
    Inventory->Stacks.RemoveAll([&](const auto& S){return S.StackId==Selected;});
    Inventory->Stacks.Insert(SelectedCopy,0);
    TMap<int32,int32> Unselected;
    for(const auto& S:Inventory->Stacks)if(S.ItemId==TEXT("rags")&&S.StackId!=Selected)Unselected.Add(S.StackId,S.Count);
    if(!TestTrue(TEXT("Hold exact wood stack"),Inventory->RequestMoveStack(Wood,TEXT("hands"),0,0,false)))
    {World->DestroyWorld(false);return false;}
    TestFalse(TEXT("A stack cannot combine with itself"),Inventory->CanCombineForRecipe(Wood,Wood,TEXT("field_splint")));
    TestFalse(TEXT("Inventory order does not turn non-held rags into held input"),Inventory->CanCombineForRecipe(Selected,Wood,TEXT("field_splint")));
    TestTrue(TEXT("Held wood and selected rags offer splint"),Inventory->CanCombineForRecipe(Wood,Selected,TEXT("field_splint")));
    auto* Rags=Inventory->Stacks.FindByPredicate([&](const auto& S){return S.StackId==Selected;});
    Rags->Condition=0;
    TestFalse(TEXT("Ruined selected ingredient rejected"),Inventory->CanCombineForRecipe(Wood,Selected,TEXT("field_splint")));
    Rags->Condition=100;
    FString Error;
    const auto Before=Inventory->Stacks;
    const auto Unchanged=[&]()
    {
        if(Before.Num()!=Inventory->Stacks.Num())return false;
        for(const auto& Expected:Before)
        {
            const auto* Actual=Inventory->Stacks.FindByPredicate([&](const auto& S){return S.StackId==Expected.StackId;});
            if(!Actual||Actual->ItemId!=Expected.ItemId||Actual->Count!=Expected.Count||Actual->Condition!=Expected.Condition||
               Actual->ContainerId!=Expected.ContainerId||Actual->X!=Expected.X||Actual->Y!=Expected.Y||Actual->bRotated!=Expected.bRotated)return false;
        }
        return true;
    };
    Inventory->WeightCapacityKg=0;
    TestFalse(TEXT("No output capacity rejects selected transaction"),Inventory->TryCraftRecipe(TEXT("field_splint"),Server,TEXT("owner"),Error,Wood,Selected));
    TestTrue(TEXT("No capacity preserves every selected and unselected stack"),Unchanged());
    Inventory->WeightCapacityKg=100;
    TestFalse(TEXT("Rejected profile write rolls selected transaction back"),Inventory->TryCraftRecipe(TEXT("field_splint"),TEXT("../invalid"),TEXT("owner"),Error,Wood,Selected));
    TestTrue(TEXT("Failed profile write preserves all inventory instance data"),Unchanged());
    TestTrue(TEXT("Exact selected transaction succeeds"),Inventory->TryCraftRecipe(TEXT("field_splint"),Server,TEXT("owner"),Error,Wood,Selected));
    TestFalse(TEXT("Selected wood consumed"),Inventory->Stacks.ContainsByPredicate([&](const auto& S){return S.StackId==Wood;}));
    TestFalse(TEXT("Selected four rags consumed"),Inventory->Stacks.ContainsByPredicate([&](const auto& S){return S.StackId==Selected;}));
    for(const auto& Pair:Unselected)
    {
        const auto* Actual=Inventory->Stacks.FindByPredicate([&](const auto& S){return S.StackId==Pair.Key;});
        TestTrue(TEXT("Unselected identical rags retain their physical identity and count"),Actual&&Actual->Count==Pair.Value&&Actual->ItemId==TEXT("rags"));
    }
    TestTrue(TEXT("One actual splint returned"),Inventory->Stacks.ContainsByPredicate([](const auto& S){return S.ItemId==TEXT("splint")&&S.Count==1;}));
    TestFalse(TEXT("Replay cannot consume stale selected identities"),Inventory->TryCraftRecipe(TEXT("field_splint"),Server,TEXT("owner"),Error,Wood,Selected));
    auto* Reloaded=World->SpawnActor<AAnomaliaSurvivor>();
    TestTrue(TEXT("Persisted selected result reloads"),Reloaded->InventoryComponent->LoadInventoryFromPlayerProfile(Server,TEXT("owner"),Error));
    TestTrue(TEXT("Restart restores the output rather than the consumed inputs"),Reloaded->InventoryComponent->Stacks.ContainsByPredicate([](const auto& S){return S.ItemId==TEXT("splint")&&S.Count==1;}));
    World->DestroyWorld(false);return true;
}
#endif
