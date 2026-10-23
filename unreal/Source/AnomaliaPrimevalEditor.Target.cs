using UnrealBuildTool;
using System.Collections.Generic;
public class AnomaliaPrimevalEditorTarget : TargetRules
{
    public AnomaliaPrimevalEditorTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Editor;
        // UE5.8 installed editor shares build products with UnrealEditor: use the requested V7 target defaults.
        DefaultBuildSettings = BuildSettingsVersion.V7;
        ExtraModuleNames.Add("AnomaliaPrimeval");
    }
}
