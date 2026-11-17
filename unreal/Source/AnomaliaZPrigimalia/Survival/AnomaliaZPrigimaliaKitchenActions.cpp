#include "../AnomaliaZPrigimaliaInventoryComponent.h"
#include "AnomaliaZPrigimaliaWaterSource.h"
#include "AnomaliaZPrigimaliaWeather.h"
#include "../AnomaliaZPrigimaliaSurvivor.h"
#include "../AnomaliaZPrigimaliaGameMode.h"
#include "../AnomaliaZPrigimaliaConfigLibrary.h"
#include "../AnomaliaZPrigimaliaLootSubsystem.h"
#include "../AnomaliaZPrigimaliaEconomySubsystem.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Controller.h"
#include "TimerManager.h"

/**
 * Actual server inventory interactions, not decorative/CONFIG_ONLY recipes.
 * A source actor is authored over real water. Nearby burning heat sources
 * are the game's existing fuel-limited fire/heater components.
 * Every successful conversion commits exactly one survivor profile write.
 * No client can choose a result item or trust its own water/heat state.
 */
namespace
{
    FName FilledItemFor(FName Empty, bool bPotable)
    {
        if(Empty==TEXT("empty_water_bottle"))
            return bPotable?FName(TEXT("water_bottle")):FName(TEXT("dirty_water_bottle"));
        if(Empty==TEXT("empty_military_canteen"))
            return bPotable?FName(TEXT("military_canteen")):FName(TEXT("dirty_military_canteen"));
        if(Empty==TEXT("empty_filter_canteen"))
            return bPotable?FName(TEXT("filter_canteen")):FName(TEXT("dirty_filter_canteen"));
        if(Empty==TEXT("cooking_pot"))
            return bPotable?FName(TEXT("cooking_pot_water")):FName(TEXT("dirty_cooking_pot_water"));
        return NAME_None;
    }

    FName TreatedItemFor(FName Dirty)
    {
        if(Dirty==TEXT("dirty_water_bottle"))return TEXT("water_bottle");
        if(Dirty==TEXT("dirty_military_canteen"))return TEXT("military_canteen");
        if(Dirty==TEXT("dirty_filter_canteen"))return TEXT("filter_canteen");
        return NAME_None;
    }
}

bool UAnomaliaZPrigimaliaInventoryComponent::IsFillableContainer(FName Id)
{
    return Id==TEXT("empty_water_bottle") || Id==TEXT("empty_military_canteen") ||
           Id==TEXT("empty_filter_canteen") || Id==TEXT("cooking_pot");
}
bool UAnomaliaZPrigimaliaInventoryComponent::IsKitchenUtensil(FName Id)
{
    return Id==TEXT("frying_pan") || Id==TEXT("cooking_pot_water");
}
FName UAnomaliaZPrigimaliaInventoryComponent::CookedFoodFor(FName Id)
{
    if(Id==TEXT("raw_meat")) return TEXT("cooked_meat");
    if(Id==TEXT("raw_fish")) return TEXT("cooked_fish");
    if(Id==TEXT("egg")) return TEXT("cooked_egg");
    if(Id==TEXT("potato")) return TEXT("cooked_potato");
    if(Id==TEXT("vegetable")) return TEXT("cooked_vegetable");
    return NAME_None;
}

AAnomaliaZPrigimaliaWaterSource* UAnomaliaZPrigimaliaInventoryComponent::FindNearbyWaterSource() const
{
    if(!GetWorld() || !GetOwner())return nullptr;
    AAnomaliaZPrigimaliaWaterSource* Closest=nullptr;
    double BestSq=TNumericLimits<double>::Max();
    for(TActorIterator<AAnomaliaZPrigimaliaWaterSource> It(GetWorld());It;++It)
    {
        auto* Source=*It;
        if(!IsValid(Source) || !Source->CanFillFrom(GetOwner()->GetActorLocation()))continue;
        const double D=FVector::DistSquared(Source->GetActorLocation(),GetOwner()->GetActorLocation());
        if(D<BestSq){BestSq=D;Closest=Source;}
    }
    return Closest;
}
bool UAnomaliaZPrigimaliaInventoryComponent::HasLiveKitchenFire() const
{
    // Required at both request and completion; walls block heat via the
    // existing server visibility test. No fictitious "fire in inventory".
    return GetWorld() && GetOwner() &&
        UAnomaliaZPrigimaliaHeatSourceComponent::Sample(
            GetWorld(),GetOwner()->GetActorLocation()+FVector(0,0,50),GetOwner())>0.05f;
}

