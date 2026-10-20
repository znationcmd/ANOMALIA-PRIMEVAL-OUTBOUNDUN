using UnrealBuildTool;
using System.Collections.Generic;
public class AnomaliaPrimevalTarget : TargetRules
{
    public AnomaliaPrimevalTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Game;
        // Keep game and editor targets on the UE5.8 compatible target defaults.
        DefaultBuildSettings = BuildSettingsVersion.V6;
        ExtraModuleNames.Add("AnomaliaPrimeval");
    }
}
