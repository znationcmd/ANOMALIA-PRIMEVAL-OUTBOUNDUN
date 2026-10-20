#pragma once
// Engine-independent transaction rules shared by the UE server adapter and native C++ tests.
#include <algorithm>
#include <cmath>
#include <map>
#include <optional>
#include <string>
#include <vector>

namespace AnomaliaFurniture
{
struct Pose
{
    double X = 0, Y = 0, Z = 0, Yaw = 0;
    bool operator==(const Pose& Other) const
    { return X == Other.X && Y == Other.Y && Z == Other.Z && Yaw == Other.Yaw; }
};
struct Record
{
    std::string Id, Owner, Type;
    Pose Transform;
    bool operator==(const Record& Other) const
    { return Id == Other.Id && Owner == Other.Owner && Type == Other.Type && Transform == Other.Transform; }
};
struct Change { std::optional<Record> Before, After; };

inline bool SafeId(const std::string& Id)
{
    if (Id.empty() || Id.size() > 64) return false;
    for (const unsigned char C : Id)
        if (!((C >= 'a' && C <= 'z') || (C >= 'A' && C <= 'Z') ||
              (C >= '0' && C <= '9') || C == '-' || C == '_')) return false;
    return true;
}
inline bool ValidPose(const Pose& P)
{
    return std::isfinite(P.X) && std::isfinite(P.Y) && std::isfinite(P.Z) && std::isfinite(P.Yaw) &&
        std::abs(P.X) <= 2400000 && std::abs(P.Y) <= 2400000 &&
        std::abs(P.Z) <= 2400000 && std::abs(P.Yaw) <= 360;
}
inline bool AllowedType(const std::string& Type)
{
    static const std::vector<std::string> Types = {"bed", "table", "chair", "sofa", "wardrobe",
        "kitchen", "lamp", "beehive", "doghouse", "barn", "fence", "tractor_shed"};
    return std::find(Types.begin(), Types.end(), Type) != Types.end();
}
class Layout
{
public:
    static constexpr std::size_t MaxObjects = 256, MaxHistory = 32;
    const std::map<std::string, Record>& All() const { return Objects; }
    const std::string& LastError() const { return Error; }
    const Record* Find(const std::string& Id) const
    { auto It = Objects.find(Id); return It == Objects.end() ? nullptr : &It->second; }

    bool Load(const std::vector<Record>& Records)
    {
        std::map<std::string, Record> Candidate;
        if (Records.size() > MaxObjects) return Fail("Too many objects");
        for (const Record& R : Records)
            if (!Valid(R) || !Candidate.emplace(R.Id, R).second) return Fail("Invalid or duplicate object");
        Objects = std::move(Candidate);
        UndoHistory.clear(); RedoHistory.clear(); Error.clear();
        return true;
    }
    bool Place(const std::string& Actor, const Record& R)
    {
        if (!SafeId(Actor) || R.Owner != Actor) return Fail("Owner mismatch");
        if (!Valid(R) || Objects.size() >= MaxObjects || Find(R.Id)) return Fail("Invalid placement");
        Commit(Actor, {std::nullopt, R}); return true;
    }
    bool Move(const std::string& Actor, const std::string& Id, const Pose& P)
    {
        const Record* Existing = Owned(Actor, Id);
        if (!Existing || !ValidPose(P)) return Fail("Invalid move or permission denied");
        Record Changed = *Existing; Changed.Transform = P;
        if (Changed == *Existing) return Fail("Nothing changed");
        Commit(Actor, {*Existing, Changed}); return true;
    }
    bool Remove(const std::string& Actor, const std::string& Id, bool Confirmed)
    {
        if (!Confirmed) return Fail("Removal requires confirmation");
        const Record* Existing = Owned(Actor, Id);
        if (!Existing) return Fail("Permission denied");
        Commit(Actor, {*Existing, std::nullopt}); return true;
    }
    bool Undo(const std::string& Actor) { return Replay(Actor, UndoHistory, RedoHistory, true); }
    bool Redo(const std::string& Actor) { return Replay(Actor, RedoHistory, UndoHistory, false); }

private:
    using Histories = std::map<std::string, std::vector<Change>>;
    std::map<std::string, Record> Objects;
    Histories UndoHistory, RedoHistory;
    std::string Error;
    bool Fail(const char* Message) { Error = Message; return false; }
    static bool Valid(const Record& R)
    { return SafeId(R.Id) && SafeId(R.Owner) && AllowedType(R.Type) && ValidPose(R.Transform); }
    const Record* Owned(const std::string& Actor, const std::string& Id) const
    { const Record* R = Find(Id); return SafeId(Actor) && R && R->Owner == Actor ? R : nullptr; }
    static void Push(std::vector<Change>& Stack, const Change& C)
    { if (Stack.size() == MaxHistory) Stack.erase(Stack.begin()); Stack.push_back(C); }
    void Apply(const std::optional<Record>& R, const std::string& Id)
    { if (R) Objects[Id] = *R; else Objects.erase(Id); }
    void Commit(const std::string& Actor, const Change& C)
    {
        const std::string Id = C.After ? C.After->Id : C.Before->Id;
        Apply(C.After, Id); Push(UndoHistory[Actor], C); RedoHistory[Actor].clear(); Error.clear();
    }
    bool Replay(const std::string& Actor, Histories& From, Histories& To, bool Reverse)
    {
        auto It = From.find(Actor);
        if (!SafeId(Actor) || It == From.end() || It->second.empty()) return Fail("History empty");
        const Change C = It->second.back();
        const auto& Expected = Reverse ? C.After : C.Before;
        const auto& Target = Reverse ? C.Before : C.After;
        const std::string Id = C.After ? C.After->Id : C.Before->Id;
        const Record* Current = Find(Id);
        if ((Expected && (!Current || !(*Current == *Expected))) || (!Expected && Current))
            return Fail("History conflicts with current world");
        if ((Target && Target->Owner != Actor) || (Expected && Expected->Owner != Actor))
            return Fail("Permission denied");
        if (Target && !Current && Objects.size() >= MaxObjects) return Fail("World capacity reached");
        Apply(Target, Id); It->second.pop_back(); Push(To[Actor], C); Error.clear(); return true;
    }
};
}
