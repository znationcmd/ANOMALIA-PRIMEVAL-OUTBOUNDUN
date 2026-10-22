/** Non-explicit opt-in family pregnancy model; gameplay time is configurable. */
export function createPregnancySystem({now=()=>Date.now(),gestationMs=7*86400000}={}){
 if(typeof now!=="function"||!Number.isFinite(gestationMs)||gestationMs<=0)throw new RangeError("Invalid gestation clock");
 const pregnancies=new Map();
 function begin({familyId,carryingPlayerId,adultConsentA=false,adultConsentB=false,carrierConsent=false}={}){
  if(!familyId||!carryingPlayerId||adultConsentA!==true||adultConsentB!==true||carrierConsent!==true)return {ok:false,reason:"adult_mutual_consent_required"};
  if(pregnancies.has(familyId))return {ok:false,reason:"already_in_progress"};
  const record={familyId,carryingPlayerId,startedAt:now(),dueAt:now()+gestationMs,status:"pregnant"};
  pregnancies.set(familyId,record);return {ok:true,pregnancy:{...record}};
 }
 function progress(familyId){const p=pregnancies.get(familyId);if(!p)return null;return {...p,progress:Math.max(0,Math.min(1,(now()-p.startedAt)/(p.dueAt-p.startedAt))),readyForBirth:now()>=p.dueAt};}
 function giveBirth(familyId,{confirmedByCarrier=false}={}){
  const p=progress(familyId);if(!p)return {ok:false,reason:"not_pregnant"};
  if(!p.readyForBirth||confirmedByCarrier!==true)return {ok:false,reason:"not_ready_or_not_confirmed"};
  pregnancies.delete(familyId);return {ok:true,familyId,animationKey:"family_birth_fade",at:now()};
 }
 return {begin,progress,giveBirth,snapshot:()=>[...pregnancies.values()].map(p=>({...p}))};
}
