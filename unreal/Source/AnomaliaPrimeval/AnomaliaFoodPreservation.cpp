#include "AnomaliaFoodPreservation.h"

namespace AnomaliaFoodPreservation
{
    bool IsPerishable(FName ItemId)
    {
        return ItemId == TEXT("raw_meat") || ItemId == TEXT("raw_fish") ||
            ItemId == TEXT("cooked_meat") || ItemId == TEXT("cooked_fish") ||
            ItemId == TEXT("meat") || ItemId == TEXT("egg") ||
            ItemId == TEXT("berry") || ItemId == TEXT("vegetable");
    }

    float DecayPerHour(FName ItemId, float TemperatureC)
    {
        if (!IsPerishable(ItemId) || !FMath::IsFinite(TemperatureC)) return 0.f;
        // Approximate gameplay shelf lives at 22 C; these are game-design values, not food-safety claims.
        const float LifeHoursAt22C =
            ItemId == TEXT("raw_fish") || ItemId == TEXT("raw_meat") ? 12.f :
            ItemId == TEXT("cooked_fish") || ItemId == TEXT("cooked_meat") || ItemId == TEXT("meat") ? 36.f :
            ItemId == TEXT("egg") ? 48.f : 72.f;
        // Q10-style temperature effect: food lasts longer when cold, but never indefinitely.
        const float RelativeRate = FMath::Pow(2.5f, (FMath::Clamp(TemperatureC, -20.f, 60.f) - 22.f) / 10.f);
        return RelativeRate / LifeHoursAt22C;
    }

    float Advance(FName ItemId, float Freshness01, float Hours, float TemperatureC)
    {
        if (!FMath::IsFinite(Freshness01)) return 0.f;
        const float Previous = FMath::Clamp(Freshness01, 0.f, 1.f);
        if (!FMath::IsFinite(Hours) || Hours <= 0.f) return Previous;
        return FMath::Clamp(Previous - FMath::Min(Hours, 24.f * 365.f) * DecayPerHour(ItemId, TemperatureC), 0.f, Previous);
    }
}
