/** ANOMALIA - food chain, fauna and non-lethal dinosaur taming.
 * Deterministic gameplay functions, separately tested without WebGL.
 */
export const JUNGLE_ZONES=[
 {id:"jungle-brume",name:"Jungle des Brumes",x:-1650,z:1450,radius:880},
 {id:"jungle-oubli",name:"Jungle Oubliée",x:1550,z:850,radius:710},
 {id:"jungle-sentinelle",name:"Forêt Équatoriale Sentinelle",x:6400,z:400,radius:540},
 {id:"jungle-caldera",name:"Jungle des Ruines",x:2300,z:-2650,radius:580}
];
export const WILDLIFE={
 deer:{name:"Cerf",habitat:"land",hp:64,drop:{raw_meat:3,hide:2},speed:4},
 boar:{name:"Sanglier",habitat:"land",hp:80,drop:{raw_meat:4,hide:2},speed:3,hostile:true},
 bird:{name:"Dindon sauvage",habitat:"land",hp:26,drop:{raw_meat:2,feather:3,egg:1},speed:2},
 jaguar:{name:"Jaguar",habitat:"jungle",hp:95,drop:{raw_meat:3,hide:3},speed:6,hostile:true},
 crocodile:{name:"Crocodile",habitat:"shore",hp:170,drop:{raw_meat:5,hide:4},speed:3,hostile:true},
 shark:{name:"Requin",habitat:"ocean",hp:190,drop:{raw_fish:6},speed:7,hostile:true}
};
export const KIBBLE_RECIPES={
 kibble_herbivore:{berry:6,egg:1,cooked_fish:1},
 kibble_carnivore:{cooked_meat:2,egg:1,berry:2}
};
export const COOKING_RECIPES={raw_meat:"cooked_meat",raw_fish:"cooked_fish"};
const foodPreference={stegosaur:"kibble_herbivore",triceratops:"kibble_herbivore",bront:"kibble_herbivore",raptor:"kibble_carnivore"};
const count=(s,id)=>Math.max(0,Number(s.inventory?.[id]||0));
function remove(s,id,amount=1){if(count(s,id)<amount)return false;s.inventory[id]-=amount;if(s.inventory[id]<=0)delete s.inventory[id];return true}
function add(s,id,amount=1){s.inventory[id]=count(s,id)+amount}
export function inJungle(x,z,height=20){
 if(height<6||height>170)return false;
 return JUNGLE_ZONES.some(a=>(x-a.x)**2+(z-a.z)**2<a.radius*a.radius);
}
export function habitatSpecies({height,biome,roll=0}){
 const r=Math.max(0,Math.min(.99999,Number(roll)||0));
 if(height< -3)return r<.53?"shark":null;
 if(height>=-3&&height<8)return r<.66?"crocodile":r<.82?"bird":null;
 if(biome==="jungle")return r<.43?"jaguar":r<.68?"deer":"bird";
 if(height<190&&height>5)return r<.34?"deer":r<.73?"boar":"bird";
 return null;
}
/** Precomputed wild animals remain stable per world chunk and terrain seed. */
export function wildlifeSpawn(cx,cz,world,limit=2){
 const {chunkSize,hash,heightAt,biomeAt}=world;
 const result=[];
 for(let n=0;n<limit*6&&result.length<limit;n++){
  const x=(cx+.13+hash(cx*91+n,cz*31+7)*.72)*chunkSize;
  const z=(cz+.13+hash(cx*17+n,cz*59+22)*.72)*chunkSize;
  const h=heightAt(x,z),biome=biomeAt(x,z);
  const species=habitatSpecies({height:h,biome,roll:hash(cx*77+n,cz*43+n)});
  if(!species)continue;
  result.push({id:"wild-"+cx+"-"+cz+"-"+n,type:species,x,z,hp:WILDLIFE[species].hp});
 }
 return result;
}
export function huntAnimal(s,animal){
 if(!animal||!WILDLIFE[animal.type])return {ok:false,message:"Animal introuvable."};
 const ids=s.hunted||(s.hunted=[]);
 if(ids.includes(animal.id))return {ok:false,message:"Animal déjà dépecé."};
 ids.push(animal.id);
 const drops=WILDLIFE[animal.type].drop;
 for(const [id,n] of Object.entries(drops))add(s,id,n);
 return {ok:true,message:"Chasse : "+WILDLIFE[animal.type].name+" · "+Object.entries(drops).map(([id,n])=>id+" ×"+n).join(", "),drops};
}
/** Search natural nests and plants. Eggs are needed for species-specific kibble. */
export function forageSupplies(s,{jungle=false,roll=0}={}){
 const r=Math.max(0,Math.min(.99999,Number(roll)||0));
 const item=r< (jungle?.38:.18)?"egg":r<.70?"berry":"fiber";
 const quantity=item==="egg"?1:item==="berry"?4:3;
 add(s,item,quantity);
 return {ok:true,item,quantity,message:"Récolte : "+item+" ×"+quantity};
}
export function fishAt(s,{nearWater,roll=0}){
 if(!nearWater)return {ok:false,message:"Approche-toi d'une rivière, d'une plage ou utilise un bateau."};
 if(count(s,"fishing_rod")<1)return {ok:false,message:"Il te faut une canne à pêche (dans l'inventaire)."};
 if(roll<.27)return {ok:false,message:"Le poisson s'est échappé. Réessaie."};
 const catchCount=roll>.92?3:roll>.7?2:1;
 add(s,"raw_fish",catchCount);
 return {ok:true,message:"Pêche : "+catchCount+" poisson(s) attrapé(s).",amount:catchCount};
}
export function cookFood(s,raw,nearFire){
 const result=COOKING_RECIPES[raw];
 if(!result)return {ok:false,message:"Aucune recette pour cet ingrédient."};
 if(!nearFire)return {ok:false,message:"Allume un feu de camp à proximité pour cuisiner."};
 if(!remove(s,raw))return {ok:false,message:"Il te manque : "+raw};
 add(s,result);
 return {ok:true,message:"Cuisson : "+result+" prêt à manger.",item:result};
}
export function craftSurvival(s,item){
 let recipe=null;
 if(item==="tranq_dart")recipe={scrap:1,cloth:1,berry:2};
 else if(item==="fishing_rod")recipe={wood:3,fiber:2};
 else recipe=KIBBLE_RECIPES[item];
 if(!recipe)return {ok:false,message:"Recette inconnue."};
 const missing=Object.entries(recipe).filter(([id,n])=>count(s,id)<n);
 if(missing.length)return {ok:false,message:"Matériaux manquants : "+missing.map(([id,n])=>id+" ×"+n).join(", ")};
 for(const [id,n] of Object.entries(recipe))remove(s,id,n);
 add(s,item,item==="tranq_dart"?3:1);
 return {ok:true,message:"Fabriqué : "+item+(item==="tranq_dart"?" ×3":"")};
}
export function tranquilize(s,dino){
 if(!dino||dino.tamed)return {ok:false,message:"Cible sauvage introuvable."};
 if(!remove(s,"tranq_dart"))return {ok:false,message:"Plus de fléchettes tranquillisantes. Fabrique-en dans l'inventaire."};
 dino.torpor=Math.min(140,(Number(dino.torpor)||0)+42);
 dino.unconscious=dino.torpor>=100;
 dino.unconsciousTime=dino.unconscious?110:0;
 return {ok:true,unconscious:dino.unconscious,torpor:dino.torpor,message:dino.unconscious?"Dinosaure endormi ! Approche-toi et donne-lui des croquettes.":"Torpeur : "+Math.round(dino.torpor)+"/100. Continue les fléchettes."};
}
export function tickTorpor(dino,dt){
 if(!dino||dino.tamed)return;
 const t=Math.max(0,Math.min(5,Number(dt)||0));
 if(dino.unconscious){
  dino.unconsciousTime=Math.max(0,(dino.unconsciousTime||0)-t);
  if(dino.unconsciousTime<=0){dino.unconscious=false;dino.torpor=0;dino.tameProgress=0;}
 }else dino.torpor=Math.max(0,(dino.torpor||0)-t*.7);
}
export function tameWithKibble(s,dino){
 if(!dino||dino.tamed)return {ok:false,message:"Ce dinosaure est déjà apprivoisé."};
 if(!dino.unconscious)return {ok:false,message:"Endors d'abord le dinosaure avec des fléchettes tranquillisantes."};
 const required=foodPreference[dino.type]||"kibble_herbivore";
 if(!remove(s,required))return {ok:false,message:"Il faut des croquettes "+(required==="kibble_carnivore"?"carnivores":"herbivores")+". Cuisine et fabrique-les."};
 dino.tameProgress=Math.min(100,(dino.tameProgress||0)+50);
 if(dino.tameProgress<100)return {ok:true,tamed:false,progress:dino.tameProgress,message:"Apprivoisement : "+dino.tameProgress+" % · encore des croquettes nécessaires."};
 dino.tamed=true;dino.unconscious=false;
 s.tamed||=[];
 if(!s.tamed.some(p=>p.id===dino.id))s.tamed.push({id:dino.id,type:dino.type,name:dino.type,hasSaddle:false});
 return {ok:true,tamed:true,progress:100,message:"Dinosaure apprivoisé ! Selle nécessaire pour le monter."};
}
