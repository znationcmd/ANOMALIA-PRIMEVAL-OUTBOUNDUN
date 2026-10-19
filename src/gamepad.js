/** Standard Gamepad API controller input for Xbox (A/B/X/Y) and PlayStation (✕/○/□/△).
 * Pure decoding makes button edges testable and prevents repeated actions when held.
 * All input is local; no permissions, drivers or external gamepad services.
 */
export const GAMEPAD_ACTIONS={
  0:"accept",        // A / Cross
  1:"back",          // B / Circle
  2:"interact",      // X / Square
  3:"inventory",     // Y / Triangle
  4:"lamp",          // LB / L1
  5:"reload",        // RB / R1
  8:"map",           // View / Create
  9:"menu",          // Menu / Options
  10:"sprint",       // L3: held
  11:"focus",        // R3
  12:"mount",        // D-pad up
  13:"boat",         // D-pad down
  14:"breed",        // D-pad left
  15:"build",        // D-pad right
};
export const GAMEPAD_LABELS={
  xbox:"Xbox : stick G déplacer · stick D regarder · RT tirer · X interagir · Y inventaire · View carte · A valider · B retour · RB recharger · L3 courir · D-pad ↑ monture / ↓ bateau / ← reproduction / → construire",
  playstation:"PS5 : stick G déplacer · stick D regarder · R2 tirer · □ interagir · △ inventaire · Create carte · ✕ valider · ○ retour · R1 recharger · L3 courir · Croix ↑ monture / ↓ bateau / ← reproduction / → construire"
};
export function controllerFamily(id=""){
 return /dualsense|dualshock|playstation|sony|054c|^wireless controller/i.test(id)?"playstation":"xbox";
}
export function deadzone(value,threshold=.16){
 const v=Number(value)||0;
 if(Math.abs(v)<=threshold)return 0;
 return Math.sign(v)*Math.min(1,(Math.abs(v)-threshold)/(1-threshold));
}
export function buttonDown(btn){
 return !!btn&&(btn.pressed===true||(Number(btn.value)||0)>.55);
}
export function readGamepad(pad,prior=[]){
 if(!pad||pad.connected===false)return null;
 const axes=Array.isArray(pad.axes)?pad.axes:[];
 const buttons=Array.from(pad.buttons||[],buttonDown);
 const prev=Array.isArray(prior)?prior:[];
 const justPressed=Object.entries(GAMEPAD_ACTIONS).filter(([i])=>buttons[+i]&&!prev[+i]).map(([i,action])=>action);
 const trigger=Number(pad.buttons?.[7]?.value||0)>.35||buttons[7];
 return {
  family:controllerFamily(pad.id),
  mapping:pad.mapping||"unknown",
  moveX:deadzone(axes[0]),
  moveY:-deadzone(axes[1]),
  lookX:deadzone(axes[2]),
  lookY:deadzone(axes[3]),
  aim:buttonDown(pad.buttons?.[6]),
  fire:trigger,
  sprint:buttons[10]||false,
  buttons,
  justPressed
 };
}
export function selectGamepad(getGamepads){
 if(typeof getGamepads!=="function")return null;
 try{
  const pads=getGamepads();
  return Array.from(pads||[]).find(p=>p&&p.connected!==false&&p.mapping==="standard")||
    Array.from(pads||[]).find(p=>p&&p.connected!==false)||null;
 }catch{return null;}
}
