#include "AnomaliaPerformanceLibrary.h"
#include "Engine/Engine.h"
#include "GameFramework/GameUserSettings.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/Paths.h"

TArray<FString> UAnomaliaPerformanceLibrary::GetGraphicsPresets()
{
    return {TEXT("PC_High"), TEXT("PS5_Target"), TEXT("XboxSeriesX_Target"), TEXT("Performance_Fallback"), TEXT("XboxSeriesS_Target"), TEXT("Android_Mobile_Target"), TEXT("IOS_Mobile_Target")};
}

bool UAnomaliaPerformanceLibrary::ApplyGraphicsPreset(const FString& PresetName)
{
    if (!GetGraphicsPresets().Contains(PresetName) || !GEngine || !GConfig) return false;
    UGameUserSettings* Settings = GEngine->GetGameUserSettings();
    if (!Settings) return false;

    // Standard Game.ini is included in packaged builds; presets never write to server files.
    const FString& Ini = GGameIni;
    int32 MinPercent = 50, MaxPercent = 85, FrameRate = 60;
    int32 View = 2, Shadow = 2, Effects = 2, Texture = 3, Foliage = 2;
    const FString SectionName = FString(TEXT("Anomalia.")) + PresetName;
    const TCHAR* Section = *SectionName;
    if (!GConfig->GetInt(Section, TEXT("RenderScaleMin"), MinPercent, Ini) ||
        !GConfig->GetInt(Section, TEXT("RenderScaleMax"), MaxPercent, Ini)) return false;
    GConfig->GetInt(Section, TEXT("ViewDistanceQuality"), View, Ini);
    GConfig->GetInt(Section, TEXT("ShadowQuality"), Shadow, Ini);
    GConfig->GetInt(Section, TEXT("EffectsQuality"), Effects, Ini);
    GConfig->GetInt(Section, TEXT("TextureQuality"), Texture, Ini);
    GConfig->GetInt(Section, TEXT("FoliageQuality"), Foliage, Ini);
    GConfig->GetInt(Section, TEXT("FrameRateLimit"), FrameRate, Ini);
    if (FrameRate < 15 || FrameRate > 120) return false;
    if (MinPercent < 25 || MaxPercent > 100 || MinPercent > MaxPercent) return false;
    Settings->SetViewDistanceQuality(FMath::Clamp(View, 0, 4));
    Settings->SetShadowQuality(FMath::Clamp(Shadow, 0, 4));
    Settings->SetVisualEffectQuality(FMath::Clamp(Effects, 0, 4));
    Settings->SetTextureQuality(FMath::Clamp(Texture, 0, 4));
    Settings->SetFoliageQuality(FMath::Clamp(Foliage, 0, 4));
    Settings->SetResolutionScaleValueEx(static_cast<float>(MaxPercent));
    Settings->SetDynamicResolutionEnabled(true);
    Settings->SetFrameRateLimit(static_cast<float>(FrameRate));
    Settings->ApplyNonResolutionSettings();
    Settings->SaveSettings(); // local GameUserSettings.ini, never server config.
    return true;
}
