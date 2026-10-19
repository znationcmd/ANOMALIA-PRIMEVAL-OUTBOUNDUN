import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {startBeachJourney,beachObjective,BEACH_SPAWN} from '../src/beach-journey.js';
import {initialState,heightAt,biomeAt} from '../src/mechanics.js';
import {consume,equip} from '../src/systems.js';
import {pickupDrop,syncInventory} from '../src/inventory.js';
import {loadSedan} from '../src/sedan.js';
test('fresh survival begins above water on a beach and objectives require drinking and actually equipping warmth',()=>{
 const s=startBeachJourney(initialState());assert.equal(biomeAt(BEACH_SPAWN.x,BEACH_SPAWN.z),'plage');assert.ok(heightAt(BEACH_SPAWN.x,BEACH_SPAWN.z)>1);assert.equal(s.inventory.water,undefined);assert.equal(s.inventory.pistol,undefined);assert.match(beachObjective(s).title,/plage/);syncInventory(s);
 assert.ok(pickupDrop(s,'beach-water').ok);assert.equal(s.beachJourney.waterDrunk,false);assert.ok(consume(s,'water').ok);assert.equal(s.beachJourney.waterDrunk,true);s.position={x:435,z:78};assert.ok(pickupDrop(s,'beach-coat').ok);assert.equal(s.beachJourney.completed,false);assert.ok(equip(s,'coat').ok);assert.match(beachObjective(s).title,/quitter/);assert.equal(s.beachJourney.completed,true);assert.ok(JSON.parse(JSON.stringify(s)).beachJourney.completed);
});
test('embedded licensed car parses offline at full scale with four independently rotating wheel groups',async()=>{
 const car=await loadSedan(),bounds=new THREE.Box3().setFromObject(car),size=bounds.getSize(new THREE.Vector3());assert.ok(size.z>4&&size.z<5.5);assert.ok(size.x>1.8&&size.x<2.6);assert.ok(size.y>1.3&&size.y<2);let wheels=0,meshes=0;car.traverse(o=>{if(o.userData.wheel)wheels++;if(o.isMesh)meshes++;});assert.equal(wheels,4);assert.ok(meshes<30,'material batching keeps draw calls bounded');
});
