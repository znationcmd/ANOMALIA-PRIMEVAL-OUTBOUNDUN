/** ANOMALIA family gameplay model: non-explicit, adult-only opt-in, no player pregnancy without consent. */
export const LIFE_STAGES=Object.freeze(["newborn","baby","child","teen","adult"]);
const STAGE_DAYS=Object.freeze([0,1,7,30,90]);
export function lifeStage(ageDays=0){let i=0;for(let n=1;n<STAGE_DAYS.length;n++)if(ageDays>=STAGE_DAYS[n])i=n;return LIFE_STAGES[i];}
export function createFamilySystem({now=()=>Date.now(),dayMs=86400000}={}){
 if(typeof now!=="function"||!Number.isFinite(dayMs)||dayMs<=0)throw new RangeError("Invalid family clock");
 const clone=value=>JSON.parse(JSON.stringify(value));
 const families=new Map();
 const children=new Map();
 function foundFamily({familyId,playerA,playerB,consentA=false,consentB=false,adultA=false,adultB=false}={}){
  if(!familyId||!playerA||!playerB||playerA===playerB||consentA!==true||consentB!==true||adultA!==true||adultB!==true)return {ok:false,reason:"adult_mutual_consent_required"};
  if(families.has(familyId))return {ok:false,reason:"already_exists"};
  const family={id:familyId,parents:[playerA,playerB],children:[],createdAt:now()};families.set(familyId,family);return {ok:true,family:clone(family)};
 }
 function welcomeChild({familyId,childId,name,mutualConsent=false}={}){
  const family=families.get(familyId);
  if(!family||!childId||children.has(childId)||mutualConsent!==true)return {ok:false,reason:"family_consent_or_id_invalid"};
  const child={id:childId,name:String(name||"Enfant"),familyId,bornAt:now(),care:{food:100,comfort:100,health:100},following:null,skills:[]};
  children.set(childId,child);family.children.push(childId);return {ok:true,child:describe(child)};
 }
 function describe(child){const ageDays=Math.max(0,(now()-child.bornAt)/dayMs);return {...child,ageDays,stage:lifeStage(ageDays),care:{...child.care},skills:[...child.skills]};}
 function careForChild(childId,{food=0,comfort=0,health=0}={}){
  const child=children.get(childId);if(!child)return {ok:false,reason:"child_not_found"};
  for(const [key,amount] of Object.entries({food,comfort,health}))child.care[key]=Math.max(0,Math.min(100,child.care[key]+Math.max(0,Number(amount)||0)));
  return {ok:true,child:describe(child)};
 }
 function followParent(childId,parentId){const child=children.get(childId),family=child&&families.get(child.familyId);
  if(!family||!family.parents.includes(parentId))return {ok:false,reason:"not_parent"};
  child.following=parentId;return {ok:true,child:describe(child)};
 }
 function learnSkill(childId,skill){const child=children.get(childId);if(!child||!skill)return {ok:false};
  if(!["teen","adult"].includes(lifeStage((now()-child.bornAt)/dayMs)))return {ok:false,reason:"too_young"};
  if(!child.skills.includes(skill))child.skills.push(String(skill));return {ok:true,child:describe(child)};
 }
 return {foundFamily,welcomeChild,careForChild,followParent,learnSkill,getChild:id=>children.has(id)?describe(children.get(id)):null,snapshot:()=>clone({families:[...families.values()],children:[...children.values()]})};
}
