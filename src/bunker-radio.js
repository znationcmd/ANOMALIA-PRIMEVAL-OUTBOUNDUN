/**
 * ANOMALIA'Z PRIGIMALIA — système original de bunkers radio.
 * Ce catalogue décrit des sites du monde ANOMALIA, pas les emplacements DayZ.
 * Une journée en jeu = 1200 secondes simulées ; trois bunkers sont actifs par nuit.
 * Les codes sont déterministes par nuit, ce qui permet une reprise de sauvegarde.
 */
export const BUNKER_FREQUENCY=80.0;
export const GAME_DAY_SECONDS=1200;
export const BROADCAST_NIGHT_START=17.75;
export const BROADCAST_NIGHT_END=6;
export const RADIO_RANGE_METERS=4000;

const WORLD_HALF=24000;
const mapGrid=(x,z)=>
  String(Math.max(0,Math.min(999,Math.floor((x+WORLD_HALF)/100)))).padStart(3,'0')+
  String(Math.max(0,Math.min(999,Math.floor((z+WORLD_HALF)/100)))).padStart(3,'0');

const areas=[
  ['Bunker des Murmures',310,-460,'médical'],
  ['Refuge du Veilleur',-410,740,'stockage'],
  ['Bunker Vesper',-780,-840,'militaire'],
  ['Station Cendre',1290,-1630,'militaire'],
  ['Refuge des Pionniers',-2280,1030,'civil'],
  ['Bunker Boréalis',-1950,1340,'médical'],
  ['Bunker Dôme',3220,850,'technologique'],
  ['Refuge du Port Noir',4100,380,'stockage'],
  ['Bunker Euryn',-650,-2840,'médical'],
  ['Bunker des Brumes',-460,520,'civil'],
  ['Bunker des Cimes',-11500,-11100,'militaire'],
  ['Refuge Boréal',-12100,-11900,'stockage'],
  ['Bunker des Aiguilles',-10700,-12600,'médical'],
  ['Bunker Valbrume',-13900,-10150,'militaire'],
  ['Refuge Mistral',-14050,-9700,'civil'],
  ['Bunker Austral',10800,12300,'militaire'],
  ['Refuge des Prés',11400,13000,'civil'],
  ['Bunker Méridia',13050,13900,'technologique'],
  ['Bunker des Dunes',12500,13300,'stockage'],
  ['Refuge Sentinelle',6250,600,'militaire'],
  ['Bunker Archipel',7380,3610,'médical'],
  ['Bunker des Cendres',3260,-5890,'stockage'],
  ['Bunker de l’Atoll',8020,-4080,'militaire']
];
export const RADIO_BUNKERS=Object.freeze(areas.map(([label,x,z,kind],i)=>Object.freeze({
  id:'radio-bunker-'+String(i+1).padStart(2,'0'),
  type:'radio-bunker',
  label,
  x,z,kind,grid:mapGrid(x,z),
  loot:{ammo:18+(i%4)*10,scrap:8+(i%3)*7,medkit:1+(i%2),food:2}
})));
export const RADIO_ANTENNAS=Object.freeze([
 ['Antenne Hélion',160,320],['Antenne Boréalis',-2060,680],['Tour Vanta',3920,700],
 ['Relais de Borée',-11800,-11500],['Relais Austral',11000,12700],
 ['Tour Sentinelle',6300,100],['Relais Archipel',7380,3550],['Relais des Cendres',3150,-5950]
].map(([label,x,z],i)=>Object.freeze({id:'radio-antenna-'+(i+1),type:'radio-antenna',label,x,z})));

const DIGITS={
 '0':'-----','1':'.----','2':'..---','3':'...--','4':'....-',
 '5':'.....','6':'-....','7':'--...','8':'---..','9':'----.'
};
const REVERSE=Object.fromEntries(Object.entries(DIGITS).map(([digit,morse])=>[morse,digit]));
export function encodeNumbers(value){
  const s=String(value);
  if(!/^\d+$/.test(s))throw new Error('Message Morse : chiffres uniquement.');
  return s.split('').map(d=>DIGITS[d]).join(' ');
}
export function decodeNumbers(value){
  const parts=String(value||'').trim().split(/[\s/]+/).filter(Boolean);
  if(!parts.length || parts.some(part=>REVERSE[part]===undefined))throw new Error('Signal Morse incomplet ou invalide.');
  return parts.map(part=>REVERSE[part]).join('');
}

