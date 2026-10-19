import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HEADER = (ROOT / "unreal/Source/AnomaliaPrimeval/AnomaliaInventoryComponent.h").read_text(encoding="utf-8")
SOURCE = (ROOT / "unreal/Source/AnomaliaPrimeval/AnomaliaInventoryComponent.cpp").read_text(encoding="utf-8")
SURVIVOR_HEADER = (ROOT / "unreal/Source/AnomaliaPrimeval/AnomaliaSurvivor.h").read_text(encoding="utf-8")
SURVIVOR_SOURCE = (ROOT / "unreal/Source/AnomaliaPrimeval/AnomaliaSurvivor.cpp").read_text(encoding="utf-8")
WIDGET_HEADER = (ROOT / "unreal/Source/AnomaliaPrimeval/AnomaliaInventoryWidget.h").read_text(encoding="utf-8")
WIDGET_SOURCE = (ROOT / "unreal/Source/AnomaliaPrimeval/AnomaliaInventoryWidget.cpp").read_text(encoding="utf-8")
INPUT_INI = (ROOT / "unreal/Config/DefaultInput.ini").read_text(encoding="utf-8")


class UE5InventorySourceTests(unittest.TestCase):
    def test_replicated_stack_model_and_core_operations_exist(self):
        self.assertIn("USTRUCT(BlueprintType)\nstruct FAnomaliaInventoryStack", HEADER)
        self.assertIn("ReplicatedUsing=OnRep_Stacks", HEADER)
        for operation in ("TryAddItem", "TryRemoveItem", "TryMoveStack", "TrySplitStack", "TryMergeStacks", "GetCurrentWeightKg"):
            with self.subTest(operation=operation):
                self.assertIn(operation, HEADER)
                self.assertIn(f"UAnomaliaInventoryComponent::{operation}", SOURCE)

    def test_mutations_require_server_authority_and_invalid_add_is_atomic(self):
        for operation in ("ConfigureCompartment", "TryAddItem", "TryMoveStack", "TrySplitStack", "TryMergeStacks"):
            with self.subTest(operation=operation):
                begin = SOURCE.index(f"bool UAnomaliaInventoryComponent::{operation}(")
                body = SOURCE[begin:SOURCE.find("\n}\n", begin) + 3]
                self.assertIn("GetOwner()->HasAuthority()", body)
        self.assertIn("GetCurrentWeightKg() + ItemWeight * Count > WeightCapacityKg", SOURCE)
        self.assertIn("if (!FindPlacement(Candidate, NewStack)) return false;", SOURCE)
        self.assertIn("if (Available < Count) return false;", SOURCE)
        self.assertIn("Commit(MoveTemp(Candidate));", SOURCE)

    def test_catalogue_matches_existing_item_ids_and_container_bounds(self):
        for item_id in ("water", "food", "bandage", "wood", "stone", "rifle_ammo", "pistol", "rifle", "fishing_rod", "saddle"):
            with self.subTest(item=item_id):
                self.assertIn(f'TEXT("{item_id}")', SOURCE)
        self.assertIn("Width > 12", SOURCE)
        self.assertIn("Height > 20", SOURCE)
        self.assertIn("Compartments.Add(Pockets)", SOURCE)
        self.assertIn("ReplicatedUsing=OnRep_Compartments", HEADER)
        self.assertIn("DOREPLIFETIME(UAnomaliaInventoryComponent, Compartments)", SOURCE)
        self.assertIn("Width < Existing->Width", SOURCE)

    def test_every_legacy_item_definition_has_a_weight_entry(self):
        systems = (ROOT / "src/systems.js").read_text(encoding="utf-8")
        definitions = systems.split("export const ITEM_DEFS={", 1)[1].split("\n};", 1)[0]
        legacy_ids = set(re.findall(r"^\s*([a-zA-Z_][a-zA-Z_0-9]*):\{label:", definitions, re.M))
        weight_table = SOURCE.split("static const TMap<FName, float> Weights = {", 1)[1].split("\n    };", 1)[0]
        ue_ids = set(re.findall(r'TEXT\("([a-zA-Z_][a-zA-Z_0-9]*)"\)', weight_table))
        self.assertEqual(ue_ids, legacy_ids)

    def test_inventory_component_is_attached_to_every_survivor(self):
        self.assertIn("TObjectPtr<UAnomaliaInventoryComponent> InventoryComponent", SURVIVOR_HEADER)
        self.assertIn('CreateDefaultSubobject<UAnomaliaInventoryComponent>(TEXT("InventoryComponent"))', SURVIVOR_SOURCE)

    def test_client_reorganization_routes_through_server_rpcs(self):
        for operation in ("MoveStack", "SplitStack", "MergeStacks"):
            with self.subTest(operation=operation):
                self.assertIn(f"Request{operation}", HEADER)
                self.assertIn(f"ServerRequest{operation}", HEADER)
                self.assertIn(f"ServerRequest{operation}_Implementation", SOURCE)
        self.assertNotIn("ServerRequestAddItem", HEADER)

    def test_inventory_has_native_umg_screen_and_i_key_toggle(self):
        self.assertIn("UAnomaliaInventoryWidget : public UUserWidget", WIDGET_HEADER)
        self.assertIn('Input->BindAction(TEXT("Inventory"), IE_Pressed, this, &AAnomaliaSurvivor::InputInventory)', SURVIVOR_SOURCE)
        self.assertIn('ActionName="Inventory",Key=I', INPUT_INI)
        self.assertIn("CreateWidget<UAnomaliaInventoryWidget>", SURVIVOR_SOURCE)
        for action in ("MoveToHands", "SplitHalf", "Merge"):
            with self.subTest(action=action):
                self.assertIn(f"EAnomaliaInventoryAction::{action}", WIDGET_SOURCE)
        self.assertIn("OnInventoryUpdated.AddDynamic", WIDGET_SOURCE)


if __name__ == "__main__":
    unittest.main()
