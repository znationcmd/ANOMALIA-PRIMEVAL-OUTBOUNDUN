import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
const read = name => readFileSync(new URL("../unreal/Content/AnomaliaZPrigimalia/Data/" + name, import.meta.url), "utf8");
const publicRead = name => readFileSync(new URL("../public/config/" + name, import.meta.url), "utf8");
const dataNames = [
  "loot_items_catalog.json",
  "rp_items_catalog.json",
  "loot_tiers.json",
  "loot_spawns.json",
  "rp_economy.json"
];
test("the Unreal native alpha carries all five authoritative live-game JSON resources byte-for-byte",()=>{
  for(const name of dataNames){
    const native=read(name);
    const original=publicRead(name);
    assert.equal(native, original, "Source-data drift: "+name);
    assert.equal(JSON.parse(native).schemaVersion, 1, name);
  }
});
test("all real loot, RP items, tiers and economy definitions are preserved",()=>{
  const loot=JSON.parse(read("loot_items_catalog.json"));
  const rp=JSON.parse(read("rp_items_catalog.json"));
  const tiers=JSON.parse(read("loot_tiers.json"));
  const spawns=JSON.parse(read("loot_spawns.json"));
  const economy=JSON.parse(read("rp_economy.json"));
  assert.equal(loot.items.length,236);
  assert.equal(rp.items.length,79);
  assert.equal(tiers.tiers.length,5);
  assert.ok(Array.isArray(spawns.spawns));
  assert.equal(economy.denominations.length,7);
  assert.equal(typeof economy.enabled,"boolean");
  const unique = new Set(rp.items.map(item=>item.id));
  assert.equal(unique.size,79);
  assert.ok(!unique.has(undefined));
});
test("Unreal source loader and packaged Content paths use the same exact authoritative filenames",()=>{
  const path=new URL("../unreal/Source/AnomaliaZPrigimalia/AnomaliaZPrigimaliaLootSubsystem.cpp",import.meta.url);
  const src=readFileSync(path,"utf8");
  const economy=readFileSync(new URL("../unreal/Source/AnomaliaZPrigimalia/AnomaliaZPrigimaliaEconomySubsystem.cpp",import.meta.url),"utf8");
  for(const name of dataNames.filter(x=>x!=="rp_economy.json"))
    assert.ok(src.includes(name),"Native loot system does not load "+name);
  assert.ok(economy.includes("rp_economy.json"));
  assert.ok(src.includes("AnomaliaZPrigimalia/Data"));
  assert.ok(economy.includes("AnomaliaZPrigimalia/Data"));
});
