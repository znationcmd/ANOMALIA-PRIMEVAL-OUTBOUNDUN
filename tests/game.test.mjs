import test from "node:test";
import assert from "node:assert/strict";
import * as world from "../src/mechanics.js";
import * as survival from "../src/systems.js";
import * as expansive from "../src/world.js";
test("three world maps are deterministic and bounded",()=>{
 for(const point of [[0,180],[200,20],[-4000,3500],[7100,-3600],[20000,0]]){const [x,z]=point;assert.equal(world.heightAt(x,z),world.heightAt(x,z));assert.ok(Number.isFinite(world.heightAt(x,z)));assert.ok(Number.isFinite(expansive.heightAt(x,z)));assert.ok(typeof expansive.biomeAt(x,z)==="string")}
 assert.ok(world.WORLD_HALF>=10000);assert.ok(expansive.WORLD_HALF_SIZE>=48000);
 assert.ok(world.SITES.some(p=>p.type==="metro"));assert.ok(world.SITES.some(p=>p.type==="catacomb"));
 assert.ok(world.SITES.some(p=>p.type==="boat"));assert.ok(world.SITES.some(p=>p.type==="bunker"));
 assert.ok(expansive.BRIDGES.length>=2);assert.ok(expansive.ISLANDS.some(p=>!p.bridge));
});
test("bunkers and containers require real keys",()=>{
 const state=world.initialState();const bunker=world.SITES.find(x=>x.type==="bunker"&&x.required);
 const denied=world.unlockSite(state,bunker);assert.equal(denied.ok,false);
 state.inventory[bunker.required]=1;
 const accepted=world.unlockSite(state,bunker);assert.equal(accepted.ok,true);
 assert.ok(state.unlocked.includes(bunker.id));
 assert.equal(world.unlockSite(state,bunker).ok,false);
});
test("clothing adds storage, inventory weighs something, can be swapped",()=>{
 const s=survival.initialState();
 const before=survival.capacity(s);
 s.inventory.backpack=1;
 const result=survival.equip(s,"backpack");
 assert.equal(result.ok,true);
 assert.ok(survival.capacity(s)>before);
 s.inventory.bag=1;
 assert.equal(survival.equip(s,"bag").ok,true);
 assert.equal(s.inventory.backpack,1);
 assert.equal(s.equipment.back,"bag");
});
test("illness can be cured and hunger thirst restored",()=>{
 const s=survival.initialState();
 s.hunger=8;s.thirst=5;s.illness="flu";s.infection=80;
 assert.equal(survival.consume(s,"water").ok,true);
 assert.ok(s.thirst>5);
 assert.equal(survival.consume(s,"food").ok,true);
 assert.ok(s.hunger>8);
 s.inventory.medicine=1;
 assert.equal(survival.consume(s,"medicine").ok,true);
 assert.equal(s.illness,null);
});
test("taming requires food; saddles permit riding and tame pair can breed",()=>{
 const s=survival.initialState();
 s.inventory.berry=15;s.inventory.saddle=1;
 const dino={id:"pet-1",type:"stegosaur",trust:0,tamed:false};
 for(let n=0;n<2;n++)survival.tame(s,dino);
 assert.ok(!dino.tamed);
 survival.tame(s,dino);
 assert.equal(dino.tamed,true);
 assert.equal(survival.saddleMount(s,dino).ok,true);
 assert.equal(s.mounted,"pet-1");
 s.tamed.push({id:"pet-2",type:"stegosaur",name:"Stégosaure",hasSaddle:false});
 assert.equal(survival.breed(s,"pet-1","pet-2").ok,true);
 assert.equal(s.tamed.length,3);
});
test("survival save loads without losing clothing and key progress",()=>{
 const s=survival.initialState();s.equipment.back="bag";s.opened.push("bunker-alpha");s.tamed.push({id:"test",type:"raptor"});
 const v=survival.hydrate(survival.serialize(s));
 assert.equal(v.equipment.back,"bag");
 assert.ok(v.opened.includes("bunker-alpha"));assert.equal(v.tamed.length,1);
});