void UAnomaliaZPrigimaliaInventoryComponent::ReportKitchenResult(const FString& Message)
{
    UseMessage=Message;
    OnInventoryUpdated.Broadcast();
    if(GetOwner())GetOwner()->ForceNetUpdate();
}

/**
 * One transactional exchange, preserving other profile fields and restoring
 * BOTH stacks/NextStackId on any invalid operation or failed disk save.
 * For single-item bottles on belt/back, the physical stack/slot is retained.
 * For a stack of empty containers, one is exchanged into a newly placed item.
 */
bool UAnomaliaZPrigimaliaInventoryComponent::CommitKitchenExchange(
    int32 PrimaryId,int32 ExpectedPrimary,FName PrimaryOutput,
    int32 SecondaryId,int32 ExpectedSecondary,FName SecondaryOutput,
    FName ExtraConsumed,FString& OutError)
{
    OutError.Empty();
    auto* User=Cast<AAnomaliaZPrigimaliaSurvivor>(GetOwner());
    auto* Mode=GetWorld()?GetWorld()->GetAuthGameMode<AAnomaliaZPrigimaliaGameMode>():nullptr;
    const auto* Loot=GetWorld()?GetWorld()->GetSubsystem<UAnomaliaZPrigimaliaLootSubsystem>():nullptr;
    const auto* Economy=GetWorld()?GetWorld()->GetSubsystem<UAnomaliaZPrigimaliaEconomySubsystem>():nullptr;
    if(!User||!User->HasAuthority()||!Mode||!User->GetController()||
       User->GetController()->GetPawn()!=User||User->Health<=0||User->bSleeping||
       IsPersistenceLocked()||bSuppressNotifications)
    {OutError=TEXT("Action indisponible pendant une sauvegarde ou sans personnage vivant.");return false;}
    const FString PlayerId=Mode->GetPersistentPlayerId(User->GetController());
    if(PlayerId.IsEmpty()||(Loot&&Loot->HasPendingPlayer(PlayerId))||
       (Economy&&Economy->HasPendingPlayer(PlayerId)))
    {OutError=TEXT("Profil indisponible pendant la synchronisation.");return false;}
    if(PrimaryId<=0 || ExpectedPrimary<1 || (SecondaryId!=0 && (SecondaryId==PrimaryId || ExpectedSecondary<1)))
    {OutError=TEXT("Sélection périmée.");return false;}

    const auto Before=Stacks;
    const int32 BeforeNextId=NextStackId;
    bSuppressNotifications=true;
    auto Restore=[&]()
    {
        Stacks=Before;
        NextStackId=BeforeNextId;
        bSuppressNotifications=false;
    };
    auto ExchangeOne=[&](int32 StackId,int32 Expected,FName Output)->bool
    {
        auto* Stack=Stacks.FindByPredicate([&](const auto& Row){return Row.StackId==StackId;});
        if(!Stack||Stack->Count!=Expected||IsRecoveryContainer(Stack->ContainerId))return false;
        if(Output.IsNone())return true; // pan stays in inventory.
        float NewWeight=0;int32 NewMax=0;FIntPoint NewSize;
        if(!GetItemRules(Output,NewWeight,NewMax,NewSize))return false;
        if(Stack->Count==1)
        {
            Stack->ItemId=Output;
            Stack->TemperatureC=20.f;
            Stack->FrozenFraction=0.f;
            return CanPlace(Stacks,*Stack,Stack->ContainerId,Stack->X,Stack->Y,Stack->bRotated) &&
                GetCurrentWeightKg()<=WeightCapacityKg+KINDA_SMALL_NUMBER;
        }
        // A container stack cannot be in an equipment attachment (single slot).
        if(FindAttachmentRule(Stack->ContainerId))return false;
        --Stack->Count;
        return TryAddItem(Output,1);
    };

    if(!ExchangeOne(PrimaryId,ExpectedPrimary,PrimaryOutput) ||
       (SecondaryId!=0 && !ExchangeOne(SecondaryId,ExpectedSecondary,SecondaryOutput)) ||
       (!ExtraConsumed.IsNone() && !TryRemoveItem(ExtraConsumed,1)))
    {
        Restore();
        OutError=TEXT("Matériau manquant, récipient déplacé ou inventaire plein. Rien n’a été consommé.");
        return false;
    }
    FString Serialized;
    if(!BuildInventoryProfile(Mode->ServerId,PlayerId,Serialized,OutError))
    {Restore();return false;}
    const auto After=Stacks;
    const int32 AfterNextId=NextStackId;
    Restore();
    if(!UAnomaliaZPrigimaliaConfigLibrary::SavePlayerProfile(Mode->ServerId,PlayerId,Serialized,OutError))
        return false;
    NextStackId=AfterNextId;
    auto ToCommit=After;
    Commit(MoveTemp(ToCommit));
    return true;
}

