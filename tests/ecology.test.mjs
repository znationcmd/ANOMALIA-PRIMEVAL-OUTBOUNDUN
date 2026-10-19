import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {heightAt,biomeAt,CHUNK_SIZE,hash2} from "../src/mechanics.js";
import {JUNGLE_ZONES,WILDLIFE,inJungle,habitatSpecies,wildlifeSpawn,huntAnimal,fishAt,cookFood,craftSurvival,forageSupplies,tranquilize,tickTorpor,tameWithKibble} from "../src/ecology.js";
import {initialState,consume,hasItem} from "../src/systems.js";

test("jungle zones have named boundaries and ocean/shore animals are separated",()=>{
 assert.ok(JUNGLE_ZONES.length>=3);
 assert.equal(inJungle(JUNGLE_ZONES[0].x,JUNGLE_ZONES[0].z,25),true);
 assert.equal(inJungle(JUNGLE_ZONES[0].x,JUNGLE_ZONES[0].z,250),false);
 assert.equal(habitatSpecies({height:-10,biome:"ocean",roll:.1}),"shark");
 assert.equal(habitatSpecies({height:1,biome:"plage",roll:.1}),"crocodile");
 assert.equal(habitatSpecies({height:20,biome:"jungle",roll:.2}),"jaguar");
 for(const key of ["crocodile","shark","deer","boar","bird","jaguar"])assert.ok(WILDLIFE[key].hp>0);
});
test("wildlife generations are repeatable and remain inside their own terrain sector",()=>{
 const w={chunkSize:CHUNK_SIZE,hash:hash2,heightAt,biomeAt};
 for(const [cx,cz] of [[0,0],[-3,1],[26,0],[10,-10]]){
  const first=wildlifeSpawn(cx,cz,w,3);
  assert.deepEqual(first,wildlifeSpawn(cx,cz,w,3));
  for(const a of first){
   assert.ok(Math.abs(a.x-cx*CHUNK_SIZE)<CHUNK_SIZE/2);
   assert.ok(Math.abs(a.z-cz*CHUNK_SIZE)<CHUNK_SIZE/2);
   assert.ok(WILDLIFE[a.type]&&a.hp>0);
  }
 }
});
test("hunting awards food and hides once and prevents duplicate looting",()=>{
 const s=initialState(),boar={id:"boar-123",type:"boar"};
 const r=huntAnimal(s,boar);assert.equal(r.ok,true);
 assert.equal(s.inventory.raw_meat,4);assert.equal(s.inventory.hide,2);
 assert.equal(huntAnimal(s,boar).ok,false);
 assert.equal(s.inventory.raw_meat,4);
});
test("fishing requires a rod and water, raw fish needs a campfire to cook",()=>{
 const s=initialState();
 assert.equal(fishAt(s,{nearWater:true,roll:.81}).ok,false);
 s.inventory.fishing_rod=1;
 assert.equal(fishAt(s,{nearWater:false,roll:.81}).ok,false);
 assert.equal(fishAt(s,{nearWater:true,roll:.15}).ok,false);
 assert.equal(fishAt(s,{nearWater:true,roll:.81}).ok,true);
 assert.equal(s.inventory.raw_fish,2);
 assert.equal(cookFood(s,"raw_fish",false).ok,false);
 assert.equal(cookFood(s,"raw_fish",true).ok,true);
 assert.equal(s.inventory.cooked_fish,1);
 s.hunger=12;assert.equal(consume(s,"cooked_fish").ok,true);
 assert.ok(s.hunger>12);
});
test("eggs and fibers can be gathered, and croquettes consume recipes",()=>{
 const s=initialState();
 assert.equal(forageSupplies(s,{jungle:true,roll:.2}).item,"egg");
 assert.equal(forageSupplies(s,{roll:.45}).item,"berry");
 assert.equal(forageSupplies(s,{roll:.95}).item,"fiber");
 s.inventory.egg=2;s.inventory.berry=12;s.inventory.cooked_fish=2;s.inventory.cooked_meat=4;
 assert.equal(craftSurvival(s,"kibble_herbivore").ok,true);
 assert.equal(craftSurvival(s,"kibble_carnivore").ok,true);
 assert.equal(s.inventory.kibble_herbivore,1);
 assert.equal(s.inventory.kibble_carnivore,1);
});
test("tranquilizer darts knock out a wild dinosaur; two correct kibble feeds tame it",()=>{
 const s=initialState();s.inventory.tranq_dart=3;s.inventory.kibble_herbivore=2;
 const dino={id:"dino-1",type:"triceratops",tamed:false,torpor:0,unconscious:false};
 assert.equal(tameWithKibble(s,dino).ok,false);
 assert.equal(tranquilize(s,dino).unconscious,false);
 assert.equal(tranquilize(s,dino).unconscious,false);
 assert.equal(tranquilize(s,dino).unconscious,true);
 assert.equal(s.inventory.tranq_dart,undefined);
 assert.equal(tameWithKibble(s,dino).progress,50);
 assert.equal(tameWithKibble(s,dino).tamed,true);
 assert.equal(s.tamed.length,1);
 assert.equal(tameWithKibble(s,dino).ok,false);
});
test("sleeping dinos eventually awaken and lose incomplete taming progress",()=>{
 const d={unconscious:true,unconsciousTime:1,torpor:110,tameProgress:50};
 tickTorpor(d,2);
 assert.equal(d.unconscious,false);assert.equal(d.tameProgress,0);
});
test("world client has actual ecology hooks, clickable map markers and console/gamepad shortcuts",()=>{
 const main=readFileSync(new URL("../src/main.js",import.meta.url),"utf8");
 for(const term of ["wildlifeSpawn(","huntAnimal(","tranquilize(","tameWithKibble(","fishNow()","cookFood(","JUNGLE_ZONES","state.mapPins.push",'"cook-meat":()=>cookNear("raw_meat")',"case \"KeyP\"","case \"KeyV\"",'case "focus":toggleTranqMode()']){
  assert.ok(main.includes(term),"missing gameplay hook: "+term);
 }
});
test('higher-tier croquettes satisfy configured dinosaur preferences; jungle supplies support recipes',()=>{
 const s=initialState();s.dinoKibblePreferences={raptor:'kibble_simple'};s.inventory.kibble_superior=2;
 const d={id:'ranked-pet',type:'raptor',unconscious:true,tamed:false};assert.equal(tameWithKibble(s,d).ok,true);assert.equal(tameWithKibble(s,d).tamed,true);assert.equal(s.inventory.kibble_superior,undefined);
 assert.equal(forageSupplies(s,{jungle:true,roll:.99}).item,'honey');
});
