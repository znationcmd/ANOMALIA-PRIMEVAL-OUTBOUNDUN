#include "AnomaliaFurnitureSubsystem.h"
#include "AnomaliaGameMode.h"
#include "AnomaliaSurvivor.h"
#include "AnomaliaHomesteadStation.h"
#include "Engine/World.h"
#include "Components/StaticMeshComponent.h"
#include "Dom/JsonObject.h"
#include "HAL/FileManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "CollisionQueryParams.h"
#include "CollisionShape.h"

namespace
{
    FString Text(const std::string& S) { return FString(UTF8_TO_TCHAR(S.c_str())); }
    std::string Bytes(const FString& S) { return std::string(TCHAR_TO_UTF8(*S)); }
    FTransform Transform(const AnomaliaFurniture::Record& R)
    { return FTransform(FRotator(0, R.Transform.Yaw, 0), FVector(R.Transform.X, R.Transform.Y, R.Transform.Z)); }
    EAnomaliaHomesteadObject Kind(const std::string& Type)
    {
        using K = EAnomaliaHomesteadObject;
        if (Type == "table") return K::Table;
        if (Type == "chair") return K::Chair;
        if (Type == "sofa") return K::Sofa;
        if (Type == "wardrobe") return K::Wardrobe;
        if (Type == "kitchen") return K::Kitchen;
        if (Type == "lamp") return K::Lamp;
        if (Type == "beehive") return K::Beehive;
        if (Type == "doghouse") return K::Doghouse;
        if (Type == "barn") return K::Barn;
        if (Type == "fence") return K::Fence;
        if (Type == "tractor_shed") return K::TractorShed;
        return K::Bed;
    }
}

FString UAnomaliaFurnitureSubsystem::FilePath() const
{
    return FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Servers"), ServerId,
        TEXT("Construction"), TEXT("world.json"));
}

AAnomaliaHomesteadStation* UAnomaliaFurnitureSubsystem::SpawnRecord(const AnomaliaFurniture::Record& R)
{
    FActorSpawnParameters Params;
    Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    AAnomaliaHomesteadStation* Actor = GetWorld()->SpawnActor<AAnomaliaHomesteadStation>(
        AAnomaliaHomesteadStation::StaticClass(), Transform(R), Params);
    if (Actor)
    {
        Actor->ObjectType = Kind(R.Type);
        Actor->PlacementId = Text(R.Id);
        Actor->ForceNetUpdate();
    }
    return Actor;
}

bool UAnomaliaFurnitureSubsystem::LoadWorld(const FString& InServerId, FString& Error)
{
    Error.Empty();
    if (!GetWorld() || GetWorld()->GetNetMode() == NM_Client ||
        !AnomaliaFurniture::SafeId(Bytes(InServerId))) { Error = TEXT("Invalid server world scope"); return false; }
    if (bReady) return InServerId == ServerId;
    ServerId = InServerId;
    const FString File = FilePath();
    SavedRoot = MakeShared<FJsonObject>();
    if (!IFileManager::Get().FileExists(*File)) { bReady = true; return true; }
    if (IFileManager::Get().FileSize(*File) > 1048576 || !FFileHelper::LoadFileToString(LoadedRaw, *File))
    { Error = TEXT("Cannot read construction world"); return false; }
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(LoadedRaw);
    if (!FJsonSerializer::Deserialize(Reader, SavedRoot) || !SavedRoot.IsValid())
    { Error = TEXT("Invalid construction JSON; original preserved"); return false; }
    FString Scope; double Version = 0;
    const TArray<TSharedPtr<FJsonValue>>* Rows = nullptr;
    if (!SavedRoot->TryGetNumberField(TEXT("schemaVersion"), Version) || Version != 1 ||
        !SavedRoot->TryGetStringField(TEXT("serverId"), Scope) || Scope != ServerId ||
        !SavedRoot->TryGetArrayField(TEXT("placements"), Rows) || !Rows || Rows->Num() > 256)
    { Error = TEXT("Invalid construction schema or server scope"); return false; }
    std::vector<AnomaliaFurniture::Record> Records;
    for (const TSharedPtr<FJsonValue>& Value : *Rows)
    {
        if (!Value.IsValid() || Value->Type != EJson::Object) { Error = TEXT("Invalid placement row"); return false; }
        const TSharedPtr<FJsonObject> Row = Value->AsObject();
        FString Id, Owner, Type;
        AnomaliaFurniture::Pose P;
        if (!Row->TryGetStringField(TEXT("id"), Id) || !Row->TryGetStringField(TEXT("owner"), Owner) ||
            !Row->TryGetStringField(TEXT("type"), Type) || !Row->TryGetNumberField(TEXT("x"), P.X) ||
            !Row->TryGetNumberField(TEXT("y"), P.Y) || !Row->TryGetNumberField(TEXT("z"), P.Z) ||
            !Row->TryGetNumberField(TEXT("yaw"), P.Yaw))
        { Error = TEXT("Missing placement fields"); return false; }
        Records.push_back({Bytes(Id), Bytes(Owner), Bytes(Type), P});
    }
    AnomaliaFurniture::Layout Candidate;
    if (!Candidate.Load(Records)) { Error = Text(Candidate.LastError()); return false; }
    TMap<FString, TWeakObjectPtr<AAnomaliaHomesteadStation>> Spawned;
    for (const auto& Pair : Candidate.All())
    {
        AAnomaliaHomesteadStation* Actor = SpawnRecord(Pair.second);
        if (!Actor)
        {
            for (const auto& Item : Spawned) if (Item.Value.IsValid()) Item.Value->Destroy();
            Error = TEXT("Construction actors could not be restored; source file preserved"); return false;
        }
        Spawned.Add(Text(Pair.first), Actor);
    }
    Layout = std::move(Candidate); Actors = std::move(Spawned); bReady = true;
    return true;
}