bool UAnomaliaZPrigimaliaInventoryComponent::RunKitchenOnServer(
    EKitchenOperation Action,int32 UtensilId,int32 ExpectedCount,int32 FoodId)
{
    auto* Survivor=Cast<AAnomaliaZPrigimaliaSurvivor>(GetOwner());
    if(!Survivor||!Survivor->HasAuthority()||!GetWorld()||!Survivor->GetController()||
       Survivor->GetController()->GetPawn()!=Survivor)return false;
    const double Now=GetWorld()->GetRealTimeSeconds();
    if(Now<NextKitchenRequestTime)return false;
    NextKitchenRequestTime=Now+.30;
    if(bKitchenPending)
    {ReportKitchenResult(TEXT("Une cuisson est déjà en cours."));return false;}
    if(Survivor->Health<=0||Survivor->bSleeping||IsPersistenceLocked())
    {ReportKitchenResult(TEXT("L'interaction n'est pas disponible actuellement."));return false;}
    const auto* Utensil=Stacks.FindByPredicate([&](const auto& S){return S.StackId==UtensilId;});
    if(!Utensil||Utensil->Count!=ExpectedCount||ExpectedCount<1||IsRecoveryContainer(Utensil->ContainerId))
    {ReportKitchenResult(TEXT("Récipient absent ou déplacé."));return false;}

    if(Action==EKitchenOperation::Fill)
    {
        if(!IsFillableContainer(Utensil->ItemId))
        {ReportKitchenResult(TEXT("Ce récipient est déjà plein ou ne contient pas d'eau."));return false;}
        const auto* Source=FindNearbyWaterSource();
        if(!Source)
        {ReportKitchenResult(TEXT("Approchez une rivière, un puits ou une fontaine équipée d'un point d'eau."));return false;}
        const FName Filled=FilledItemFor(Utensil->ItemId,Source->bPotable);
        FString Error;
        if(!CommitKitchenExchange(UtensilId,ExpectedCount,Filled,0,0,NAME_None,NAME_None,Error))
        {ReportKitchenResult(Error);return false;}
        ReportKitchenResult(Source->bPotable?TEXT("Récipient rempli d'eau potable."):
                                       TEXT("Récipient rempli d'eau non traitée : purifiez-la ou faites-la bouillir."));
        return true;
    }

    if(Action==EKitchenOperation::Treat)
    {
        const FName Clean=TreatedItemFor(Utensil->ItemId);
        if(Clean.IsNone())
        {ReportKitchenResult(TEXT("Ce récipient ne contient pas d'eau à traiter."));return false;}
        FString Error;
        if(!CommitKitchenExchange(UtensilId,ExpectedCount,Clean,0,0,NAME_None,TEXT("water_purification_tablets"),Error))
        {ReportKitchenResult(Error);return false;}
        ReportKitchenResult(TEXT("Eau traitée : une tablette consommée."));
        return true;
    }

    if(Action==EKitchenOperation::Boil || Action==EKitchenOperation::Cook)
    {
        if(!HasLiveKitchenFire())
        {ReportKitchenResult(TEXT("Approchez un feu allumé et alimenté, sans obstacle."));return false;}
        if(ExpectedCount!=1)
        {ReportKitchenResult(TEXT("Séparez les ustensiles empilés avant cuisson."));return false;}
        if(Action==EKitchenOperation::Boil)
        {
            if(Utensil->ItemId!=TEXT("dirty_cooking_pot_water"))
            {ReportKitchenResult(TEXT("Remplissez d'abord la marmite avec de l'eau non traitée."));return false;}
            PendingFoodId=0;
            PendingFoodCount=0;
        }
        else
        {
            if(!IsKitchenUtensil(Utensil->ItemId)||FoodId<=0||FoodId==UtensilId)
            {ReportKitchenResult(TEXT("Utilisez une poêle ou une marmite d'eau propre avec un aliment cru."));return false;}
            const auto* Food=Stacks.FindByPredicate([&](const auto& S){return S.StackId==FoodId;});
            if(!Food||Food->Count<1||IsRecoveryContainer(Food->ContainerId)||
               CookedFoodFor(Food->ItemId).IsNone())
            {ReportKitchenResult(TEXT("Sélectionnez un aliment cru compatible."));return false;}
            PendingFoodId=FoodId;
            PendingFoodCount=Food->Count;
        }
        bKitchenPending=true;
        bKitchenBoiling=Action==EKitchenOperation::Boil;
        PendingUtensilId=UtensilId;
        PendingUtensilCount=ExpectedCount;
        const float Duration=bKitchenBoiling?20.f:(Utensil->ItemId==TEXT("frying_pan")?30.f:40.f);
        GetWorld()->GetTimerManager().SetTimer(KitchenCookTimer,this,
            &UAnomaliaZPrigimaliaInventoryComponent::FinishKitchenCooking,Duration,false);
        GetWorld()->GetTimerManager().SetTimer(KitchenCheckTimer,this,
            &UAnomaliaZPrigimaliaInventoryComponent::CheckKitchenFire,1.f,true);
        ReportKitchenResult(FString::Printf(TEXT("%s : %.0f secondes. Restez près du feu allumé."),
            bKitchenBoiling?TEXT("Ébullition"):TEXT("Cuisson"),Duration));
        return true;
    }
    return false;
}

