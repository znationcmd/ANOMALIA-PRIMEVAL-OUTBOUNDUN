#include "AnomaliaInputProfileComponent.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "InputAction.h"
#include "InputActionValue.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"
#include "GameFramework/InputSettings.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "Engine/LocalPlayer.h"
#include "Kismet/GameplayStatics.h"

UAnomaliaInputProfileComponent::UAnomaliaInputProfileComponent(){PrimaryComponentTick.bCanEverTick=false;}
FKey UAnomaliaInputProfileComponent::LayoutKey(FName Axis,FKey Key,bool bAZERTY)
{
    if(Axis==TEXT("MoveForward")&&(Key==EKeys::W||Key==EKeys::Z))return bAZERTY?EKeys::Z:EKeys::W;
    if(Axis==TEXT("MoveRight")&&(Key==EKeys::A||Key==EKeys::Q))return bAZERTY?EKeys::Q:EKeys::A;
    return Key;
}
void UAnomaliaInputProfileComponent::LoadPreferences()
{
    if(Preferences)return;
    auto* Pawn=Cast<APawn>(GetOwner());auto* PC=Pawn?Cast<APlayerController>(Pawn->GetController()):nullptr;
    auto* LP=PC?PC->GetLocalPlayer():nullptr;if(!LP)return;
    SaveSlot=FString::Printf(TEXT("ANOMALIA_Controls_LocalPlayer_%d"),LP->GetControllerId());
    Preferences=Cast<UAnomaliaControlPreferences>(UGameplayStatics::LoadGameFromSlot(SaveSlot,0));
    if(Preferences&&Preferences->SchemaVersion!=1){Preferences=nullptr;bSaveAllowed=false;}
    if(!Preferences)
    {
        // Never replace an unknown/incompatible save with a newly created settings object.
        if(UGameplayStatics::DoesSaveGameExist(SaveSlot,0))bSaveAllowed=false;
        Preferences=NewObject<UAnomaliaControlPreferences>(this);
    }
}
bool UAnomaliaInputProfileComponent::SavePreferences()
{return bSaveAllowed&&Preferences&&!SaveSlot.IsEmpty()&&UGameplayStatics::SaveGameToSlot(Preferences,SaveSlot,0);}
void UAnomaliaInputProfileComponent::Deactivate()
{
    if(auto* Subsystem=BoundSubsystem.Get();Subsystem&&MappingContext)Subsystem->RemoveMappingContext(MappingContext);
    if(auto* Input=BoundInput.Get())for(uint32 Handle:BindingHandles)Input->RemoveBindingByHandle(Handle);
    BindingHandles.Reset();Actions.Reset();MappingContext=nullptr;BoundInput.Reset();BoundSubsystem.Reset();
}
void UAnomaliaInputProfileComponent::EndPlay(const EEndPlayReason::Type Reason){Deactivate();Super::EndPlay(Reason);}
bool UAnomaliaInputProfileComponent::Install(UInputComponent* Input,bool bVehicle)
{
    auto* Enhanced=Cast<UEnhancedInputComponent>(Input);
    auto* Pawn=Cast<APawn>(GetOwner());auto* PC=Pawn?Cast<APlayerController>(Pawn->GetController()):nullptr;
    auto* LP=PC?PC->GetLocalPlayer():nullptr;
    auto* Subsystem=LP?LP->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>():nullptr;
    if(!Enhanced||!Subsystem)return false;
    const TArray<FName> AxisNames=bVehicle?
        TArray<FName>{TEXT("MoveForward"),TEXT("MoveRight"),TEXT("Turn"),TEXT("LookUp"),TEXT("TurnRate"),TEXT("LookUpRate"),TEXT("VehiclePitch"),TEXT("VehicleRoll"),TEXT("VehicleVertical"),TEXT("VehicleBrake")}:
        TArray<FName>{TEXT("MoveForward"),TEXT("MoveRight"),TEXT("Turn"),TEXT("LookUp"),TEXT("TurnRate"),TEXT("LookUpRate")};
    TArray<FName> ButtonNames={TEXT("Interact"),TEXT("Pause"),TEXT("VehicleCamera")};
    if(!bVehicle)
    {
        ButtonNames.Append({TEXT("Jump"),TEXT("Inventory"),TEXT("MeleeAttack"),TEXT("Sprint"),TEXT("Rest"),TEXT("TacticalCrouch"),TEXT("PaceMode"),TEXT("PaceUp"),TEXT("PaceDown")});
        for(int32 I=0;I<10;++I)ButtonNames.Add(FName(*FString::Printf(TEXT("Quickbar%d"),I)));
    }
    auto* Settings=UInputSettings::GetInputSettings();
    if(!Settings)return false;
    // Existing user-defined modifier chords need their legacy handler until chord actions are authored.
    for(const auto& M:Settings->GetActionMappings())
        if(ButtonNames.Contains(M.ActionName)&&(M.bShift||M.bCtrl||M.bAlt||M.bCmd))return false;
    Deactivate();LoadPreferences();if(!Preferences)return false;
    BoundInput=Enhanced;BoundSubsystem=Subsystem;bVehicleContext=bVehicle;ActiveButtonNames=ButtonNames;ActiveAxisNames=AxisNames;
    MappingContext=NewObject<UInputMappingContext>(this);
    for(const FName Name:AxisNames)
    {
        auto* Action=NewObject<UInputAction>(this);Action->ValueType=EInputActionValueType::Axis1D;Action->bConsumeInput=false;Actions.Add(Action);
        TArray<FInputAxisKeyMapping> Mappings;Settings->GetAxisMappingByName(Name,Mappings);TSet<FString> Seen;
        for(const auto& M:Mappings)
        {
            const FKey Key=LayoutKey(Name,M.Key,Preferences->bAZERTY);
            const FString Identity=Key.ToString()+FString::SanitizeFloat(M.Scale);if(Seen.Contains(Identity))continue;Seen.Add(Identity);
            auto& Mapping=MappingContext->MapKey(Action,Key);
            if(Key.IsGamepadKey()){auto* DeadZone=NewObject<UInputModifierDeadZone>(MappingContext);DeadZone->LowerThreshold=.15f;Mapping.Modifiers.Add(DeadZone);}
            auto* Scalar=NewObject<UInputModifierScalar>(MappingContext);Scalar->Scalar=FVector(M.Scale,1,1);Mapping.Modifiers.Add(Scalar);
        }
        BindingHandles.Add(Enhanced->BindAction(Action,ETriggerEvent::Triggered,this,&UAnomaliaInputProfileComponent::AxisChanged,Name).GetHandle());
        BindingHandles.Add(Enhanced->BindAction(Action,ETriggerEvent::Completed,this,&UAnomaliaInputProfileComponent::AxisChanged,Name).GetHandle());
        BindingHandles.Add(Enhanced->BindAction(Action,ETriggerEvent::Canceled,this,&UAnomaliaInputProfileComponent::AxisChanged,Name).GetHandle());
    }
    for(const FName Name:ButtonNames)
    {
        auto* Action=NewObject<UInputAction>(this);Action->ValueType=EInputActionValueType::Boolean;Action->bConsumeInput=false;Actions.Add(Action);
        TArray<FInputActionKeyMapping> Mappings;Settings->GetActionMappingByName(Name,Mappings);TSet<FKey> Seen;
        for(const auto& M:Mappings)
        {
            const auto& Overrides=M.Key.IsGamepadKey()?Preferences->GamepadActions:Preferences->KeyboardActions;
            const FKey Key=Overrides.Contains(Name)?Overrides[Name]:M.Key;
            if(!Key.IsValid()||Seen.Contains(Key))continue;Seen.Add(Key);MappingContext->MapKey(Action,Key);
        }
        BindingHandles.Add(Enhanced->BindAction(Action,ETriggerEvent::Started,this,&UAnomaliaInputProfileComponent::ButtonStarted,Name).GetHandle());
        BindingHandles.Add(Enhanced->BindAction(Action,ETriggerEvent::Completed,this,&UAnomaliaInputProfileComponent::ButtonEnded,Name).GetHandle());
        BindingHandles.Add(Enhanced->BindAction(Action,ETriggerEvent::Canceled,this,&UAnomaliaInputProfileComponent::ButtonEnded,Name).GetHandle());
    }
    Subsystem->AddMappingContext(MappingContext,bVehicle?20:10);
    UE_LOG(LogTemp,Log,TEXT("ANOMALIA Enhanced Input active: %s %s"),bVehicle?TEXT("vehicle"):TEXT("survivor"),Preferences->bAZERTY?TEXT("AZERTY"):TEXT("QWERTY"));
    return true;
}
void UAnomaliaInputProfileComponent::AxisChanged(const FInputActionValue& Value,FName Name){OnControl.Broadcast(Name,Value.Get<float>(),false);}
void UAnomaliaInputProfileComponent::ButtonStarted(const FInputActionValue& Value,FName Name){OnControl.Broadcast(Name,1,true);}
void UAnomaliaInputProfileComponent::ButtonEnded(const FInputActionValue& Value,FName Name){OnControl.Broadcast(Name,0,false);}
bool UAnomaliaInputProfileComponent::SetAZERTY(bool Enabled)
{
    LoadPreferences();if(!Preferences)return false;const bool Before=Preferences->bAZERTY;Preferences->bAZERTY=Enabled;
    if(!SavePreferences()){Preferences->bAZERTY=Before;return false;}
    if(auto* Input=BoundInput.Get())return Install(Input,bVehicleContext);return true;
}
bool UAnomaliaInputProfileComponent::RemapAction(FName Action,FKey Key)
{
    LoadPreferences();if(!Preferences||!Key.IsValid()||Key.IsAxis1D()||Key.IsAxis2D()||Key.IsAxis3D())return false;
    // Only a real currently installed button action may be remapped.
    auto* Settings=UInputSettings::GetInputSettings();TArray<FInputActionKeyMapping> Mappings;Settings->GetActionMappingByName(Action,Mappings);
    if(Mappings.IsEmpty()||!ActiveButtonNames.Contains(Action))return false;
    // Reject collisions within this pawn context; vehicle and survivor profiles remain independent.
    for(const FName Other:ActiveButtonNames)
    {
        if(Other==Action)continue;
        TArray<FInputActionKeyMapping> OtherMappings;Settings->GetActionMappingByName(Other,OtherMappings);
        const auto& Existing=Key.IsGamepadKey()?Preferences->GamepadActions:Preferences->KeyboardActions;
        for(const auto& M:OtherMappings)
            if(M.Key.IsGamepadKey()==Key.IsGamepadKey() && (Existing.Contains(Other)?Existing[Other]:M.Key)==Key)return false;
    }
    for(const FName Axis:ActiveAxisNames)
    {
        TArray<FInputAxisKeyMapping> Axes;Settings->GetAxisMappingByName(Axis,Axes);
        for(const auto& M:Axes)if(LayoutKey(Axis,M.Key,Preferences->bAZERTY)==Key)return false;
    }
    auto& Overrides=Key.IsGamepadKey()?Preferences->GamepadActions:Preferences->KeyboardActions;
    const auto Before=Overrides;Overrides.Add(Action,Key);
    if(!SavePreferences()){Overrides=Before;return false;}
    if(auto* Input=BoundInput.Get())return Install(Input,bVehicleContext);return true;
}
bool UAnomaliaInputProfileComponent::SetGlyphFamily(EAnomaliaGlyphFamily Family)
{
    if(Family!=EAnomaliaGlyphFamily::Generic&&Family!=EAnomaliaGlyphFamily::PlayStation&&Family!=EAnomaliaGlyphFamily::Xbox)return false;
    LoadPreferences();if(!Preferences)return false;const auto Before=Preferences->GlyphFamily;Preferences->GlyphFamily=Family;
    if(!SavePreferences()){Preferences->GlyphFamily=Before;return false;}return true;
}
FString UAnomaliaInputProfileComponent::GetKeyPrompt(FKey Key) const
{
    if(!Key.IsGamepadKey()||!Preferences||Preferences->GlyphFamily==EAnomaliaGlyphFamily::Generic)return Key.GetDisplayName().ToString();
    const bool PS=Preferences->GlyphFamily==EAnomaliaGlyphFamily::PlayStation;
    if(Key==EKeys::Gamepad_FaceButton_Bottom)return PS?TEXT("Croix"):TEXT("A");
    if(Key==EKeys::Gamepad_FaceButton_Right)return PS?TEXT("Rond"):TEXT("B");
    if(Key==EKeys::Gamepad_FaceButton_Left)return PS?TEXT("Carré"):TEXT("X");
    if(Key==EKeys::Gamepad_FaceButton_Top)return PS?TEXT("Triangle"):TEXT("Y");
    if(Key==EKeys::Gamepad_LeftTrigger||Key==EKeys::Gamepad_LeftTriggerAxis)return PS?TEXT("L2"):TEXT("LT");
    if(Key==EKeys::Gamepad_RightTrigger||Key==EKeys::Gamepad_RightTriggerAxis)return PS?TEXT("R2"):TEXT("RT");
    if(Key==EKeys::Gamepad_LeftShoulder)return PS?TEXT("L1"):TEXT("LB");
    if(Key==EKeys::Gamepad_RightShoulder)return PS?TEXT("R1"):TEXT("RB");
    if(Key==EKeys::Gamepad_Special_Left)return PS?TEXT("Pavé tactile"):TEXT("Affichage");
    if(Key==EKeys::Gamepad_Special_Right)return PS?TEXT("Options"):TEXT("Menu");
    return Key.GetDisplayName().ToString();
}
