/** ANOMALIA prototype survival states; seconds are simulation time. No permanent unconscious lock. */
const clamp=(n,min,max)=>Math.max(min,Math.min(max,Number(n)||0));
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
 if(now<state.unconsciousUntil||now<state.sleepUntil)return false;
 state.sleepUntil=now+30;state.sleeping=true;return true;
}
export function applyKnockout(state,now,duration=23){
 initVitals(state);
 state.unconsciousUntil=Math.max(state.unconsciousUntil,now+Math.max(0,duration));
 state.sleeping=false;return state.unconsciousUntil;
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
 if(bloodCritical&&now>=state.unconsciousUntil&&now>=state.nextBloodFaintAt){
  state.unconsciousUntil=now+10;
  state.nextBloodFaintAt=state.unconsciousUntil+5;
 }
 return {sleeping:state.sleeping,unconscious:now<state.unconsciousUntil,unconsciousSeconds:Math.max(0,state.unconsciousUntil-now),bloodCritical,bloodBlink:bloodCritical&&Math.floor(now*2)%2===0,canAct:!state.sleeping&&now>=state.unconsciousUntil};
}