bool UAnomaliaFurnitureSubsystem::Persist(const AnomaliaFurniture::Layout& Candidate, FString& Error)
{
    const FString File = FilePath();
    FString Current;
    if (IFileManager::Get().FileExists(*File))
    {
        if (IFileManager::Get().FileSize(*File) > 1048576 || !FFileHelper::LoadFileToString(Current, *File) || Current != LoadedRaw)
        { Error = TEXT("Construction file changed externally; restart before editing"); return false; }
    }
    else if (!LoadedRaw.IsEmpty()) { Error = TEXT("Construction file disappeared; original session preserved"); return false; }
    TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>(*SavedRoot);
    TMap<FString, TSharedPtr<FJsonObject>> PreviousRows;
    const TArray<TSharedPtr<FJsonValue>>* OldRows = nullptr;
    if (SavedRoot->TryGetArrayField(TEXT("placements"), OldRows) && OldRows)
        for (const auto& Value : *OldRows)
        {
            FString Id;
            if (Value.IsValid() && Value->Type == EJson::Object && Value->AsObject()->TryGetStringField(TEXT("id"), Id))
                PreviousRows.Add(Id, Value->AsObject());
        }
    TArray<TSharedPtr<FJsonValue>> Rows;
    for (const auto& Pair : Candidate.All())
    {
        const auto& R = Pair.second;
        const auto* Old = PreviousRows.Find(Text(R.Id));
        TSharedPtr<FJsonObject> Row = Old ? MakeShared<FJsonObject>(**Old) : MakeShared<FJsonObject>();
        Row->SetStringField(TEXT("id"), Text(R.Id)); Row->SetStringField(TEXT("owner"), Text(R.Owner));
        Row->SetStringField(TEXT("type"), Text(R.Type));
        Row->SetNumberField(TEXT("x"), R.Transform.X); Row->SetNumberField(TEXT("y"), R.Transform.Y);
        Row->SetNumberField(TEXT("z"), R.Transform.Z); Row->SetNumberField(TEXT("yaw"), R.Transform.Yaw);
        Rows.Add(MakeShared<FJsonValueObject>(Row));
    }
    Root->SetNumberField(TEXT("schemaVersion"), 1); Root->SetStringField(TEXT("serverId"), ServerId);
    Root->SetArrayField(TEXT("placements"), Rows);
    FString Serialized;
    if (!FJsonSerializer::Serialize(Root.ToSharedRef(), TJsonWriterFactory<>::Create(&Serialized)) || Serialized.Len() > 262144)
    { Error = TEXT("Construction snapshot too large"); return false; }
    if (!IFileManager::Get().MakeDirectory(*FPaths::GetPath(File), true))
    { Error = TEXT("Cannot create construction directory"); return false; }
    const FString Temp = File + TEXT(".tmp-") + FGuid::NewGuid().ToString(EGuidFormats::Digits);
    if (!FFileHelper::SaveStringToFile(Serialized, *Temp, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM) ||
        !IFileManager::Get().Move(*File, *Temp, true, true))
    { IFileManager::Get().Delete(*Temp); Error = TEXT("Construction save failed; transaction rejected"); return false; }
    LoadedRaw = Serialized; SavedRoot = Root; return true;
}

bool UAnomaliaFurnitureSubsystem::ValidateChangedPose(AAnomaliaSurvivor* Caller,
    const AnomaliaFurniture::Record& R, FString& Error) const
{
    const FVector Position(R.Transform.X, R.Transform.Y, R.Transform.Z);
    if (FVector::DistSquared(Caller->GetActorLocation(), Position) > FMath::Square(1000.f))
    { Error = TEXT("Move within 10 metres of the furniture"); return false; }
    FCollisionQueryParams Query(SCENE_QUERY_STAT(AnomaliaFurniture), false, Caller);
    const auto* Existing = Actors.Find(Text(R.Id));
    if (Existing && Existing->IsValid()) Query.AddIgnoredActor(Existing->Get());
    FHitResult Ground;
    if (!GetWorld()->LineTraceSingleByChannel(Ground, Position + FVector(0,0,100),
        Position - FVector(0,0,100), ECC_Visibility, Query) ||
        FMath::Abs(Position.Z - (Ground.ImpactPoint.Z + 50.f)) > 15.f)
    { Error = TEXT("A supported position above the ground is required"); return false; }
    FCollisionQueryParams OverlapQuery(SCENE_QUERY_STAT(AnomaliaFurnitureOverlap), false);
    if (Existing && Existing->IsValid()) OverlapQuery.AddIgnoredActor(Existing->Get());
    if (GetWorld()->OverlapBlockingTestByChannel(Position, FRotator(0,R.Transform.Yaw,0).Quaternion(),
        ECC_Pawn, FCollisionShape::MakeBox(FVector(49.f)), OverlapQuery))
    { Error = TEXT("Furniture collides with the world"); return false; }
    return true;
}

