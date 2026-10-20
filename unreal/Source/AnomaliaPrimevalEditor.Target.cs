using UnrealBuildTool;
using System.Collections.Generic;
public class AnomaliaPrimevalEditorTarget : TargetRules
{
    public AnomaliaPrimevalEditorTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Editor;
        // UE5.8 installed editor shares build products with UnrealEditor: use current compatible defaults.
        DefaultBuildSettings = BuildSettingsVersion.V6;
        ExtraModuleNames.Add("AnomaliaPrimeval");
    }
}
