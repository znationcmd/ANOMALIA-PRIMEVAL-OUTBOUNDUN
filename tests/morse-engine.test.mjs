import test from 'node:test';
import assert from 'node:assert/strict';
import {encodeBunkerTransmission,decodeBunkerTransmission,createPrivateCycle,publicCycleView,checkBunkerCode} from '../src/morse-engine.js';
test('Morse preserves leading zeros',()=>{
 const encoded=encodeBunkerTransmission('001234','0007');
 assert.deepEqual(decodeBunkerTransmission(encoded),{digits:'0012340007',grid:'001234',code:'0007'});
});
test('reject malformed transmissions',()=>assert.throws(()=>decodeBunkerTransmission('.----')));
test('server code stays out of public catalog',()=>{
 const cycle=createPrivateCycle([{id:'test-bunker',grid:'123456'}]);
 assert.ok(checkBunkerCode(cycle,'test-bunker',cycle.entries[0].code));
 assert.equal('code' in publicCycleView(cycle).entries[0],false);
});