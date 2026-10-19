import test from 'node:test';
import assert from 'node:assert/strict';
import {parseNavalConfig} from '../src/naval-config.js';
import {VEHICLES,spawnVehicle,tickVehicle,enterVehicle} from '../src/vehicles.js';
test('naval XML settings control types, quantity and positions',()=>{
 const rows=parseNavalConfig('<navalVehicles><vehicle type="carrier" enabled="1" nominal="2" respawn="1800"><pos x="120" z="240" yaw="90"/></vehicle><vehicle type="warship" enabled="0" nominal="9"><pos x="50" z="20"/></vehicle><vehicle type="submarine" enabled="1" nominal="1"><pos x="250" z="300"/></vehicle></navalVehicles>');
 assert.equal(rows.length,3);assert.equal(rows[0].nominal,2);assert.equal(rows[0].positions[0].yaw,Math.PI/2);assert.equal(rows[1].enabled,false);assert.equal(rows[2].type,'submarine');
 assert.deepEqual(parseNavalConfig('<navalVehicles/>'),[]);
 assert.throws(()=>parseNavalConfig('<!DOCTYPE x><navalVehicles/>'));
});
test('all three naval prototypes are pilotable on sea and reject dry land',()=>{
 for(const type of ['carrier','warship','submarine']){
  assert.ok(VEHICLES[type]);
  const state={vehicles:[],vehicleSequence:0},sea=()=>-15;
  const spawned=spawnVehicle(state,type,0,0,sea);
  assert.equal(spawned.ok,true,type);
  const v=spawned.vehicle;
  for(let i=0;i<30;i++)tickVehicle(v,{forward:1,up:1,turn:0},.1,{heightAt:sea});
  assert.ok(Math.hypot(v.x,v.z)>0.2,type+' should move');
  assert.ok(v.fuel<100);
  assert.equal(spawnVehicle(state,type,0,0,()=>10).ok,false);
 }
});

test('large naval ships can be boarded from near their hull but not from far away',()=>{
 const sea=()=>-30,state={vehicles:[],vehicleSequence:0,position:{x:0,z:0}};
 const created=spawnVehicle(state,'carrier',0,0,sea);assert.equal(created.ok,true);
 state.position={x:0,z:36};assert.equal(enterVehicle(state,created.vehicle.id).ok,true);
 state.activeVehicle=null;state.position={x:0,z:75};assert.equal(enterVehicle(state,created.vehicle.id).ok,false);
});

test('duplicate ship categories are merged without discarding spawn positions',()=>{
 const rows=parseNavalConfig('<navalVehicles><vehicle type="carrier" nominal="1" respawn="5000"><pos x="100" z="200"/></vehicle><vehicle type="carrier" nominal="2" respawn="3000"><pos x="300" z="400"/></vehicle></navalVehicles>');
 assert.equal(rows.length,1);assert.equal(rows[0].nominal,3);assert.equal(rows[0].positions.length,2);assert.equal(rows[0].respawn,3000);
});
