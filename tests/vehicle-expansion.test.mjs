import test from 'node:test';
import assert from 'node:assert/strict';
import {VEHICLES,spawnVehicle,tickVehicle} from '../src/vehicles.js';
import {RACE_TRACKS,trackSegments} from '../src/race-tracks.js';
import {parseNavalConfig} from '../src/naval-config.js';
import {PEAKS,SITES,WORLD_HALF} from '../src/mechanics.js';
test('all requested vehicle families have pilotable definitions',()=>{
 for(const id of ['transport_truck','heavy_truck','quad','buggy','snowmobile','jetski','zodiac','dirt_bike','kart','formula1','car','motorcycle','suv','police','gendarmerie','firetruck','ambulance','armored_van','van','fighter_jet','attack_helicopter','transport_helicopter','monster_truck','carrier','warship','submarine']){
  assert.ok(VEHICLES[id],id);assert.ok(VEHICLES[id].speed>0,id);
 }
});
test('tracks have valid geometry and accessible world positions',()=>{
 assert.deepEqual(RACE_TRACKS.map(t=>t.kind),['formula1','monster','motocross']);
 for(const track of RACE_TRACKS){
  assert.ok(Math.abs(track.x)+track.rx<WORLD_HALF);
  assert.ok(Math.abs(track.z)+track.rz<WORLD_HALF);
  assert.equal(trackSegments(track).length,track.segments);
  assert.ok(trackSegments(track).every(s=>s.length>0&&s.length<100));
  assert.ok(SITES.some(s=>s.id===track.id));
 }
 assert.ok(PEAKS.some(p=>p.height>=1300));
});
test('new land, sea and air vehicles can be configured by XML and spawned',()=>{
 const xml='<navalVehicles><vehicle type="formula1" nominal="2" respawn="300"><pos x="9000" z="16000"/></vehicle><vehicle type="fighter_jet" nominal="1"><pos x="9000" z="16000"/></vehicle><vehicle type="zodiac" nominal="1"><pos x="5000" z="2000"/></vehicle></navalVehicles>';
 assert.equal(parseNavalConfig(xml).length,3);
 const state={vehicles:[]};assert.equal(spawnVehicle(state,'formula1',9000,16000,()=>25).ok,true);
 assert.equal(spawnVehicle(state,'zodiac',5000,2000,()=>-10).ok,true);
 assert.equal(spawnVehicle(state,'fighter_jet',9000,16000,()=>25).ok,true);
 tickVehicle(state.vehicles[0],{forward:1},.1,{heightAt:()=>25,solids:[]});
 assert.ok(state.vehicles[0].speed>0);
});
