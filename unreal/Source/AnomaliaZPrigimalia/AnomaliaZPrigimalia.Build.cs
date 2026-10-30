using UnrealBuildTool;
public class AnomaliaZPrigimalia : ModuleRules
{
    public AnomaliaZPrigimalia(ReadOnlyTargetRules Target) : base(Target)
    {
        string Stamp = System.IO.Path.GetFullPath(System.IO.Path.Combine(ModuleDirectory, "../../Build/AnomaliaZPrigimaliaSourceCommit.generated.txt"));
        ExternalDependencies.Add(Stamp);
        string Commit = System.IO.File.Exists(Stamp) ? System.IO.File.ReadAllText(Stamp).Trim() : "local";
        if (!System.Text.RegularExpressions.Regex.IsMatch(Commit, "^[0-9a-f]{40}$")) Commit = "local";
        PrivateDefinitions.Add("ANOMALIA_BUILD_COMMIT=\"" + Commit + "\"");
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine", "InputCore", "EnhancedInput", "UMG", "Slate", "SlateCore", "Json", "JsonUtilities", "ChaosVehicles" });
        // FUniqueNetIdRepl / FUniqueNetIdWrapper::ToString() used for per-player persistence.
        PrivateDependencyModuleNames.Add("CoreOnline");
        PrivateDependencyModuleNames.Add("PhysicsCore");
        // MoviePlayer renders rotating user-provided loading artwork during map travel.
        PrivateDependencyModuleNames.Add("MoviePlayer");
        if (Target.bBuildEditor) PrivateDependencyModuleNames.AddRange(new string[] { "UnrealEd", "Landscape" });
    }
}
