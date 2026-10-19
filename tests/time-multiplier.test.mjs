import test from 'node:test';
import assert from 'node:assert/strict';
import {tickSurvival,initialState} from '../src/mechanics.js';
test('timeMultiplier affects world clock but not hunger and thirst rates',()=>{
 const a=initialState(),b=initialState();a.timeMultiplier=1;b.timeMultiplier=12;
 tickSurvival(a,.1,false);tickSurvival(b,.1,false);
 assert.ok(b.elapsed>a.elapsed*11);
 assert.equal(a.hunger,b.hunger);assert.equal(a.thirst,b.thirst);
});
test('invalid time multipliers are bounded',()=>{
 const a=initialState();a.timeMultiplier=1000000;tickSurvival(a,.1,false);
 assert.ok(a.elapsed<=2.4);
});