void UAnomaliaZPrigimaliaInventoryComponent::CheckKitchenFire()
{
    if(!bKitchenPending||!HasLiveKitchenFire()||IsPersistenceLocked())
    {
        if(GetWorld()){GetWorld()->GetTimerManager().ClearTimer(KitchenCookTimer);
                       GetWorld()->GetTimerManager().ClearTimer(KitchenCheckTimer);}
        bKitchenPending=false;
        ReportKitchenResult(TEXT("Cuisson interrompue : feu éteint, déplacement ou sauvegarde. Aliments conservés."));
    }
}

void UAnomaliaZPrigimaliaInventoryComponent::FinishKitchenCooking()
{
    if(!bKitchenPending)return;
    bKitchenPending=false;
    if(GetWorld())GetWorld()->GetTimerManager().ClearTimer(KitchenCheckTimer);
    if(!HasLiveKitchenFire())
    {ReportKitchenResult(TEXT("Cuisson annulée : feu éteint ou trop éloigné. Rien n'a été consommé."));return;}
    const auto* Utensil=Stacks.FindByPredicate([&](const auto& S){return S.StackId==PendingUtensilId;});
    if(!Utensil||Utensil->Count!=PendingUtensilCount)
    {ReportKitchenResult(TEXT("Ustensile déplacé : cuisson annulée."));return;}
    FName VesselOutput=NAME_None;
    int32 FoodId=0, FoodCount=0;
    FName FoodOutput=NAME_None;
    if(bKitchenBoiling)
    {
        if(Utensil->ItemId!=TEXT("dirty_cooking_pot_water"))
        {ReportKitchenResult(TEXT("Marmite modifiée pendant l'ébullition."));return;}
        VesselOutput=TEXT("cooking_pot_water");
    }
    else
    {
        if(!IsKitchenUtensil(Utensil->ItemId))
        {ReportKitchenResult(TEXT("Ustensile non compatible."));return;}
        const auto* Food=Stacks.FindByPredicate([&](const auto& S){return S.StackId==PendingFoodId;});
        if(!Food || Food->Count!=PendingFoodCount)
        {ReportKitchenResult(TEXT("Aliment modifié : cuisson annulée."));return;}
        FoodOutput=CookedFoodFor(Food->ItemId);
        if(FoodOutput.IsNone())
        {ReportKitchenResult(TEXT("Aliment non compatible."));return;}
        FoodId=PendingFoodId;FoodCount=PendingFoodCount;
        // A single potful is used for each batch; the pan is never consumed.
        if(Utensil->ItemId==TEXT("cooking_pot_water"))VesselOutput=TEXT("cooking_pot");
    }
    FString Error;
    if(!CommitKitchenExchange(PendingUtensilId,PendingUtensilCount,VesselOutput,
                              FoodId,FoodCount,FoodOutput,NAME_None,Error))
    {ReportKitchenResult(Error);return;}
    ReportKitchenResult(bKitchenBoiling?TEXT("L'eau de la marmite est désormais potable."):
                                  TEXT("Aliment cuit et enregistré dans l'inventaire."));
}

