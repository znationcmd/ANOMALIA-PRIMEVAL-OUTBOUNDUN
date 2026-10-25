using UnrealBuildTool;
public class AnomaliaPrimeval : ModuleRules
{
    public AnomaliaPrimeval(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine", "InputCore", "EnhancedInput", "UMG", "Slate", "SlateCore", "Json", "JsonUtilities", "ChaosVehicles" });
        // FUniqueNetIdRepl / FUniqueNetIdWrapper::ToString() used for per-player persistence.
        PrivateDependencyModuleNames.Add("CoreOnline");
        if (Target.bBuildEditor) PrivateDependencyModuleNames.AddRange(new string[] { "UnrealEd", "Landscape" });
    }
}

