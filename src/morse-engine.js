// ANOMALIA'Z Morse protocol, independent from any DayZ assets.
// Public decoders never generate or expose private live bunker codes.
// Browser-compatible secure crypto supplied by the runtime.
const MORSE_DIGITS = ['-----','.----','..---','...--','....-','.....','-....','--...','---..','----.'];
const REVERSE = Object.fromEntries(MORSE_DIGITS.map((m,i)=>[m,String(i)]));
export function encodeBunkerTransmission(grid,code){
 if(!/^\d{6}$/.test(grid)||!/^\d{4}$/.test(code))throw new Error('Grille à 6 chiffres et code à 4 chiffres requis.');
 return (grid+code).split('').map(d=>MORSE_DIGITS[Number(d)]).join(' ');
}
export function decodeBunkerTransmission(input){
 const raw=String(input??'').trim();
 if(raw.length>350)throw new Error('Signal trop long.');
 let digits;
 if(/^\d{10}$/.test(raw))digits=raw;
 else {
  if(!/^[.\-\s/]+$/.test(raw))throw new Error('Signal Morse invalide.');
  const groups=raw.split(/[\s/]+/).filter(Boolean);
  if(groups.length!==10||groups.some(g=>!Object.hasOwn(REVERSE,g)))throw new Error('10 groupes Morse numériques complets requis.');
  digits=groups.map(g=>REVERSE[g]).join('');
 }
 return {digits,grid:digits.slice(0,6),code:digits.slice(6)};
}
function secureRandomInt(max){if(typeof crypto==='undefined'||!crypto.getRandomValues)throw new Error('Secure RNG unavailable'); const range=0x100000000;const limit=range-(range%max);const u=new Uint32Array(1);do{crypto.getRandomValues(u)}while(u[0]>=limit);return u[0]%max;}\nexport function createPrivateCycle(bunkers,{now=Date.now(),durationMs=24*60*60*1000,activeCount=3}={}){
 if(!Array.isArray(bunkers)||!Number.isSafeInteger(activeCount)||activeCount<1||!Number.isSafeInteger(durationMs)||durationMs<60000)throw new Error('Configuration incorrecte.');
 const eligible=bunkers.filter(b=>/^\d{6}$/.test(String(b.grid))&&typeof b.id==='string');
 if(!eligible.length)return {cycleId:null,expiresAt:null,entries:[]};
 const cycleId=Math.floor(now/durationMs);
 const pool=[...eligible];
 for(let i=pool.length-1;i>0;i--){const j=secureRandomInt(i+1);[pool[i],pool[j]]=[pool[j],pool[i]]}
 const entries=pool.slice(0,Math.min(activeCount,pool.length)).map(b=>{
  const code=String(secureRandomInt(10000)).padStart(4,'0');
  return {id:b.id,grid:b.grid,code,morse:encodeBunkerTransmission(b.grid,code)};
 });
 return {cycleId,expiresAt:new Date((cycleId+1)*durationMs).toISOString(),entries};
}
export function publicCycleView(cycle){
 return {cycleId:cycle.cycleId,expiresAt:cycle.expiresAt,entries:(cycle.entries||[]).map(({id,grid})=>({id,grid}))};
}
export function checkBunkerCode(cycle,id,attempt){const entry=(cycle.entries||[]).find(x=>x.id===id);return Boolean(entry&&/^\d{4}$/.test(String(attempt))&&entry.code===String(attempt))}
