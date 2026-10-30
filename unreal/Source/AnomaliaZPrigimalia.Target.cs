using UnrealBuildTool;
using System.Collections.Generic;
public class AnomaliaZPrigimaliaTarget : TargetRules
{
    public AnomaliaZPrigimaliaTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Game;
        // Keep game and editor targets on the the V7 target defaults requested by the user's UE5.8 installation.
        DefaultBuildSettings = BuildSettingsVersion.V7;
        ExtraModuleNames.Add("AnomaliaZPrigimalia");
    }
}
