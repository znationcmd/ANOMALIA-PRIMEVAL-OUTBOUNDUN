/**
 * UNKNOWN HORROR X — original creatures for the standalone 20x20 km map.
 * Deterministic pure spawn rules; no Unreal actors/assets are created by this file.
 * Coordinates in metres, relative to centre, -10000..10000.
 */
export const HORROR_LAYERS = Object.freeze({
 surface:{label:'Surface',zMin:0,zMax:2000,spawnCap:120},
 metro:{label:'Métro −1',zMin:-90,zMax:-8,spawnCap:65},
 labs:{label:'Laboratoires −2',zMin:-240,zMax:-90,spawnCap:60},
 undergroundCity:{label:'Ville souterraine −3',zMin:-520,zMax:-240,spawnCap:100},
 abyss:{label:'Grottes profondes −4',zMin:-1200,zMax:-520,spawnCap:65}
});
const species=[
 ['zombie_vagabond','Zombie vagabond','zombie',['surface','metro','undergroundCity'],1,65,false],
 ['zombie_coureur','Zombie coureur','zombie',['surface','metro','labs','undergroundCity'],2,90,false],
 ['zombie_mineur','Zombie mineur','zombie',['metro','undergroundCity','abyss'],2,120,false],
 ['zombie_contamine','Zombie contaminé','zombie',['labs','undergroundCity','abyss'],3,170,false],
 ['zombie_colosse','Zombie colosse','zombie',['surface','labs','undergroundCity','abyss'],5,380,false],
 ['wolf','Loup','animal',['surface','metro','abyss'],2,90,true],
 ['bear','Ours','animal',['surface','abyss'],4,280,true],
 ['boar','Sanglier','animal',['surface','metro'],2,85,true],
 ['deer','Cerf','animal',['surface'],1,70,true],
 ['bat','Chauve-souris','animal',['metro','labs','undergroundCity','abyss'],1,20,false],
 ['giant_rat','Rat des galeries','animal',['metro','labs','undergroundCity','abyss'],1,35,false],
 ['cave_crocodile','Crocodile cavernicole','animal',['surface','abyss'],4,210,false],
 ['raptor','Raptor','dinosaur',['surface','metro','undergroundCity'],4,180,true],
 ['triceratops','Tricératops','dinosaur',['surface','undergroundCity'],3,370,true],
 ['stegosaurus','Stégosaure','dinosaur',['surface','undergroundCity'],3,410,true],
 ['carnotaurus','Carnotaurus','dinosaur',['surface','undergroundCity','abyss'],5,530,true],
 ['ankylosaurus','Ankylosaure','dinosaur',['surface','undergroundCity','abyss'],4,460,true],
 ['spinosaurus','Spinosaure','dinosaur',['surface','abyss'],5,800,true],
 ['deinonychus','Deinonychus','dinosaur',['metro','undergroundCity','abyss'],4,260,true]
];
export const HORROR_CREATURES=Object.freeze(Object.fromEntries(species.map(([id,name,kind,layers,danger,hp,tamable])=>[
 id,Object.freeze({id,name,kind,layers:Object.freeze(layers),danger,hp,tamable})
])));
export const HORROR_SPAWN_PROFILES=Object.freeze({
 surface:{zombie:0.45,animal:0.32,dinosaur:0.23},
 metro:{zombie:0.58,animal:0.27,dinosaur:0.15},
 labs:{zombie:0.75,animal:0.25,dinosaur:0},
 undergroundCity:{zombie:0.55,animal:0.15,dinosaur:0.30},
 abyss:{zombie:0.34,animal:0.27,dinosaur:0.39}
});
export const HORROR_SPAWN_ZONES=Object.freeze({
 surface:['villes en ruine','forêts','routes','montagnes','berges'],
 metro:['quais','tunnels','dépôts','gares de correspondance'],
 labs:['couloirs','salles de confinement','maintenance'],
 undergroundCity:['rues','immeubles','places','parkings'],
 abyss:['cavernes','mines','rivières souterraines']
});
const clampRoll=v=>Math.min(.999999,Math.max(0,Number.isFinite(v)?v:0));
const hash=(a,b,seed=1729)=>{
 let n=Math.imul((a|0)^seed,374761393)^Math.imul((b|0)+seed,668265263);
 n=Math.imul(n^(n>>>13),1274126177);
 return ((n^(n>>>16))>>>0)/4294967296;
};
/** No simulation occurs in water. For flooded tunnels pass isFlooded=true. */
export function chooseHorrorSpecies(layer,roll=0,{maxDanger=5}={}){
 const weights=HORROR_SPAWN_PROFILES[layer];
 if(!weights)return null;
 const eligible=Object.values(HORROR_CREATURES).filter(s=>s.layers.includes(layer)&&s.danger<=maxDanger);
 if(!eligible.length)return null;
 const r=clampRoll(roll);
 let category='dinosaur',start=weights.zombie+weights.animal;
 if(r<weights.zombie){category='zombie';start=0}
 else if(r<start){category='animal';start=weights.zombie}
 const pool=eligible.filter(s=>s.kind===category);
 if(!pool.length)return null;
 const weight=weights[category],fraction=weight>0?(r-start)/weight:0;
 return pool[Math.min(pool.length-1,Math.floor(Math.max(0,fraction)*pool.length))].id;
}
/**
 * Create stable spawn candidates for one loaded streaming cell, without models.
 * Chunk coordinates are local to UNKNOWN HORROR X; water cells are excluded.
 */
export function generateHorrorSpawns({layer,cx,cz,land=true,isFlooded=false,limit=6,seed=1729,maxDanger=5}){
 if(!HORROR_LAYERS[layer]||!Number.isInteger(cx)||!Number.isInteger(cz))return [];
 if(layer==='surface'&&!land || layer!=='surface'&&isFlooded)return [];
 const total=Math.max(0,Math.min(32,Math.floor(Number(limit)||0))),result=[];
 for(let i=0;i<total;i++){
  const roll=hash(cx*47+i,cz*89+i*7,seed),type=chooseHorrorSpecies(layer,roll,{maxDanger});
  if(!type)continue;
  result.push({id:`uhx:${layer}:${cx}:${cz}:${i}`,type,layer,
   x:cx*256+hash(cx*17+i,cz*31+i,seed)*256,
   y:layer==='surface'?0:(HORROR_LAYERS[layer].zMin+HORROR_LAYERS[layer].zMax)/2,
   z:cz*256+hash(cx*97+i,cz*19+i,seed)*256,
   hp:HORROR_CREATURES[type].hp,danger:HORROR_CREATURES[type].danger});
 }
 return result;
}
export function mayTameHorrorCreature(type){
 const entry=HORROR_CREATURES[type];return Boolean(entry?.tamable&&entry.kind!=='zombie');
}