function stableHash(n){
  let x=n|0;
  x=Math.imul(x^x>>>16,0x45d9f3b);
  x=Math.imul(x^x>>>16,0x45d9f3b);
  return (x^x>>>16)>>>0;
}
export function radioTime(elapsed=0){
  const seconds=Math.max(0,Number(elapsed)||0);
  const daySeconds=((seconds%GAME_DAY_SECONDS)+GAME_DAY_SECONDS)%GAME_DAY_SECONDS;
  const hour=daySeconds/(GAME_DAY_SECONDS/24);
  const onAir=hour>=BROADCAST_NIGHT_START||hour<BROADCAST_NIGHT_END;
  const date=Math.floor(seconds/GAME_DAY_SECONDS)-(hour<BROADCAST_NIGHT_END?1:0);
  return {hour,onAir,nightId:date};
}
export function activeBunkers(state){
  const t=radioTime(state?.elapsed);
  if(!t.onAir)return [];
  const night=t.nightId;
  // Permutation déterministe pour que les trois emplacements soient distincts.
  const pool=RADIO_BUNKERS.map((b,i)=>({b,key:stableHash((night+131)*53+i*7919)}))
    .sort((a,b)=>a.key-b.key).slice(0,3);
  return pool.map(({b})=>({...b,code:String(stableHash((night+709)*9973+Number(b.id.slice(-2))*191)%10000).padStart(4,'0')}));
}
export function broadcast(state){
  const active=activeBunkers(state);
  if(!active.length)return null;
  const phase=(Number(state?.elapsed)||0)%GAME_DAY_SECONDS;
  const index=Math.floor(Math.max(0,phase)/15)%active.length;
  const current=active[index];
  const digits=current.grid+current.code;
  return {frequency:BUNKER_FREQUENCY,grid:current.grid,
    morse:encodeNumbers(digits),digits,bunkerId:current.id,
    nightId:radioTime(state?.elapsed).nightId};
}
export function decodeBroadcast(morse){
  const digits=/^\d+$/.test(String(morse).trim())?String(morse).trim():decodeNumbers(morse);
  if(!/^\d{10}$/.test(digits))throw new Error('Une transmission complète comporte 10 chiffres.');
  const bunker=RADIO_BUNKERS.find(b=>b.grid===digits.slice(0,6))||null;
  return {digits,grid:digits.slice(0,6),code:digits.slice(6),bunker};
}
export function canHearBroadcast(state, position){
  const x=Number(position?.x),z=Number(position?.z);
  if(!Number.isFinite(x)||!Number.isFinite(z))return false;
  if(!(state?.inventory?.radio_transceiver>0 && state?.inventory?.radio_battery>0))return false;
  if(Math.abs(Number(state?.radioFrequency??80)-80)>0.05)return false;
  return RADIO_ANTENNAS.some(a=>Math.hypot(a.x-x,a.z-z)<=RADIO_RANGE_METERS);
}
export function unlockRadioBunker(state,bunkerId,enteredCode){
  const bunker=RADIO_BUNKERS.find(b=>b.id===bunkerId);
  if(!bunker)return {ok:false,message:'Bunker inconnu.'};
  const available=activeBunkers(state).find(b=>b.id===bunkerId);
  if(!available)return {ok:false,message:'Ce bunker est fermé pendant ce cycle radio.'};
  if(!/^\d{4}$/.test(String(enteredCode||''))||String(enteredCode)!==available.code)
    return {ok:false,message:'Code incorrect ou incomplet.'};
  state.radioOpenUntil ||= {};
  state.radioOpenUntil[bunkerId]=Number(state.elapsed||0)+12;
  const alreadyCollected=Array.isArray(state.collected)&&state.collected.includes(bunkerId);
  if(!alreadyCollected){
    state.collected ||= [];
    state.collected.push(bunkerId);
    state.inventory ||= {};
    for(const [item,quantity] of Object.entries(bunker.loot))state.inventory[item]=(state.inventory[item]||0)+quantity;
  }
  return {ok:true,looted:!alreadyCollected,bunker,
    message:alreadyCollected?'Porte ouverte : butin déjà récupéré.':'Bunker ouvert ! Coffre rare récupéré.'};
}
export function radioDoorOpen(state,bunkerId){
  return Number(state?.radioOpenUntil?.[bunkerId]||0)>Number(state?.elapsed||0);
}
