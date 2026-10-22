/** ANOMALIA original deterministic limb injury rules. Prototype only. */
export const LIMBS=['leftArm','rightArm','leftLeg','rightLeg'];
export function applyLimbImpact(state,{limb,force,protection=0}){
 if(!LIMBS.includes(limb)||!Number.isFinite(force))throw Error('Invalid impact');
 const impact=Math.max(0,force)*(1-Math.max(0,Math.min(1,protection)));
 const injuries=state.limbInjuries??={};
 const previous=injuries[limb]||{severity:0,immobilized:false,healing:0};
 const severity=Math.max(previous.severity,impact>=90?3:impact>=60?2:impact>=30?1:0);
 injuries[limb]={...previous,severity,healing:severity?0:previous.healing};
 return injuries[limb];
}
export function limbEffects(state){
 const injuries=state.limbInjuries||{};
 const level=limb=>injuries[limb]?.severity||0;
 const arms=Math.max(level('leftArm'),level('rightArm'));
 const legs=Math.max(level('leftLeg'),level('rightLeg'));
 return {aimSway:arms*0.3,reloadMultiplier:1+arms*.45,canUseTwoHandedWeapons:arms<2,
 movementMultiplier:Math.max(.25,1-legs*.22),canSprint:legs<2,
 canClimb:arms<2&&legs<2,armFractured:arms>0,legFractured:legs>0};
}
export function applySplint(state,limb){
 const injury=state.limbInjuries?.[limb];if(!injury||!injury.severity)return false;
 if((state.inventory?.splint||0)<1)return false;
 state.inventory.splint--;injury.immobilized=true;return true;
}
export function healLimbInjuries(state,seconds){
 for(const injury of Object.values(state.limbInjuries||{})){
  if(!injury.severity)continue;
  injury.healing=(injury.healing||0)+Math.max(0,seconds)*(injury.immobilized?2:0.35);
  if(injury.healing>=1800){injury.severity=Math.max(0,injury.severity-1);injury.healing=0;}
 }
}
