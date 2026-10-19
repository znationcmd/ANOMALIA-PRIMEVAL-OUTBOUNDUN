import test from 'node:test';
import assert from 'node:assert/strict';
import {BRIDGES,movementVector,bridgeSurface,groundHeight,moveWithCollisions} from '../src/movement.js';
import {heightAt} from '../src/mechanics.js';
test('forward follows the camera at every heading; partial sticks retain precision',()=>{
 for(const yaw of [0,.8,Math.PI,4.7]){
  const v=movementVector(1,0,yaw);assert.ok(Math.abs(v.x+Math.sin(yaw))<1e-10);assert.ok(Math.abs(v.z+Math.cos(yaw))<1e-10);
 }
 assert.equal(movementVector(.25,0,0).z,-.25);
 assert.ok(Math.abs(Math.hypot(...Object.values(movementVector(1,1,0)))-1)<1e-10);
});
test('solid buildings prevent tunnelling and allow sliding along walls',()=>{
 const solids=[{x:0,z:0,width:10,depth:10}];
 const blocked=moveWithCollisions({x:-10,z:0},30,0,solids);assert.ok(blocked.x<=-5.65);
 const slide=moveWithCollisions({x:-6,z:0},4,4,solids);assert.ok(slide.x<=-5.65);assert.ok(slide.z>3.9);
 const free=moveWithCollisions({x:-10,z:-10},2,3,solids);assert.ok(Math.abs(free.x+8)<1e-9&&Math.abs(free.z+7)<1e-9);
});
test('both bridge decks meet land, support the player across water, and leave nearby ocean untouched',()=>{
 for(const b of BRIDGES){
  assert.ok(heightAt(b.x1,b.z1)>=8);assert.ok(heightAt(b.x2,b.z2)>=8);
  assert.ok(Math.abs(groundHeight(b.x1,b.z1,heightAt)-heightAt(b.x1,b.z1))<1e-8);
  for(let i=0;i<=20;i++){
   const t=i/20,x=b.x1+(b.x2-b.x1)*t,z=b.z1+(b.z2-b.z1)*t;
   assert.ok(groundHeight(x,z,heightAt)>=8);
  }
  const x=(b.x1+b.x2)/2,z=(b.z1+b.z2)/2;
  assert.equal(bridgeSurface(x+100,z+100,heightAt),null);
 }
});
