import {inJungle} from "./ecology.js";
/** Pure, deterministic world rules. Coordinates are in metres. No copyrighted game assets. */
export const WORLD_HALF=24000;
export const CHUNK_SIZE=256;
export const SEA_LEVEL=0;
export const WORLD_SEED=28041996;
export const CONTINENTS=[
 {id:"north",name:"Terres de Borée",cx:-11500,cz:-11500,rx:7500,rz:7500},
 {id:"south",name:"Continent Austral",cx:11000,cz:12500,rx:8000,rz:6500},
 {id:"prime",name:"Continent Primeval",cx:-600,cz:0,rx:5450,rz:4250},
 {id:"island-a",name:"Île Sentinelle",cx:6350,cz:0,rx:1080,rz:1420},
 {id:"island-b",name:"Archipel du Néant",cx:7400,cz:3650,rx:1050,rz:900},
 {id:"island-c",name:"Les Cendres",cx:3100,cz:-5900,rx:1450,rz:1060},
 {id:"island-d",name:"Île Brisée",cx:-6900,cz:4300,rx:940,rz:1130},
 {id:"island-e",name:"Atoll Oublié",cx:8100,cz:-4200,rx:1200,rz:950}
];
export const CITIES=[
 {id:"nordheim",name:"Nordheim — Capitale de Borée",x:-11500,z:-11500,radius:1050,density:.67},
 {id:"australis",name:"Australis — Cité des plaines",x:11000,z:12500,radius:950,density:.64},
 {id:"valbrume",name:"Valbrume — Ville des montagnes",x:-14000,z:-10000,radius:550,density:.50},
 {id:"meridia",name:"Méridia — Ville australe",x:13000,z:14000,radius:650,density:.56},
 {id:"helion",name:"Hélion — Métropole oubliée",x:0,z:0,radius:1000,density:0.83},
 {id:"borealis",name:"Boréalis — Cité industrielle",x:-2400,z:850,radius:820,density:0.63},
 {id:"caldera",name:"Caldera — Forteresse",x:1500,z:-1800,radius:620,density:0.57},
 {id:"vanta",name:"Vanta — Port marchand",x:3900,z:500,radius:630,density:0.66},
 {id:"euryn",name:"Euryn — Ruines du nord",x:-800,z:-2950,radius:680,density:0.49},
 {id:"sentinelle",name:"Sentinelle — Colonie insulaire",x:6200,z:100,radius:460,density:0.44},
 {id:"keros",name:"Kéros — Village volcanique",x:3200,z:-6000,radius:410,density:0.40}
];
export const PEAKS=[
 {x:-14000,z:-13500,height:1250,radius:1800},
 {x:-10000,z:-15500,height:980,radius:1450},
 {x:-12400,z:-17100,height:1320,radius:1800},
 {x:-16400,z:-13200,height:1080,radius:1650},
 {x:12500,z:11000,height:1100,radius:1700},
 {x:15000,z:14500,height:820,radius:1500},
 {x:-3200,z:-2200,height:680,radius:880},
 {x:1400,z:2700,height:980,radius:1150},
 {x:-500,z:-3700,height:650,radius:750},
 {x:3400,z:-1900,height:560,radius:730},
 {x:7400,z:3550,height:480,radius:580},
 {x:3000,z:-6250,height:440,radius:640}
];
export const SITES=[
 {id:"f1-austral",type:"racetrack",label:"Circuit de Formule 1 Austral",x:9000,z:16000},
 {id:"monster-arena",type:"racetrack",label:"Circuit Monster Trucks",x:15000,z:17400},
 {id:"motocross-trail",type:"racetrack",label:"Terrain de motocross",x:8000,z:11000},
 {id:"snowy-boreal",type:"mountain",label:"Massif enneigé de Borée",x:-12400,z:-17100},
 {id:"alpha-key",type:"key",label:"Cache du veilleur — clé Alpha",x:65,z:-95,item:"key_alpha"},
 {id:"cargo-key",type:"key",label:"Cadavre du contrebandier — clé rouge",x:-90,z:50,item:"key_red"},
 {id:"bunker-alpha",type:"bunker",label:"Bunker ALPHA",x:260,z:-240,required:"key_alpha",loot:{ammo:24,water:2,scrap:12,medkit:1}},
 {id:"cargo-red",type:"container",label:"Conteneur sécurisé ROUGE",x:150,z:130,required:"key_red",loot:{wood:12,ammo:18,food:3}},
 {id:"metro-helion",type:"metro",label:"Métro souterrain Hélion",x:-145,z:85,underground:"metro"},
 {id:"catacomb-helion",type:"catacomb",label:"Catacombes de la vieille ville",x:350,z:240,underground:"catacomb"},
 {id:"village-mist",type:"village",label:"Village caché des Brumes",x:-520,z:430,loot:{food:4,wood:20,water:4}},
 {id:"bridge-sentinelle",type:"bridge",label:"Pont des Survivants — vers Sentinelle",x:5230,z:0},
 {id:"port-vanta",type:"boat",label:"Bateau côtier — Port Vanta",x:4990,z:950},
 {id:"bunker-omega-key",type:"key",label:"Clé Bunker Omega",x:-1650,z:800,item:"key_omega"},
 {id:"bunker-omega",type:"bunker",label:"Bunker OMEGA",x:-2100,z:920,required:"key_omega",loot:{ammo:50,scrap:25,medkit:2}},
 {id:"bunker-abyss-key",type:"key",label:"Clé de l'Abysse",x:6320,z:800,item:"key_abyss"},
 {id:"bunker-abyss",type:"bunker",label:"Bunker ABYSSE",x:6470,z:1150,required:"key_abyss",loot:{ammo:90,medkit:4,food:8}},
 {id:"metro-borealis",type:"metro",label:"Métro Boréalis — ligne noire",x:-2380,z:780,underground:"metro"},
 {id:"catacomb-euryn",type:"catacomb",label:"Catacombes d'Euryn",x:-950,z:-2950,underground:"catacomb"},
 {id:"village-ashen",type:"village",label:"Village caché de Cendre",x:3500,z:-5910,loot:{food:3,water:2}},
 {id:"village-atoll",type:"village",label:"Refuge de l'Atoll",x:8010,z:-4130,loot:{water:5,wood:10}},
 {id:"cargo-blue-key",type:"key",label:"Clé du conteneur bleu",x:3930,z:570,item:"key_blue"},
 {id:"cargo-blue",type:"container",label:"Conteneur sécurisé BLEU",x:4020,z:480,required:"key_blue",loot:{ammo:30,scrap:16}}
];
export const ITEM_NAMES={milk:"Lait frais",eggs:"Œufs de poule",
 wood:"Bois",scrap:"Pièces métalliques",food:"Rations",water:"Eau potable",medkit:"Kit médical",
 ammo:"Munitions",key_alpha:"Clé Alpha",key_red:"Clé rouge",key_omega:"Clé Omega",key_abyss:"Clé Abysse",key_blue:"Clé bleue"
};
export function clamp(v,min,max){return Math.min(max,Math.max(min,v))}
export function smooth(t){t=clamp(t,0,1);return t*t*(3-2*t)}
export function hash2(x,z,seed=WORLD_SEED){let n=(Math.imul(x|0,374761393)+Math.imul(z|0,668265263)+Math.imul(seed,1442695041))|0;n=Math.imul(n^(n>>>13),1274126177);return ((n^(n>>>16))>>>0)/4294967296}
export function noise2(x,z){const ix=Math.floor(x),iz=Math.floor(z),fx=smooth(x-ix),fz=smooth(z-iz);const a=hash2(ix,iz),b=hash2(ix+1,iz),c=hash2(ix,iz+1),d=hash2(ix+1,iz+1);return (a*(1-fx)+b*fx)*(1-fz)+(c*(1-fx)+d*fx)*fz}
export function fBm(x,z){return (noise2(x/120,z/120)-.5)*9+(noise2(x/480,z/480)-.5)*26+(noise2(x/1250,z/1250)-.5)*36}
export function landMask(x,z){let mask=0;for(const c of CONTINENTS){const nx=(x-c.cx)/c.rx,nz=(z-c.cz)/c.rz;const edge=(noise2(x/650,z/650)-.5)*.068+(noise2(x/150,z/150)-.5)*.013;const r=Math.sqrt(nx*nx+nz*nz)+edge;mask=Math.max(mask,1-smooth((r-.80)/.28))}return clamp(mask,0,1)}
export function heightAt(x,z){const land=landMask(x,z);let h=-11+land*(23+fBm(x,z)*.55);for(const p of PEAKS){const dx=x-p.x,dz=z-p.z,r2=(dx*dx+dz*dz)/(p.radius*p.radius);h+=p.height*Math.exp(-r2*2.0)*Math.pow(land,1.5)}return h}
export function biomeAt(x,z){const h=heightAt(x,z);if(h<SEA_LEVEL-1)return "ocean";if(h<5)return "plage";if(h>340)return "neiges";if(h>190)return "montagne";if(h>75)return "hautes-terres";if(inJungle(x,z,h))return "jungle";if(noise2(x/900+12,z/900-8)>.61)return "prairie";return "forêt"}
export function nearestCity(x,z){let best=null,dist=Infinity;for(const city of CITIES){const d=Math.hypot(x-city.x,z-city.z);if(d<dist){best=city;dist=d}}return {city:best,distance:dist}}
export function nearestSite(x,z,maxDistance=Infinity,sites=SITES){let target=null,dist=maxDistance;for(const s of sites){const d=Math.hypot(x-s.x,z-s.z);if(d<dist){target=s;dist=d}}return target?{site:target,distance:dist}:null}
export function initialState(){return {version:1,position:{x:0,z:180},yaw:0,health:100,stamina:100,hunger:100,thirst:100,ammo:12,magazine:12,inventory:{wood:15,scrap:4,food:2,water:2,medkit:1,ammo:48},collected:[],unlocked:[],structures:[],kills:0,distance:0,day:1,elapsed:0,underground:null,boat:false,boatPosition:{x:4990,z:950},quest:0}}
export function normalizeState(v){const d=initialState();if(!v||v.version!==1)return d;const numeric=(n,f,min,max)=>Number.isFinite(n)?clamp(n,min,max):f;const x=numeric(v.position?.x,d.position.x,-WORLD_HALF,WORLD_HALF),z=numeric(v.position?.z,d.position.z,-WORLD_HALF,WORLD_HALF);d.position={x,z};for(const k of ["health","stamina","hunger","thirst"])d[k]=numeric(v[k],d[k],0,100);d.ammo=numeric(v.ammo,12,0,12);d.inventory={...d.inventory};for(const k of Object.keys(ITEM_NAMES))d.inventory[k]=numeric(v.inventory?.[k],d.inventory[k]||0,0,9999);d.collected=Array.isArray(v.collected)?v.collected.filter(x=>typeof x==="string").slice(0,1000):[];d.unlocked=Array.isArray(v.unlocked)?v.unlocked.filter(x=>typeof x==="string").slice(0,200):[];d.structures=Array.isArray(v.structures)?v.structures.filter(x=>x&&["shelter","fire"].includes(x.type)&&Number.isFinite(x.x)&&Number.isFinite(x.z)).slice(0,200):[];d.day=numeric(v.day,1,1,99999);d.elapsed=numeric(v.elapsed,0,0,1e9);d.kills=numeric(v.kills,0,0,1e7);d.distance=numeric(v.distance,0,0,1e9);d.quest=numeric(v.quest,0,0,20);d.boatPosition={x:numeric(v.boatPosition?.x,4990,-WORLD_HALF,WORLD_HALF),z:numeric(v.boatPosition?.z,950,-WORLD_HALF,WORLD_HALF)};return d}
export function hasItem(state,item){return (state.inventory[item]||0)>0}
export function addItems(state,loot){for(const [key,value]of Object.entries(loot)){state.inventory[key]=(state.inventory[key]||0)+value}}
export function unlockSite(state,site){if(state.collected.includes(site.id))return {ok:false,message:"Déjà exploré : "+site.label};
 if(site.type==="key"){state.inventory[site.item]=(state.inventory[site.item]||0)+1;state.collected.push(site.id);return {ok:true,message:"Trouvé : "+ITEM_NAMES[site.item]}}
 if(site.required&&!hasItem(state,site.required))return {ok:false,locked:true,message:"Verrouillé — clé requise : "+ITEM_NAMES[site.required]};
 if(site.loot){if(site.required)state.unlocked.push(site.id);addItems(state,site.loot);state.collected.push(site.id);return {ok:true,message:site.label+" ouvert · butin récupéré"}}
 return {ok:true,message:site.label};
}
export function buildStructure(state,type,x,z){const price=type==="shelter"?{wood:10,scrap:3}:type==="fire"?{wood:5}:{};
 if(!Object.keys(price).length)return {ok:false,message:"Construction inconnue"};
 for(const [id,n]of Object.entries(price))if((state.inventory[id]||0)<n)return {ok:false,message:"Il manque "+ITEM_NAMES[id]+" : "+(n-(state.inventory[id]||0))};
 for(const [id,n]of Object.entries(price))state.inventory[id]-=n;
 const structure={type,x,z};state.structures.push(structure);return {ok:true,structure,message:type==="shelter"?"Abri construit":"Feu de camp installé"}}
export function tickSurvival(state,seconds,running=false){const dt=Math.min(Math.max(0,seconds),0.10);state.elapsed+=Number((dt*Math.max(.1,Math.min(24,Number(state.timeMultiplier)||1))).toFixed(8));state.hunger=clamp(state.hunger-dt*.020*(state.foodDrain??1),0,100);state.thirst=clamp(state.thirst-dt*.036*(state.waterDrain??1),0,100);state.stamina=clamp(state.stamina+(running?-dt*13:dt*8),0,100);if(state.hunger===0||state.thirst===0)state.health=clamp(state.health-dt*1.8,0,100)}
