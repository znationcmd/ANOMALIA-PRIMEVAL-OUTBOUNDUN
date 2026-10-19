using UnrealBuildTool;
using System.Collections.Generic;
public class AnomaliaPrimevalEditorTarget : TargetRules
{
    public AnomaliaPrimevalEditorTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Editor;
        DefaultBuildSettings = BuildSettingsVersion.V5;
        ExtraModuleNames.Add("AnomaliaPrimeval");
    }
}
