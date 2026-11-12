#include "AnomaliaCityBlock.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInterface.h"

AAnomaliaCityBlock::AAnomaliaCityBlock()
{
    PrimaryActorTick.bCanEverTick=false;
    CityRoot=CreateDefaultSubobject<USceneComponent>(TEXT("CityRoot"));
    SetRootComponent(CityRoot);CityRoot->SetMobility(EComponentMobility::Static);
}
void AAnomaliaCityBlock::OnConstruction(const FTransform& Transform)
{Super::OnConstruction(Transform);RebuildCity();}
void AAnomaliaCityBlock::BeginPlay()
{Super::BeginPlay();RebuildCity();}
int32 AAnomaliaCityBlock::GetOriginalInstanceCount() const
{int32 Count=0;for(const auto& Batch:Batches)Count+=Batch.Instances.Num();return Count;}
void AAnomaliaCityBlock::RebuildCity()
{
    for(const auto& Reference:GeneratedComponents)if(auto* Component=Reference.Get()){RemoveInstanceComponent(Component);Component->DestroyComponent();}
    GeneratedComponents.Reset();
    auto Configure=[this](UStaticMeshComponent* Component,const FAnomaliaCityMeshBatch& Batch)
    {
        Component->SetupAttachment(CityRoot);Component->SetMobility(EComponentMobility::Static);
        Component->SetStaticMesh(Batch.Mesh);Component->SetCollisionObjectType(ECC_WorldStatic);
        Component->SetCollisionEnabled(Batch.bCollision?ECollisionEnabled::QueryAndPhysics:ECollisionEnabled::NoCollision);
        Component->SetVisibility(Batch.bVisible);Component->SetHiddenInGame(!Batch.bVisible);
        Component->SetCollisionResponseToAllChannels(ECR_Block);Component->SetCanEverAffectNavigation(false);
        for(int32 Index=0;Index<Batch.Materials.Num();++Index)if(Batch.Materials[Index])Component->SetMaterial(Index,Batch.Materials[Index]);
        AddInstanceComponent(Component);GeneratedComponents.Add(Component);
    };
    for(const auto& Batch:Batches)
    {
        if(!Batch.Mesh || Batch.Instances.IsEmpty())continue;
        TArray<FTransform> Positive;
        for(const auto& Transform:Batch.Instances)
        {
            if(Transform.ContainsNaN() || Transform.GetScale3D().GetAbsMin()<SMALL_NUMBER)continue;
            const FVector Scale=Transform.GetScale3D();
            if(Scale.X*Scale.Y*Scale.Z>0){Positive.Add(Transform);continue;}
            // A separate component preserves mirrored source winding without
            // mixing opposite handedness in a single instanced draw call.
            auto* Component=NewObject<UStaticMeshComponent>(this,NAME_None,RF_Transient);
            Configure(Component,Batch);Component->SetRelativeTransform(Transform);Component->RegisterComponent();
        }
        if(!Positive.IsEmpty())
        {
            auto* Component=NewObject<UHierarchicalInstancedStaticMeshComponent>(this,NAME_None,RF_Transient);
            Configure(Component,Batch);Component->AddInstances(Positive,false,false,false);Component->RegisterComponent();
        }
    }
}
