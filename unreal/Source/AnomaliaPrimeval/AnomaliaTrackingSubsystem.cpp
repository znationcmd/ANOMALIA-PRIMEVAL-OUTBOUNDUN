#include "AnomaliaTrackingSubsystem.h"
#include "Engine/World.h"

bool UAnomaliaTrackingSubsystem::DoesSupportWorldType(EWorldType::Type Type) const
{
 return Type == EWorldType::Game || Type == EWorldType::PIE;
}
TStatId UAnomaliaTrackingSubsystem::GetStatId() const
{
 RETURN_QUICK_DECLARE_CYCLE_STAT(UAnomaliaTrackingSubsystem, STATGROUP_Tickables);
}
double UAnomaliaTrackingSubsystem::Lifespan(const FAnomaliaTrackClue& Clue, float Rain) const
{
 const float TerrainFactor = Clue.Terrain == TEXT("mud") ? 1.7f :
  Clue.Terrain == TEXT("snow") ? 1.6f : Clue.Terrain == TEXT("sand") ? 1.25f :
  Clue.Terrain == TEXT("grass") ? .75f : Clue.Terrain == TEXT("stone") ? .2f :
  Clue.Terrain == TEXT("water") ? .02f : 1.f;
 return (Clue.Kind == EAnomaliaTrackKind::Blood ? 900. : 1500.) * TerrainFactor *
  (1. - FMath::Clamp(static_cast<double>(Rain), 0., 1.) * .85);
}
void UAnomaliaTrackingSubsystem::AddClue(EAnomaliaTrackKind Kind, const FString& ActorId, FVector Location, FRotator Direction, FName Terrain, float Severity)
{
 if (ActorId.IsEmpty() || Location.ContainsNaN() || Direction.ContainsNaN() || !FMath::IsFinite(Severity)) return;
 FAnomaliaTrackClue Clue;
 Clue.Kind = Kind; Clue.ActorId = ActorId; Clue.Location = Location; Clue.Direction = Direction;
 Clue.Terrain = Terrain; Clue.Severity = FMath::Clamp(Severity, 0.f, 1.f);
 Clue.SpawnTimeSeconds = ClockSeconds;
 Clues.Add(MoveTemp(Clue));
 if (Clues.Num() > 2000) Clues.RemoveAt(0, Clues.Num() - 2000);
}
TArray<FAnomaliaTrackClue> UAnomaliaTrackingSubsystem::FindNearby(FVector Origin, float Radius, float Rain, const FString& ActorFilter) const
{
 TArray<FAnomaliaTrackClue> Found;
 const float RadiusSquared = FMath::Square(FMath::Max(0.f, Radius));
 for (const FAnomaliaTrackClue& Clue : Clues)
 {
  if (!ActorFilter.IsEmpty() && Clue.ActorId != ActorFilter) continue;
  if (ClockSeconds - Clue.SpawnTimeSeconds >= Lifespan(Clue, Rain)) continue;
  if (FVector::DistSquared(Origin, Clue.Location) <= RadiusSquared) Found.Add(Clue);
 }
 Found.Sort([](const FAnomaliaTrackClue& A, const FAnomaliaTrackClue& B){return A.SpawnTimeSeconds > B.SpawnTimeSeconds;});
 return Found;
}
void UAnomaliaTrackingSubsystem::Tick(float DeltaTime)
{
 ClockSeconds += FMath::Max(0.f, DeltaTime);
 CleanupAccumulator += DeltaTime;
 if (CleanupAccumulator < 30.f) return;
 CleanupAccumulator = 0.f;
 Clues.RemoveAll([this](const FAnomaliaTrackClue& Clue)
 {return ClockSeconds - Clue.SpawnTimeSeconds >= Lifespan(Clue, 0.f);});
}