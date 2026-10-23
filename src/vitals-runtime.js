/** ANOMALIA prototype survival states; seconds are simulation time. No permanent unconscious lock. */
const clamp=(n,min,max)=>Math.max(min,Math.min(max,Number.isFinite(Number(n))?Number(n):min));
/** Saved timestamps belong to an earlier performance clock; never restore them. */
export function restoreVitals(state,saved){
 const source=saved&&saved.version===1?saved:{};
 for(const key of ['fatigue','sleepDebt','blood','wetness','shock']){
  const fallback=key==='blood'?100:0;
  state[key]=Number.isFinite(source[key])?clamp(source[key],0,100):fallback;
 }
 state.sleeping=false;state.sleepUntil=0;state.unconsciousUntil=0;state.nextBloodFaintAt=0;
 return initVitals(state);
}
export function initVitals(state){
 state.fatigue=clamp(state.fatigue,0,100);
 state.sleepDebt=clamp(state.sleepDebt,0,100);
 state.blood=clamp(state.blood??100,0,100);
 state.unconsciousUntil=Number(state.unconsciousUntil)||0;
 state.nextBloodFaintAt=Number(state.nextBloodFaintAt)||0;
 state.sleepUntil=Number(state.sleepUntil)||0;
 return state;
}
export function startSleep(state,now){
 initVitals(state);
 if(state.health<=0||!Number.isFinite(now)||now<state.unconsciousUntil||now<state.sleepUntil)return false;
 state.sleepUntil=now+30;state.sleeping=true;return true;
}
export function applyKnockout(state,now,duration=23){
 initVitals(state);
 if(state.health<=0||!Number.isFinite(now))return state.unconsciousUntil;
 state.unconsciousUntil=Math.max(state.unconsciousUntil,now+clamp(duration,0,60));
 state.sleeping=false;state.sleepUntil=0;return state.unconsciousUntil;
}
export function tickVitals(state,now,dt,{active=true}={}){
 initVitals(state);dt=clamp(dt,0,1);
 if(state.sleeping){
  if(now>=state.sleepUntil){state.sleeping=false;state.fatigue=0;state.sleepDebt=0;}
 }else if(active&&now>=state.unconsciousUntil){
  state.fatigue=clamp(state.fatigue+dt*.012,0,100);
  state.sleepDebt=clamp(state.sleepDebt+dt*.004,0,100);
 }
 const bloodCritical=state.blood<40;
 if(active&&state.health>0&&bloodCritical&&now>=state.unconsciousUntil&&now>=state.nextBloodFaintAt){
  applyKnockout(state,now,10);
  state.nextBloodFaintAt=state.unconsciousUntil+5;
 }
 return {sleeping:state.sleeping,unconscious:now<state.unconsciousUntil,unconsciousSeconds:Math.max(0,state.unconsciousUntil-now),bloodCritical,bloodBlink:bloodCritical&&Math.floor(now*2)%2===0,canAct:!state.sleeping&&now>=state.unconsciousUntil};
}
