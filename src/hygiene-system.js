/** ANOMALIA: hygiene and physiological needs. Hook actions to interactable sanitary fixtures and animations. */
export const SANITARY_FIXTURES=Object.freeze(["toilet","urinal","shower","bathtub","sink"]);
const clamp=(n)=>Math.max(0,Math.min(100,Number.isFinite(n)?n:0));
export function createHygieneState(saved={}){
 return {hygiene:clamp(saved.hygiene??100),bladder:clamp(saved.bladder??0),bowel:clamp(saved.bowel??0),lastUpdate:Number.isFinite(saved.lastUpdate)?saved.lastUpdate:Date.now()};
}
export function tickHygiene(state,{now=Date.now(),activity=1,rain=0}={}){
 const elapsed=Math.max(0,Math.min((now-state.lastUpdate)/60000,60));
 return {...state,hygiene:clamp(state.hygiene-elapsed*(.09+.06*activity+.05*rain)),bladder:clamp(state.bladder+elapsed*.14),bowel:clamp(state.bowel+elapsed*.07),lastUpdate:now};
}
export function useSanitaryFixture(state,fixture,{hasWater=true,privacyMode=true}={}){
 if(!SANITARY_FIXTURES.includes(fixture))return {ok:false,reason:"unknown_fixture",state};
 if(["shower","bathtub","sink"].includes(fixture)&&!hasWater)return {ok:false,reason:"no_water",state};
 const next={...state};let action;
 switch(fixture){
  case "toilet": if(state.bladder<10&&state.bowel<10)return {ok:false,reason:"no_need",state};next.bladder=0;next.bowel=0;action="toilet";break;
  case "urinal": if(state.bladder<10)return {ok:false,reason:"no_need",state};next.bladder=0;action="urinate";break;
  case "shower":next.hygiene=100;action="shower";break;
  case "bathtub":next.hygiene=100;action="bathe";break;
  case "sink":next.hygiene=clamp(next.hygiene+25);action="wash_hands";break;
 }
 return {ok:true,state:next,action,privacyMode,animationKey:`hygiene_${action}`};
}
export function hygieneEffects(state){
 return {needsToUrinate:state.bladder>=80,needsToDefecate:state.bowel>=80,dirty:state.hygiene<30,discomfort:Math.max(0,(state.bladder-75)/25,(state.bowel-75)/25,(30-state.hygiene)/30)};
}
