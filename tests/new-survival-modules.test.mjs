import test from 'node:test';
import assert from 'node:assert/strict';
import {createTrackingSystem} from '../src/tracking-system.js';
import {createHygieneState,tickHygiene,useSanitaryFixture} from '../src/hygiene-system.js';
import {createFamilySystem} from '../src/family-system.js';
import {createPregnancySystem} from '../src/family-pregnancy.js';

test('tracking rejects invalid capacity and retains unique clue identity when the buffer is full',()=>{
 for(const maxClues of [-1,0,Infinity,NaN,1.5])assert.throws(()=>createTrackingSystem({maxClues}),RangeError);
 const traces=createTrackingSystem({maxClues:2});const ids=[];
 for(let i=0;i<6;i++)ids.push(traces.addClue({type:'footprint',actorId:'p1',x:i,y:0,z:0,time:1000}).id);
 assert.equal(new Set(ids).size,6);assert.equal(traces.snapshot().length,2);
 assert.equal(traces.addClue({type:'blood',actorId:'p1',x:0,z:0,severity:NaN}),null);
 assert.equal(traces.nearby({x:5,z:0,now:1100}).length,2);
});
test('hygiene retains saved needs when clocks are invalid or move backwards, and fixtures require water',()=>{
 const state=createHygieneState({lastUpdate:1000,hygiene:40,bladder:90,bowel:85});
 for(const now of [NaN,Infinity,0])assert.deepEqual(tickHygiene(state,{now}),state);
 assert.equal(useSanitaryFixture(state,'shower',{hasWater:false}).ok,false);
 const toilet=useSanitaryFixture(state,'toilet');assert.equal(toilet.state.bladder,0);assert.equal(toilet.state.bowel,0);
 assert.equal(state.bladder,90);
});
test('family snapshots and returned parent arrays cannot mutate live ownership or child state',()=>{
 const f=createFamilySystem({now:()=>1000});
 assert.equal(f.foundFamily({familyId:'f',playerA:'a',playerB:'b',consentA:'yes',consentB:true,adultA:true,adultB:true}).ok,false);
 const created=f.foundFamily({familyId:'f',playerA:'a',playerB:'b',consentA:true,consentB:true,adultA:true,adultB:true});
 created.family.parents.push('intruder');
 assert.equal(f.welcomeChild({familyId:'f',childId:'c',mutualConsent:'yes'}).ok,false);
 assert.equal(f.welcomeChild({familyId:'f',childId:'c',mutualConsent:true}).ok,true);
 const snapshot=f.snapshot();snapshot.families[0].parents.push('intruder');snapshot.children[0].care.health=0;
 assert.equal(f.followParent('c','intruder').ok,false);assert.equal(f.getChild('c').care.health,100);
});
test('pregnancy requires explicit confirmation and snapshot edits cannot trigger early birth',()=>{
 for(const gestationMs of [0,-1,Infinity,NaN])assert.throws(()=>createPregnancySystem({gestationMs}),RangeError);
 let time=0;const p=createPregnancySystem({now:()=>time,gestationMs:100});
 assert.equal(p.begin({familyId:'f',carryingPlayerId:'a',adultConsentA:'yes',adultConsentB:true,carrierConsent:true}).ok,false);
 assert.equal(p.begin({familyId:'f',carryingPlayerId:'a',adultConsentA:true,adultConsentB:true,carrierConsent:true}).ok,true);
 p.snapshot()[0].dueAt=0;assert.equal(p.giveBirth('f',{confirmedByCarrier:true}).ok,false);
 time=100;assert.equal(p.giveBirth('f',{confirmedByCarrier:'yes'}).ok,false);
 assert.equal(p.giveBirth('f',{confirmedByCarrier:true}).ok,true);assert.equal(p.giveBirth('f',{confirmedByCarrier:true}).ok,false);
});
