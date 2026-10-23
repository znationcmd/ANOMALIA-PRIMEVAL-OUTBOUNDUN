import test from 'node:test';
import assert from 'node:assert/strict';
import {getSurvivalIndicators,PERMANENT_VITALS} from '../src/status-indicators.js';
import {restoreVitals,startSleep,tickVitals,applyKnockout} from '../src/vitals-runtime.js';

test('saved fatigue and blood survive normal state normalization without restoring process timers',()=>{
 const s=restoreVitals({health:100},{version:1,fatigue:83,sleepDebt:71,blood:29,wetness:80,shock:67,sleeping:true,unconsciousUntil:1e12});
 assert.equal(s.fatigue,83);assert.equal(s.blood,29);assert.equal(s.sleepDebt,71);
 assert.equal(s.sleeping,false);assert.equal(s.unconsciousUntil,0);
 assert.equal(tickVitals(s,0,.1).unconsciousSeconds,10);
 const invalid=restoreVitals({health:100},{version:1,fatigue:Infinity,blood:NaN});
 assert.equal(invalid.fatigue,0);assert.equal(invalid.blood,100);
});
test('temporary conditions disappear after recovery, including explicit null and false overrides',()=>{
 const state={fatigue:80,blood:30,temperature:34,wetness:80,illness:'flu',fracture:true,infection:55,bleeding:2,drugEffects:{intoxication:4,withdrawal:8}};
 const before=getSurvivalIndicators(state).map(x=>x.id);
 for(const id of ['exhausted','lowBlood','cold','soaked','illness','fracture','infection','bleeding','underInfluence','withdrawal'])assert.ok(before.includes(id),id);
 Object.assign(state,{fatigue:0,blood:100,temperature:37,wetness:0,conditions:{illness:null,fracture:false,infection:0,bleeding:0},drugEffects:{intoxication:0,withdrawal:0}});
 assert.deepEqual(getSurvivalIndicators(state),[]);
 assert.ok(PERMANENT_VITALS.some(([id])=>id==='temperature'));
 assert.ok(PERMANENT_VITALS.some(([id])=>id==='fatigue'));
 assert.deepEqual(getSurvivalIndicators({temperature:null}),[]);
});
test('sleep recovers after thirty simulation seconds, blood faint repeats until recovered without killing',()=>{
 const s=restoreVitals({health:78},{version:1,fatigue:96,sleepDebt:84,blood:100});
 assert.ok(startSleep(s,0));assert.ok(tickVitals(s,29,1).sleeping);
 assert.equal(tickVitals(s,30,1).sleeping,false);assert.equal(s.fatigue,0);assert.equal(s.sleepDebt,0);
 s.blood=25;
 assert.equal(tickVitals(s,31,.1).unconsciousSeconds,10);
 assert.equal(tickVitals(s,41,.1).unconscious,false);
 assert.equal(tickVitals(s,46,.1).unconsciousSeconds,10);
 s.blood=55;assert.equal(tickVitals(s,61,.1).unconscious,false);assert.equal(s.health,78);
 applyKnockout(s,70);assert.equal(tickVitals(s,70,.1).unconsciousSeconds,23);
 assert.equal(tickVitals(s,93,.1).unconscious,false);
 s.health=0;assert.equal(startSleep(s,94),false);
});
