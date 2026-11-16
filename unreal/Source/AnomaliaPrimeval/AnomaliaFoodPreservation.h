#pragma once

#include "CoreMinimal.h"

/** Shared, deterministic food aging rules, used both by carried food and appliances. */
namespace AnomaliaFoodPreservation
{
    bool IsPerishable(FName ItemId);
    /** Freshness loss in one game hour at a given Celsius temperature. */
    float DecayPerHour(FName ItemId, float TemperatureC);
    /** A value of zero means spoiled. Never increases freshness. */
    float Advance(FName ItemId, float Freshness01, float Hours, float TemperatureC);
}