bool UAnomaliaFurnitureSubsystem::Execute(AAnomaliaSurvivor* Caller, EAnomaliaFurnitureCommand Command,
    FName Type, const FString& Id, const FVector& Location, float Yaw, bool Confirmed, FString& Error)
{
    Error.Empty();
    if (!bReady || !IsValid(Caller) || !Caller->HasAuthority() || Caller->GetWorld() != GetWorld() ||
        !Caller->GetController() || Caller->Health <= 0)
    { Error = TEXT("Furniture editing unavailable"); return false; }
    const AAnomaliaGameMode* Rules = Cast<AAnomaliaGameMode>(GetWorld()->GetAuthGameMode());
    if (!Rules || (GetWorld()->GetNetMode() != NM_Standalone && !Rules->bEnableFurniturePrototype))
    { Error = TEXT("Creative furniture prototype disabled on this server"); return false; }
    const FString Owner = Rules->GetFurnitureOwnerId(Caller->GetController());
    if (Owner.IsEmpty()) { Error = TEXT("Authenticated player identity required"); return false; }
    const std::string Actor = Bytes(Owner);
    AnomaliaFurniture::Layout Candidate = Layout;
    bool Accepted = false;
    const AnomaliaFurniture::Pose P{Location.X, Location.Y, Location.Z, Yaw};
    switch (Command)
    {
        case EAnomaliaFurnitureCommand::Place:
            Accepted = Candidate.Place(Actor, {Bytes(FGuid::NewGuid().ToString(EGuidFormats::Digits)), Actor, Bytes(Type.ToString()), P}); break;
        case EAnomaliaFurnitureCommand::Move: Accepted = Candidate.Move(Actor, Bytes(Id), P); break;
        case EAnomaliaFurnitureCommand::Remove: Accepted = Candidate.Remove(Actor, Bytes(Id), Confirmed); break;
        case EAnomaliaFurnitureCommand::Undo: Accepted = Candidate.Undo(Actor); break;
        case EAnomaliaFurnitureCommand::Redo: Accepted = Candidate.Redo(Actor); break;
        default: Error = TEXT("Unknown furniture command"); return false;
    }
    if (!Accepted) { Error = Text(Candidate.LastError()); return false; }
    for (const auto& Pair : Layout.All())
        if (!Candidate.Find(Pair.first) && FVector::DistSquared(Caller->GetActorLocation(),
            Transform(Pair.second).GetLocation()) > FMath::Square(1000.f))
        { Error = TEXT("Move within 10 metres before removing furniture"); return false; }
    TMap<FString, TWeakObjectPtr<AAnomaliaHomesteadStation>> Added;
    // Validate every changed pose before spawning or touching committed scene objects.
    for (const auto& Pair : Candidate.All())
    {
        const auto* Old = Layout.Find(Pair.first);
        if (!Old || !(Old->Transform == Pair.second.Transform))
        {
            if (!ValidateChangedPose(Caller, Pair.second, Error)) return false;
        }
    }
    for (const auto& Pair : Candidate.All())
        if (!Layout.Find(Pair.first))
        {
            auto* Spawned = SpawnRecord(Pair.second);
            if (!Spawned)
            {
                for (const auto& Item : Added) if (Item.Value.IsValid()) Item.Value->Destroy();
                Error = TEXT("Could not spawn furniture"); return false;
            }
            Added.Add(Text(Pair.first), Spawned);
        }
    if (!Persist(Candidate, Error))
    {
        for (const auto& Pair : Added) if (Pair.Value.IsValid()) Pair.Value->Destroy();
        return false;
    }
    for (const auto& Pair : Layout.All())
        if (!Candidate.Find(Pair.first))
        {
            auto* Item = Actors.Find(Text(Pair.first));
            if (Item && Item->IsValid()) Item->Get()->Destroy();
            Actors.Remove(Text(Pair.first));
        }
    for (const auto& Pair : Added) Actors.Add(Pair.Key, Pair.Value);
    for (const auto& Pair : Candidate.All())
    {
        auto* Item = Actors.Find(Text(Pair.first));
        if (Item && Item->IsValid()) { Item->Get()->SetActorTransform(Transform(Pair.second)); Item->Get()->ForceNetUpdate(); }
    }
    Layout = std::move(Candidate); return true;
}
