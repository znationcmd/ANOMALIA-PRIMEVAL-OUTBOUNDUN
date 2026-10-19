using UnrealBuildTool;
using System.Collections.Generic;
public class AnomaliaPrimevalTarget : TargetRules
{
    public AnomaliaPrimevalTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Game;
        DefaultBuildSettings = BuildSettingsVersion.V5;
        ExtraModuleNames.Add("AnomaliaPrimeval");
    }
}
