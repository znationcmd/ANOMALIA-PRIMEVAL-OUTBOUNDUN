import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {parseWorldConfig,XML_FILES} from '../src/xml-config.js';
import {parseTextSettings,parseIni} from '../src/text-settings.js';
import {tickEconomy} from '../src/economy.js';
import {VEHICLES,spawnVehicle,enterVehicle,exitVehicle,tickVehicle,togglePerspective} from '../src/vehicles.js';
import {adoptCompanion,companionCommand,tickCompanion} from '../src/companions.js';
import {initializeNPCs,recruitNPC,tickNPCs,bankTransaction} from '../src/ai-bank.js';
const docs=()=>Object.fromEntries([...XML_FILES,'Game.ini','GameUserSettings.ini','serverDZ.cfg','world-settings.json'].map(n=>[n,readFileSync(new URL('../public/config/'+n,import.meta.url),'utf8')]));
const state=()=>({position:{x:0,z:0},inventory:{food:5},health:100,vehicles:[]});
test('XML config reads quantities, crash positions and cargo and rejects invalid or external entity documents',()=>{
 const files=docs(),c=parseWorldConfig(files);assert.equal(c.types.find(t=>t.id==='water').nominal,18);assert.equal(c.events[0].positions.length,3);assert.equal(c.events[0].cargo[0].id,'rifle');assert.equal(c.ai.length,5);
 assert.throws(()=>parseWorldConfig({...files,'types.xml':'<types><type></types>'}));assert.throws(()=>parseWorldConfig({...files,'types.xml':'<!DOCTYPE x [<!ENTITY y SYSTEM "file:///etc/passwd">]><types/>'}));
 const disabled=parseWorldConfig({...files,'cfgeconomycore.xml':files['cfgeconomycore.xml'].replace('name="LootEnabled" value="1"','name="LootEnabled" value="0"')});assert.equal(disabled.economy.loot,false);
});
test('INI and CFG settings alter configured rates and allowed perspective without executing scripts',()=>{
 const files=docs();files['Game.ini']='[ANOMALIA]\nLootMultiplier=3\nTamingSpeedMultiplier=2';files['GameUserSettings.ini']='[ServerSettings]\nServerThirdPersonPlayer=False\nPlayerCharacterFoodDrainMultiplier=0\n[ScalabilityGroups]\nsg.ShadowQuality=0';
 const c=parseTextSettings(files);assert.equal(c.lootMultiplier,3);assert.equal(c.tamingSpeed,2);assert.equal(c.foodDrain,0);assert.equal(c.thirdPersonAllowed,false);assert.equal(c.shadows,false);
 parseIni('[__proto__]\npolluted=1');assert.equal({}.polluted,undefined);
});
test('configured economy creates unique loot and actual crash cargo, then respects restock timers',()=>{
 const s=state(),c=parseWorldConfig(docs());tickEconomy(s,c,1000);const count=s.groundDrops.length;assert.ok(count>80);assert.equal(s.worldEvents.length,7);tickEconomy(s,c,1001);assert.equal(s.groundDrops.length,count);
 const loot=s.groundDrops.find(t=>t.uid.startsWith('ce-'));s.groundDrops=s.groundDrops.filter(t=>t.uid!==loot.uid);tickEconomy(s,c,1002);assert.ok(!s.groundDrops.some(t=>t.uid===loot.uid));s.groundDrops=s.groundDrops.filter(d=>d.id!==loot.id);tickEconomy(s,c,2000);assert.ok(s.groundDrops.some(t=>t.uid===loot.uid));
});
test('every vehicle accepts controls, moves, and has persistent inside/outside view switching',()=>{
 for(const [id,def]of Object.entries(VEHICLES)){
  const s=state(),heightAt=()=>def.mode==='water'?-10:10;const r=spawnVehicle(s,id,0,0,heightAt);assert.ok(r.ok);assert.ok(enterVehicle(s,r.vehicle.id).ok);const v=r.vehicle;
  for(let i=0;i<40;i++)tickVehicle(v,{forward:1,up:1,turn:.1},.1,{heightAt});assert.ok(Math.hypot(v.x,v.z)>1,id+' must move');assert.ok(v.fuel<100);
  assert.equal(togglePerspective(s).ok,true);assert.equal(s.vehicleView,'inside');togglePerspective(s);assert.equal(s.vehicleView,'outside');
 }
});
test('land vehicles stop at walls and water, and aircraft cannot be exited in flight',()=>{
 const s=state(),heightAt=()=>10;const v=spawnVehicle(s,'car',0,0,heightAt).vehicle;v.speed=20;
 for(let i=0;i<20;i++)tickVehicle(v,{forward:1},.1,{heightAt,solids:[{x:0,z:-8,width:10,depth:2}]});assert.ok(v.z>-6.1);
 const air=spawnVehicle(s,'helicopter',20,0,heightAt).vehicle;s.position={x:20,z:0};enterVehicle(s,air.id);air.y=30;assert.equal(exitVehicle(s,heightAt).ok,false);
});
test('companion follows, waits, feeds and retains state through save/load',()=>{
 const s=state();assert.ok(adoptCompanion(s,'dog').ok);assert.equal(s.inventory.food,2);s.position.x=20;const p=s.companion;for(let i=0;i<50;i++)tickCompanion(s,.1,{heightAt:()=>10,move:(p,dx,dz)=>({x:p.x+dx,z:p.z+dz})});assert.ok(p.x>10);
 companionCommand(s,'stay');const x=p.x;s.position.x=40;tickCompanion(s,.1,{heightAt:()=>10,move:(p,dx,dz)=>({x:p.x+dx,z:p.z+dz})});assert.equal(p.x,x);assert.equal(JSON.parse(JSON.stringify(s)).companion.mode,'stay');
});
test('bank transfers conserve game credits; friendly AI can join and hostile AI attacks with line of sight',()=>{
 const s=state();initializeNPCs(s,[{id:'a',name:'Ally',faction:'friendly',x:2,z:0,recruitCost:100},{id:'h',name:'Hostile',faction:'hostile',x:20,z:0}]);assert.equal(s.cash,250);bankTransaction(s,'deposit',150);assert.equal(s.cash+s.bank,250);assert.equal(bankTransaction(s,'withdraw',151).ok,false);assert.equal(bankTransaction(s,'withdraw',50).ok,true);assert.equal(recruitNPC(s,'a').ok,true);assert.equal(s.npcs[0].mode,'follow');
 const hp=s.health;tickNPCs(s,.1,{move:(p,dx,dz)=>({x:p.x+dx,z:p.z+dz}),clearShot:()=>true,now:0});assert.ok(s.health<hp);const before=s.health;tickNPCs(s,.1,{move:p=>p,clearShot:()=>false,now:1});assert.equal(s.health,before);
});
