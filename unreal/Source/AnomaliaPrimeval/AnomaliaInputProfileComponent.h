#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "GameFramework/SaveGame.h"
#include "InputCoreTypes.h"
#include "AnomaliaInputProfileComponent.generated.h"

class UInputComponent;
class UEnhancedInputComponent;
class UEnhancedInputLocalPlayerSubsystem;
class UInputMappingContext;
class UInputAction;
struct FInputActionValue;

UENUM(BlueprintType)
enum class EAnomaliaGlyphFamily : uint8 { Generic, PlayStation, Xbox };

/** Local machine/user preferences only. No gameplay RPC and no shared server configuration writes. */
UCLASS()
class ANOMALIAPRIMEVAL_API UAnomaliaControlPreferences : public USaveGame
{
    GENERATED_BODY()
public:
    UPROPERTY(SaveGame) int32 SchemaVersion=1;
    UPROPERTY(SaveGame) bool bAZERTY=true;
    UPROPERTY(SaveGame) TMap<FName,FKey> KeyboardActions;
    UPROPERTY(SaveGame) TMap<FName,FKey> GamepadActions;
    /** Explicit override. Generic never pretends that a vendor was detected. */
    UPROPERTY(SaveGame) EAnomaliaGlyphFamily GlyphFamily=EAnomaliaGlyphFamily::Generic;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FAnomaliaControlEvent,FName,Name,float,Value,bool,bPressed);

/** Runtime Enhanced Input contexts for the actual survivor/vehicle pawn, removed on unpossess. */
UCLASS(ClassGroup=(ANOMALIA),meta=(BlueprintSpawnableComponent))
class ANOMALIAPRIMEVAL_API UAnomaliaInputProfileComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UAnomaliaInputProfileComponent();
    bool Install(UInputComponent* Input,bool bVehicle);
    void Deactivate();
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    UPROPERTY(BlueprintAssignable,Category="ANOMALIA|Controls") FAnomaliaControlEvent OnControl;
    UFUNCTION(BlueprintCallable,Category="ANOMALIA|Controls") bool SetAZERTY(bool bEnabled);
    UFUNCTION(BlueprintCallable,Category="ANOMALIA|Controls") bool RemapAction(FName Action,FKey Key);
    UFUNCTION(BlueprintCallable,Category="ANOMALIA|Controls") bool SetGlyphFamily(EAnomaliaGlyphFamily Family);
    UFUNCTION(BlueprintPure,Category="ANOMALIA|Controls") FString GetKeyPrompt(FKey Key) const;
    UFUNCTION(BlueprintPure,Category="ANOMALIA|Controls") bool IsEnhancedInputActive() const {return MappingContext!=nullptr;}
    UFUNCTION(BlueprintPure,Category="ANOMALIA|Controls") bool IsAZERTY() const {return !Preferences||Preferences->bAZERTY;}
    static FKey LayoutKey(FName Axis,FKey Key,bool bAZERTY);
private:
    void AxisChanged(const FInputActionValue& Value,FName Name);
    void ButtonStarted(const FInputActionValue& Value,FName Name);
    void ButtonEnded(const FInputActionValue& Value,FName Name);
    bool SavePreferences();
    void LoadPreferences();
    UPROPERTY(Transient) TObjectPtr<UAnomaliaControlPreferences> Preferences;
    UPROPERTY(Transient) TObjectPtr<UInputMappingContext> MappingContext;
    UPROPERTY(Transient) TArray<TObjectPtr<UInputAction>> Actions;
    TWeakObjectPtr<UEnhancedInputComponent> BoundInput;
    TWeakObjectPtr<UEnhancedInputLocalPlayerSubsystem> BoundSubsystem;
    TArray<uint32> BindingHandles;
    TArray<FName> ActiveButtonNames;
    TArray<FName> ActiveAxisNames;
    FString SaveSlot;
    bool bVehicleContext=false;
    bool bSaveAllowed=true;
};
