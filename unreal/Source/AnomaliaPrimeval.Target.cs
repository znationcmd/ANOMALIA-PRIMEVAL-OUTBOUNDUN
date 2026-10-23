using UnrealBuildTool;
using System.Collections.Generic;
public class AnomaliaPrimevalTarget : TargetRules
{
    public AnomaliaPrimevalTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Game;
        // Keep game and editor targets on the the V7 target defaults requested by the user's UE5.8 installation.
        DefaultBuildSettings = BuildSettingsVersion.V7;
        ExtraModuleNames.Add("AnomaliaPrimeval");
    }
}