bool UAnomaliaZPrigimaliaInventoryComponent::RequestFillContainer(int32 Id,int32 Count)
{
    if(!GetOwner())return false;
    if(GetOwner()->HasAuthority())return RunKitchenOnServer(EKitchenOperation::Fill,Id,Count);
    ServerRequestFillContainer(Id,Count);return true;
}
void UAnomaliaZPrigimaliaInventoryComponent::ServerRequestFillContainer_Implementation(int32 Id,int32 Count)
{ RunKitchenOnServer(EKitchenOperation::Fill,Id,Count); }

bool UAnomaliaZPrigimaliaInventoryComponent::RequestTreatWater(int32 Id,int32 Count)
{
    if(!GetOwner())return false;
    if(GetOwner()->HasAuthority())return RunKitchenOnServer(EKitchenOperation::Treat,Id,Count);
    ServerRequestTreatWater(Id,Count);return true;
}
void UAnomaliaZPrigimaliaInventoryComponent::ServerRequestTreatWater_Implementation(int32 Id,int32 Count)
{ RunKitchenOnServer(EKitchenOperation::Treat,Id,Count); }

bool UAnomaliaZPrigimaliaInventoryComponent::RequestBoilPot(int32 Id,int32 Count)
{
    if(!GetOwner())return false;
    if(GetOwner()->HasAuthority())return RunKitchenOnServer(EKitchenOperation::Boil,Id,Count);
    ServerRequestBoilPot(Id,Count);return true;
}
void UAnomaliaZPrigimaliaInventoryComponent::ServerRequestBoilPot_Implementation(int32 Id,int32 Count)
{ RunKitchenOnServer(EKitchenOperation::Boil,Id,Count); }

bool UAnomaliaZPrigimaliaInventoryComponent::RequestCookFood(int32 UtensilId,int32 FoodId,int32 ExpectedFoodCount)
{
    if(!GetOwner())return false;
    if(GetOwner()->HasAuthority())return RunKitchenOnServer(EKitchenOperation::Cook,UtensilId,1,FoodId);
    ServerRequestCookFood(UtensilId,FoodId,ExpectedFoodCount);return true;
}
void UAnomaliaZPrigimaliaInventoryComponent::ServerRequestCookFood_Implementation(int32 UtensilId,int32 FoodId,int32 ExpectedFoodCount)
{
    // Server rejects stale counts; caller cannot specify the result food or vessel.
    const auto* Food=Stacks.FindByPredicate([&](const auto& S){return S.StackId==FoodId;});
    if(!Food||Food->Count!=ExpectedFoodCount||ExpectedFoodCount<1)
    {ReportKitchenResult(TEXT("L'aliment a changé : sélectionnez-le à nouveau."));return;}
    RunKitchenOnServer(EKitchenOperation::Cook,UtensilId,1,FoodId);
}
