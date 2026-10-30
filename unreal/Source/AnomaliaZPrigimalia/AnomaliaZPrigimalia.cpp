#include "Modules/ModuleManager.h"
#include "MoviePlayer.h"
#include "ImageUtils.h"
#include "Engine/Texture2D.h"
#include "Misc/CoreDelegates.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformMisc.h"
#include "UObject/StrongObjectPtr.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Layout/SScaleBox.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/Images/SThrobber.h"
#include "Styling/SlateBrush.h"

// Four user-supplied images, rotating on successive Unreal map loads.
// Images are read from the user's own LOCALAPPDATA, never copied into a
// commercial release, never displayed on the startup main menu.
class FAnomaliaZPrigimaliaGameModule final : public FDefaultGameModuleImpl
{
    FDelegateHandle BeforeMapHandle;
    TStrongObjectPtr<UTexture2D> CurrentTexture;
    FSlateBrush CurrentBrush;

    static FString LoadingFolder()
    {
        return FPaths::Combine(
            FPlatformMisc::GetEnvironmentVariable(TEXT("LOCALAPPDATA")),
            TEXT("AnomaliaZPrigimalia"), TEXT("LoadingScreens"));
    }

    void ShowNextLoadingArt(const FString& MapName)
    {
        if (IsRunningDedicatedServer() || IsRunningCommandlet() || !IsMoviePlayerEnabled())
            return;
#if WITH_EDITOR
        if (GIsEditor) return;
#endif
        const FString Folder=LoadingFolder();
        static const TCHAR* Names[]={
            TEXT("loading-01.jpg"), TEXT("loading-02.jpg"),
            TEXT("loading-03.jpg"), TEXT("loading-04.jpg")
        };
        const FString Rotation=FPaths::Combine(Folder,TEXT("rotation.txt"));
        FString Previous;
        int32 Last=-1;
        if(FFileHelper::LoadFileToString(Previous,*Rotation))
        {
            const FString Trimmed=Previous.TrimStartAndEnd();
            if(Trimmed.IsNumeric()) Last=FCString::Atoi(*Trimmed);
        }
        for(int32 Offset=1;Offset<=4;++Offset)
        {
            const int32 Index=((Last+Offset)%4+4)%4;
            const FString ImagePath=FPaths::Combine(Folder,Names[Index]);
            if(!FPaths::FileExists(ImagePath))continue;
            if(IFileManager::Get().FileSize(*ImagePath)>8*1024*1024)continue;
            UTexture2D* Texture=FImageUtils::ImportFileAsTexture2D(ImagePath);
            if(!Texture)
            {
                UE_LOG(LogTemp,Warning,TEXT("PRIGIMALIA LOADING: invalid JPEG %s"),*ImagePath);
                continue;
            }
            CurrentTexture.Reset(Texture);
            CurrentBrush.SetResourceObject(CurrentTexture.Get());
            CurrentBrush.ImageSize=FVector2D(Texture->GetSizeX(),Texture->GetSizeY());
            const auto Content=SNew(SOverlay)
                +SOverlay::Slot()
                [
                    SNew(SScaleBox).Stretch(EStretch::ScaleToFill)
                    [
                        SNew(SImage).Image(&CurrentBrush)
                    ]
                ]
                +SOverlay::Slot().VAlign(VAlign_Bottom).Padding(FMargin(24.f))
                [
                    SNew(SBorder).BorderBackgroundColor(FLinearColor(.012f,.014f,.016f,.75f))
                    [
                        SNew(SHorizontalBox)
                        +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(FMargin(12.f))
                        [
                            SNew(SThrobber)
                        ]
                        +SHorizontalBox::Slot().FillWidth(1.f).VAlign(VAlign_Center).Padding(FMargin(8.f))
                        [
                            SNew(STextBlock).Text(FText::FromString(TEXT("ANOMALIA'Z PRIGIMALIA  ·  CHARGEMENT...")))
                        ]
                    ]
                ];
            FLoadingScreenAttributes Screen;
            Screen.bAutoCompleteWhenLoadingCompletes=true;
            Screen.bWaitForManualStop=false;
            Screen.MinimumLoadingScreenDisplayTime=.25f;
            Screen.WidgetLoadingScreen=Content;
            GetMoviePlayer()->SetupLoadingScreen(Screen);
            // Persist only after the image is proven readable. Keep the image
            // unchanged throughout this loading operation; next load advances.
            FFileHelper::SaveStringToFile(FString::FromInt(Index),*Rotation);
            UE_LOG(LogTemp,Display,TEXT("PRIGIMALIA_LOADING_IMAGE_SELECTED=%d MAP=%s"),Index+1,*MapName);
            return;
        }
        // No missing images or synthetic artwork: engine standard load UI.
        UE_LOG(LogTemp,Display,TEXT("PRIGIMALIA_LOADING_ART_NOT_INSTALLED: %s"),*Folder);
    }

public:
    virtual void StartupModule() override
    {
        FDefaultGameModuleImpl::StartupModule();
        if(!IsRunningDedicatedServer() && !IsRunningCommandlet())
            BeforeMapHandle=FCoreUObjectDelegates::PreLoadMap.AddRaw(
                this,&FAnomaliaZPrigimaliaGameModule::ShowNextLoadingArt);
    }
    virtual void ShutdownModule() override
    {
        if(BeforeMapHandle.IsValid())
            FCoreUObjectDelegates::PreLoadMap.Remove(BeforeMapHandle);
        CurrentTexture.Reset();
        FDefaultGameModuleImpl::ShutdownModule();
    }
};
IMPLEMENT_PRIMARY_GAME_MODULE(FAnomaliaZPrigimaliaGameModule, AnomaliaZPrigimalia, "AnomaliaZPrigimalia");
