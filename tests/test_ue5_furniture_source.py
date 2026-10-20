"""Source boundary guards only. UE compilation, physics and RPC execution are not tested here."""
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'unreal/Source/AnomaliaPrimeval'

class FurnitureSourceGuards(unittest.TestCase):
    def test_client_rpc_cannot_choose_an_owner_or_server(self):
        header = (SOURCE / 'AnomaliaFurnitureComponent.h').read_text()
        rpc = header.split('void ServerRequest(', 1)[1].split(');', 1)[0]
        self.assertNotIn('OwnerId', rpc)
        self.assertNotIn('ServerId', rpc)
        self.assertNotIn('Controller', rpc)
        source = (SOURCE / 'AnomaliaFurnitureSubsystem.cpp').read_text()
        self.assertIn('Rules->GetFurnitureOwnerId(Caller->GetController())', source)
        self.assertIn('Caller->GetWorld() != GetWorld()', source)
        self.assertIn('!Rules->bEnableFurniturePrototype', source)

    def test_file_scope_and_atomic_transaction_order(self):
        source = (SOURCE / 'AnomaliaFurnitureSubsystem.cpp').read_text()
        self.assertIn('TEXT("Servers"), ServerId', source)
        self.assertIn('TEXT("Construction"), TEXT("world.json")', source)
        self.assertIn('Scope != ServerId', source)
        self.assertIn('Current != LoadedRaw', source)
        self.assertIn('MakeShared<FJsonObject>(*SavedRoot)', source)
        self.assertIn('MakeShared<FJsonObject>(**Old)', source)
        execute = source.split('bool UAnomaliaFurnitureSubsystem::Execute(', 1)[1]
        self.assertLess(execute.index('if (!Persist(Candidate, Error))'), execute.index('Layout = std::move(Candidate)'))
        self.assertIn('ValidateChangedPose(Caller', execute)

    def test_actor_identity_and_movement_are_replicated(self):
        source = (SOURCE / 'AnomaliaHomesteadStation.cpp').read_text()
        self.assertIn('SetReplicateMovement(true)', source)
        self.assertIn('SetMobility(EComponentMobility::Movable)', source)
        self.assertIn('DOREPLIFETIME(AAnomaliaHomesteadStation, PlacementId)', source)
        survivor = (SOURCE / 'AnomaliaSurvivor.cpp').read_text()
        self.assertIn('FurnitureComponent->BindInput(Input)', survivor)

    def test_offline_identity_fallback_cannot_apply_to_multiplayer(self):
        source = (SOURCE / 'AnomaliaGameMode.cpp').read_text()
        identity = source.split('FString AAnomaliaGameMode::GetPersistentPlayerId(', 1)[1].split('\n}', 1)[0]
        self.assertIn('GetNetMode() == NM_Standalone && Controller->IsLocalController()', identity)
        self.assertIn('if (!NetId.IsValid()) return FString();', identity)
        self.assertIn('FSHA1::HashBuffer', identity)
