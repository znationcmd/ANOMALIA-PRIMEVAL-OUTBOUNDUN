
/** ANOMALIA PRIMEVAL OUTBOUNDUN
 * Deterministic 96 x 96 km open-world terrain and hand-authored landmarks.
 * Distances and positions are metres. No copyrighted game assets.
 */
export const WORLD_HALF_SIZE=48000;
export const CHUNK_SIZE=360;
export const SEA_LEVEL=0;
export const START={x:920,z:680};
export const ISLANDS=[
 {name:"Île du Phare",x:19800,z:900,r:3200,bridge:true},
 {name:"Archipel Obscur",x:29500,z:-5300,r:4400,bridge:false},
 {name:"Terres de Brume",x:-26600,z:-14200,r:5500,bridge:false},
 {name:"Île Titan",x:6000,z:29000,r:5600,bridge:false},
];
export const POIS=[
 {id:"nova",name:"Nova Bastion",type:"city",x:1400,z:1600,r:1250},
 {id:"cendre",name:"Port Cendre",type:"city",x:12200,z:1600,r:1000},
 {id:"ferraille",name:"Ferraille",type:"city",x:-5500,z:3700,r:1400},
 {id:"aeropolis",name:"Aéropolis",type:"city",x:5100,z:-8500,r:1550},
 {id:"sentinelle",name:"Fort Sentinelle",type:"city",x:-9200,z:-4800,r:1050},
 {id:"village",name:"Village des Cendres",type:"village",x:2250,z:2900,r:320},
 {id:"hidden-village",name:"Village secret des Pins",type:"hidden-village",x:-3200,z:-1100,r:260},
 {id:"hidden-village-2",name:"Village des Égarés",type:"hidden-village",x:3700,z:-2700,r:240},
 {id:"bunker-alpha",name:"Bunker Alpha",type:"bunker",x:650,z:1350,key:"key_bunker_alpha"},
 {id:"bunker-zero",name:"Bunker Zéro",type:"bunker",x:-6900,z:3700,key:"key_bunker_zero"},
 {id:"locked-container",name:"Conteneur sécurisé 07",type:"container",x:1170,z:840,key:"key_container"},
 {id:"locked-container-2",name:"Cargaison blindée",type:"container",x:2700,z:3150,key:"key_container"},
 {id:"metro-nova",name:"Métro Nova",type:"metro",x:1030,z:2000},
 {id:"metro-cendre",name:"Métro Port Cendre",type:"metro",x:11900,z:1800},
 {id:"catacomb-nova",name:"Catacombes de Nova",type:"catacomb",x:2250,z:1850},
 {id:"catacomb-ferraille",name:"Cryptes de Ferraille",type:"catacomb",x:-5650,z:3100},
 {id:"harbor-prime",name:"Port des Naufragés",type:"harbor",x:15200,z:300},
 {id:"harbor-isle",name:"Marina du Phare",type:"harbor",x:19700,z:950},
 {id:"harbor-obscur",name:"Anse Obscure",type:"harbor",x:29400,z:-5300},
 {id:"isle-phare",name:"Île du Phare",type:"island",x:19800,z:900},
 {id:"isle-obscure",name:"Archipel Obscur",type:"island",x:29500,z:-5300},
 {id:"isle-brume",name:"Terres de Brume",type:"island",x:-26600,z:-14200},
 {id:"isle-titan",name:"Île Titan",type:"island",x:6000,z:29000},
];
export const BRIDGES=[
 {name:"Pont de l'Exode",from:{x:15500,z:900},to:{x:17700,z:900},width:28},
 {name:"Viaduc des Cendres",from:{x:9000,z:1600},to:{x:12000,z:1600},width:21},
];
function fract(n){return n-Math.floor(n)}
export function hash2(x,z,seed=1){return fract(Math.sin(x*127.1+z*311.7+seed*81.37)*43758.5453123)}
function smooth(t){return t*t*(3-2*t)}
function noise(x,z,seed=7){const i=Math.floor(x),j=Math.floor(z),u=smooth(x-i),v=smooth(z-j);const a=hash2(i,j,seed),b=hash2(i+1,j,seed),c=hash2(i,j+1,seed),d=hash2(i+1,j+1,seed);return (a+(b-a)*u)*(1-v)+(c+(d-c)*u)*v}
function fbm(x,z){let a=0,f=1,amp=1,n=0;for(let k=0;k<5;k++){a+=(noise(x*f,z*f,47+k)-.5)*amp;n+=amp;f*=2;amp*=.48}return a/n}
export function heightAt(x,z){
 const d=Math.hypot(x*.92,z);
 const mainland=Math.max(0,1-Math.pow(d/17500,1.65));
 let land=mainland*80;
 for(const island of ISLANDS){const distance=Math.hypot(x-island.x,z-island.z);const shape=Math.max(0,1-Math.pow(distance/island.r,1.55));land=Math.max(land,shape*80)}
 let mountain=0;
 for(const [cx,cz,height,r] of [[-2600,-7800,285,5100],[6200,-6300,230,4700],[-12500,4600,320,4500],[3500,10200,185,4400],[19800,1200,105,1600],[30500,-5400,190,2400]]){
   const dx=x-cx,dz=z-cz;
   const ridge=Math.max(0,1-Math.hypot(dx,dz)/r);
   mountain+=Math.pow(ridge,1.85)*height;
 }
 let result=-37+land+mountain+fbm(x/950,z/950)*45* Math.max(.12,land/70) +fbm(x/140,z/140)*9*Math.max(.08,land/75);
 // Roads and built-up settlements flatten the local ground without loading textures.
 for(const poi of POIS){
  if(!["city","village","hidden-village"].includes(poi.type))continue;
  const dst=Math.hypot(x-poi.x,z-poi.z),radius=poi.r||250;
  if(dst<radius){const t=Math.min(1,Math.max(0,(dst-radius*.65)/(radius*.35)));const flatten=smooth(t);result=result*flatten+(22+mountain*.12)*(1-flatten)}
 }
 return Math.max(-95,result);
}
export function biomeAt(x,z){
 const y=heightAt(x,z);
 if(y<=2)return "ocean";
 if(y<=13)return "beach";
 if(y>155)return "snow";
 if(y>87)return "alpine";
 if(noise(x/2100,z/2100,78)>.59)return "forest";
 if(noise(x/800,z/800,29)>.59)return "dry";
 return "grassland";
}
export function nearestPoi(x,z,types=undefined){
 let best=null,bestDistance=Infinity;
 for(const p of POIS){if(types&&!types.includes(p.type))continue;const d=Math.hypot(x-p.x,z-p.z);if(d<bestDistance){best=p;bestDistance=d}}
 return best?{...best,distance:bestDistance}:null;
}
export function pointsInRange(x,z,radius,types=undefined){return POIS.filter(p=>(!types||types.includes(p.type))&&(p.x-x)**2+(p.z-z)**2<=radius**2)}
export function chunkCoordinates(x,z){return {cx:Math.floor(x/CHUNK_SIZE),cz:Math.floor(z/CHUNK_SIZE)}}
export function locationType(x,z){return biomeAt(x,z)==="ocean"?"sea":"land"}
export function worldBounds(x,z){return Math.abs(x)<=WORLD_HALF_SIZE&&Math.abs(z)<=WORLD_HALF_SIZE}
export function rngAt(x,z,seed=1){return hash2(Math.round(x),Math.round(z),seed)}
