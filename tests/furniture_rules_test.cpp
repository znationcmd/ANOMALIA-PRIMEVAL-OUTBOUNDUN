#include "Furniture/AnomaliaFurnitureRules.h"
#include <cassert>
#include <limits>
#include <iostream>
using namespace AnomaliaFurniture;
int main()
{
    Layout L;
    Record Bed{"bed-1", "alice", "bed", {100, 200, 50, 0}};
    assert(L.Place("alice", Bed));
    assert(!L.Place("bob", Bed));
    assert(!L.Move("bob", "bed-1", {0, 0, 50, 0}));
    assert(!L.Remove("bob", "bed-1", true));
    assert(!L.Remove("alice", "bed-1", false));
    assert(L.Find("bed-1")->Owner == "alice");
    assert(L.Move("alice", "bed-1", {300, 400, 50, 90}));
    assert(!L.Move("alice", "bed-1", {0, 0, 0, std::numeric_limits<double>::infinity()}));
    assert(!L.Move("alice", "bed-1", {2400001, 0, 0, 0}));
    assert(L.Undo("alice")); assert(L.Find("bed-1")->Transform.X == 100);
    assert(L.Redo("alice")); assert(L.Find("bed-1")->Transform.Yaw == 90);
    assert(L.Remove("alice", "bed-1", true)); assert(!L.Find("bed-1"));
    assert(L.Undo("alice")); assert(L.Find("bed-1"));
    assert(L.Move("alice", "bed-1", {500, 0, 50, 180}));
    assert(!L.Redo("alice"));
    assert(L.Place("bob", {"chair-b", "bob", "chair", {0, 0, 50, 0}}));
    assert(L.Undo("alice")); assert(L.Find("chair-b"));
    Layout OtherServer;
    assert(!OtherServer.Find("bed-1")); assert(!OtherServer.Undo("alice"));
    // Invalid imports cannot partially replace an existing layout.
    assert(!L.Load({Bed, Bed})); assert(L.Find("chair-b"));
    assert(!L.Load({{"evil", "alice", "unknown-class", {}}})); assert(L.Find("chair-b"));
    assert(!L.Place("../bob", {"a", "../bob", "bed", {}}));
    assert(!L.Place("alice", {"bad", "alice", "bed", {0, std::numeric_limits<double>::quiet_NaN(), 0, 0}}));
    // Simulate the adapter preparing a transaction then failing persistence: committed state is unchanged.
    Layout Candidate = L;
    assert(Candidate.Remove("bob", "chair-b", true)); assert(L.Find("chair-b"));
    // Save/reload round trip deliberately resets session undo history.
    std::vector<Record> Saved; for (const auto& Pair : L.All()) Saved.push_back(Pair.second);
    Layout Reloaded; assert(Reloaded.Load(Saved)); assert(Reloaded.All() == L.All());
    assert(!Reloaded.Undo("alice"));
    Layout Full;
    for (std::size_t I = 0; I < Layout::MaxObjects; ++I)
        assert(Full.Place("alice", {"item-" + std::to_string(I), "alice", "chair", {}}));
    assert(!Full.Place("bob", {"extra", "bob", "chair", {}}));
    for (std::size_t I = 0; I < Layout::MaxHistory; ++I) assert(Full.Undo("alice"));
    assert(!Full.Undo("alice"));
    std::cout << "Furniture transaction rules passed (portable C++, not Unreal runtime).\n";
}
