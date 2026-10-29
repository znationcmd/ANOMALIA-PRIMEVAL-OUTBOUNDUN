#include "../AnomaliaInputProfileComponent.h"
#include "Misc/AutomationTest.h"
#include "Misc/Guid.h"
#include "Kismet/GameplayStatics.h"

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaControlLayoutTest,"Anomalia.Controls.Layout",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FAnomaliaControlLayoutTest::RunTest(const FString&)
{
    using Profile=UAnomaliaInputProfileComponent;
    TestEqual(TEXT("AZERTY forward converts W to Z"),Profile::LayoutKey(TEXT("MoveForward"),EKeys::W,true),EKeys::Z);
    TestEqual(TEXT("AZERTY left converts A to Q"),Profile::LayoutKey(TEXT("MoveRight"),EKeys::A,true),EKeys::Q);
    TestEqual(TEXT("QWERTY forward converts Z to W"),Profile::LayoutKey(TEXT("MoveForward"),EKeys::Z,false),EKeys::W);
    TestEqual(TEXT("QWERTY left converts Q to A"),Profile::LayoutKey(TEXT("MoveRight"),EKeys::Q,false),EKeys::A);
    TestEqual(TEXT("Mouse axis remains unchanged"),Profile::LayoutKey(TEXT("Turn"),EKeys::MouseX,false),EKeys::MouseX);
    TestEqual(TEXT("Analog left stick remains unchanged"),Profile::LayoutKey(TEXT("MoveForward"),EKeys::Gamepad_LeftY,false),EKeys::Gamepad_LeftY);
    TestEqual(TEXT("Custom movement key remains unchanged"),Profile::LayoutKey(TEXT("MoveForward"),EKeys::Up,true),EKeys::Up);
    TestEqual(TEXT("Action keys are not converted as movement keys"),Profile::LayoutKey(TEXT("Interact"),EKeys::A,true),EKeys::A);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaControlSaveTest,"Anomalia.Controls.LocalPreferencesPersistence",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FAnomaliaControlSaveTest::RunTest(const FString&)
{
    const FString Slot=TEXT("ANOMALIA_Controls_Automation_")+FGuid::NewGuid().ToString(EGuidFormats::Digits);
    if(UGameplayStatics::DoesSaveGameExist(Slot,0)){AddError(TEXT("Unexpected existing isolated slot preserved"));return false;}
    auto* Preferences=NewObject<UAnomaliaControlPreferences>();
    Preferences->bAZERTY=false;Preferences->GlyphFamily=EAnomaliaGlyphFamily::PlayStation;
    Preferences->KeyboardActions.Add(TEXT("Interact"),EKeys::F);
    Preferences->GamepadActions.Add(TEXT("Inventory"),EKeys::Gamepad_Special_Left);
    if(!TestTrue(TEXT("Actual local preference save succeeds"),UGameplayStatics::SaveGameToSlot(Preferences,Slot,0)))return false;
    auto* Loaded=Cast<UAnomaliaControlPreferences>(UGameplayStatics::LoadGameFromSlot(Slot,0));
    TestNotNull(TEXT("Settings load as the expected save type"),Loaded);
    if(Loaded)
    {
        TestEqual(TEXT("Schema survives restart"),Loaded->SchemaVersion,1);
        TestFalse(TEXT("QWERTY preference survives restart"),Loaded->bAZERTY);
        TestTrue(TEXT("Explicit glyph preference survives restart"),Loaded->GlyphFamily==EAnomaliaGlyphFamily::PlayStation);
        TestTrue(TEXT("Keyboard override survives restart"),Loaded->KeyboardActions.FindRef(TEXT("Interact"))==EKeys::F);
        TestTrue(TEXT("Controller override survives restart"),Loaded->GamepadActions.FindRef(TEXT("Inventory"))==EKeys::Gamepad_Special_Left);
    }
    TestTrue(TEXT("Only this test-created save is removed"),UGameplayStatics::DeleteGameInSlot(Slot,0));
    return true;
}
#endif
