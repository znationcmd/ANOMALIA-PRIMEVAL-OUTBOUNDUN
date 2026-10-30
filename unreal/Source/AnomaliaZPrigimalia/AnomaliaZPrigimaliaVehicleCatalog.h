#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "AnomaliaZPrigimaliaVehicleCatalog.generated.h"

/** Data-driven vehicle roster: definitions only, not finished physics or art assets. */
UENUM(BlueprintType)
enum class EAnomaliaZPrigimaliaVehicleDomain : uint8
{
    Ground UMETA(DisplayName="Terre"),
    Water UMETA(DisplayName="Mer"),
    Underwater UMETA(DisplayName="Sous-marin"),
    Air UMETA(DisplayName="Air"),
    Rail UMETA(DisplayName="Rail"),
    Cable UMETA(DisplayName="Téléphérique")
};

USTRUCT(BlueprintType)
struct FAnomaliaZPrigimaliaVehicleDefinition
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|Vehicles")
    FName Id = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|Vehicles")
    FString Label;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|Vehicles")
    EAnomaliaZPrigimaliaVehicleDomain Domain = EAnomaliaZPrigimaliaVehicleDomain::Ground;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|Vehicles", meta=(ClampMin="1.0"))
    float MaxSpeedKmh = 80.f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|Vehicles", meta=(ClampMin="0"))
    int32 Seats = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|Vehicles", meta=(ClampMin="0"))
    int32 StorageSlots = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|Vehicles")
    bool bEmergencyVehicle = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|Vehicles")
    bool bMilitaryVehicle = false;
};

UCLASS()
class ANOMALIAZPRIGIMALIA_API UAnomaliaZPrigimaliaVehicleCatalog : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    /** Full initial ANOMALIA roster, available in Blueprints and C++. */
    UFUNCTION(BlueprintPure, Category="ANOMALIA|Vehicles")
    static TArray<FAnomaliaZPrigimaliaVehicleDefinition> GetDefaultVehicleCatalog();

    UFUNCTION(BlueprintPure, Category="ANOMALIA|Vehicles")
    static bool FindVehicleDefinition(FName VehicleId, FAnomaliaZPrigimaliaVehicleDefinition& OutDefinition);
};
