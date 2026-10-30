
/** Gameplay systems for the original open world ANOMALIA’Z PRIGIMALIA.
 * All game state is local; no in-game payments or third party credentials.
 */
export const ITEM_DEFS={
 thatch:{label:"Branchages",weight:0.12,kind:"material"},
 fungal_wood:{label:"Bois fongique",weight:0.6,kind:"material"},
 flint:{label:"Silex",weight:0.4,kind:"material"},
 fur:{label:"Fourrure",weight:0.3,kind:"material"},
 wool:{label:"Laine",weight:0.3,kind:"material"},
 keratin:{label:"Kératine",weight:0.3,kind:"material"},
 chitin:{label:"Chitine",weight:0.25,kind:"material"},
 metal_ore:{label:"Minerai de métal",weight:1.2,kind:"material"},
 metal_ingot:{label:"Lingot de métal",weight:1,kind:"material"},
 crystal:{label:"Cristal",weight:0.6,kind:"material"},
 obsidian:{label:"Obsidienne",weight:0.8,kind:"material"},
 oil:{label:"Pétrole",weight:0.8,kind:"material"},
 silica_pearls:{label:"Perles de silice",weight:0.2,kind:"material"},
 charcoal:{label:"Charbon de bois",weight:0.15,kind:"material"},
 gunpowder:{label:"Poudre à canon",weight:0.15,kind:"material"},
 sparkpowder:{label:"Poudre étincelante",weight:0.15,kind:"material"},
 cementing_paste:{label:"Ciment",weight:0.3,kind:"material"},
 achatina_paste:{label:"Pâte d'Achatina",weight:0.3,kind:"material"},
 electronics:{label:"Électroniques",weight:0.2,kind:"material"},
 polymer:{label:"Polymère",weight:0.3,kind:"material"},
 organic_polymer:{label:"Polymère organique",weight:0.3,kind:"material"},
 gasoline:{label:"Essence",weight:0.7,kind:"material"},
 absorbent_substrate:{label:"Substrat absorbant",weight:0.4,kind:"material"},
 black_pearls:{label:"Perles noires",weight:0.2,kind:"material"},
 rare_mushroom:{label:"Champignon rare",weight:0.1,kind:"material"},
 angler_gel:{label:"Gel d'Anguille",weight:0.25,kind:"material"},
 bio_toxin:{label:"Toxine biologique",weight:0.2,kind:"material"},
 leech_blood:{label:"Sang de sangsue",weight:0.2,kind:"material"},
 woolly_rhino_horn:{label:"Corne de rhinocéros laineux",weight:1,kind:"material"},
 sulfur:{label:"Soufre",weight:0.6,kind:"material"},
 silk:{label:"Soie",weight:0.15,kind:"material"},
 sand:{label:"Sable",weight:0.6,kind:"material"},
 green_gem:{label:"Gemme verte",weight:0.3,kind:"material"},
 blue_gem:{label:"Gemme bleue",weight:0.3,kind:"material"},
 red_gem:{label:"Gemme rouge",weight:0.3,kind:"material"},
 condensed_gas:{label:"Gaz condensé",weight:0.7,kind:"material"},
 element:{label:"Élément",weight:0.5,kind:"material"},
 element_shard:{label:"Fragment d'Élément",weight:0.2,kind:"material"},
 element_dust:{label:"Poussière d'Élément",weight:0.05,kind:"material"},
 key_alpha:{label:"Clé Alpha",weight:.03,kind:"key"},
 key_red:{label:"Clé rouge",weight:.03,kind:"key"},
 key_omega:{label:"Clé Omega",weight:.03,kind:"key"},
 key_abyss:{label:"Clé Abysse",weight:.03,kind:"key"},
 key_blue:{label:"Clé bleue",weight:.03,kind:"key"},
 kibble_basic:{label:"Croquettes basiques",weight:.3,kind:"taming"},
 kibble_simple:{label:"Croquettes simples",weight:.3,kind:"taming"},
 kibble_regular:{label:"Croquettes ordinaires",weight:.3,kind:"taming"},
 kibble_superior:{label:"Croquettes supérieures",weight:.3,kind:"taming"},
 kibble_exceptional:{label:"Croquettes exceptionnelles",weight:.3,kind:"taming"},
 kibble_extraordinary:{label:"Croquettes extraordinaires",weight:.3,kind:"taming"},
 honey:{label:"Miel sauvage",weight:.3,kind:"material"},
 rare_flower:{label:"Fleur rare",weight:.05,kind:"material"},
 sap:{label:"Sève",weight:.1,kind:"material"},
 vegetable:{label:"Légumes sauvages",weight:.2,kind:"material"},
 scrap:{label:"Ferraille",weight:.55,kind:"material"},
 ammo:{label:"Munitions de pistolet",weight:.025,kind:"ammo"},
 medkit:{label:"Kit médical",weight:.6,kind:"medical"},
 raw_meat:{label:"Viande crue",weight:.6,kind:"raw"},
 raw_fish:{label:"Poisson cru",weight:.48,kind:"raw"},
 cooked_meat:{label:"Viande grillée",weight:.55,kind:"food"},
 cooked_fish:{label:"Poisson grillé",weight:.43,kind:"food"},
 hide:{label:"Peau animale",weight:.6,kind:"material"},
 feather:{label:"Plume",weight:.07,kind:"material"},
 egg:{label:"Œuf sauvage",weight:.22,kind:"food"},
 fishing_rod:{label:"Canne à pêche",weight:1.2,kind:"tool"},
 tranq_dart:{label:"Fléchette tranquillisante",weight:.1,kind:"ammo"},
 kibble_herbivore:{label:"Croquettes herbivores",weight:.35,kind:"taming"},
 kibble_carnivore:{label:"Croquettes carnivores",weight:.35,kind:"taming"},
 wood:{label:"Bois",weight:.65,kind:"material"},
 stone:{label:"Pierre",weight:1.5,kind:"material"},
 cloth:{label:"Tissu",weight:.3,kind:"material"},
 water:{label:"Eau potable",weight:.8,kind:"drink"},
 food:{label:"Ration",weight:.45,kind:"food"},
 meat:{label:"Viande cuite",weight:.5,kind:"food"},
 medicine:{label:"Antibiotiques",weight:.2,kind:"medical"},
 bandage:{label:"Bandages",weight:.15,kind:"medical"},
 rifle_ammo:{label:"Munitions",weight:.035,kind:"ammo"},
 rifle:{label:"Fusil d'exploration",weight:4.5,kind:"weapon"},
 pistol:{label:"Pistolet",weight:1.2,kind:"weapon"},
 headlamp:{label:"Lampe frontale",weight:.4,kind:"tool"},
 key_bunker_alpha:{label:"Clé Bunker Alpha",weight:.03,kind:"key"},
 key_bunker_zero:{label:"Clé Bunker Zéro",weight:.03,kind:"key"},
 key_container:{label:"Clé conteneur",weight:.03,kind:"key"},
 saddle:{label:"Selle renforcée",weight:5,kind:"saddle"},
 berry:{label:"Baies",weight:.08,kind:"food"},
 fiber:{label:"Fibres",weight:.1,kind:"material"},
 jacket:{label:"Veste tactique",weight:2,kind:"clothing",slot:"torso",capacity:9,warmth:17,protection:6},
 coat:{label:"Manteau d'hiver",weight:3.4,kind:"clothing",slot:"torso",capacity:6,warmth:35,protection:4},
 shirt:{label:"Chemise",weight:.45,kind:"clothing",slot:"torso",capacity:2,warmth:5,protection:0},
 pants:{label:"Pantalon cargo",weight:1.4,kind:"clothing",slot:"legs",capacity:8,warmth:8,protection:2},
 jeans:{label:"Jean",weight:.8,kind:"clothing",slot:"legs",capacity:3,warmth:6,protection:1},
 boots:{label:"Bottes de randonnée",weight:1.6,kind:"clothing",slot:"feet",capacity:1,warmth:8,protection:3},
 helmet:{label:"Casque balistique",weight:1.9,kind:"clothing",slot:"head",capacity:0,warmth:2,protection:16},
 backpack:{label:"Sac d'expédition",weight:2.6,kind:"clothing",slot:"back",capacity:28,warmth:0,protection:0},
 bag:{label:"Petit sac",weight:1.2,kind:"clothing",slot:"back",capacity:12,warmth:0,protection:0},
 vest:{label:"Gilet tactique",weight:2.2,kind:"clothing",slot:"vest",capacity:12,warmth:3,protection:14},
};
export const BASE_CAPACITY=14;
export const EQUIPMENT_SLOTS=["head","torso","vest","legs","feet","back"];
export const DISEASES={
 flu:{label:"Grippe",symptoms:"fatigue, frissons",speed:.85},
 infection:{label:"Infection",symptoms:"fièvre, perte de santé",speed:1.8},
 poisoning:{label:"Intoxication",symptoms:"déshydratation",speed:1.3},
};
export function initialState(){
 return {
  version:2,seed:7462,clock:9*60,x:920,z:680,interior:null,
  health:100,hunger:100,thirst:100,stamina:100,temperature:37,infection:0,illness:null,
  equipment:{head:null,torso:"shirt",vest:null,legs:"jeans",feet:"boots",back:null},
  inventory:{water:3,food:3,bandage:2,wood:4,stone:4,berry:2,rifle_ammo:24,pistol:1},
  weapon:"pistol",ammo:12,magazine:12,shots:0,
  keys:[],opened:[],built:[],tamed:[],kills:0,experience:0,mounted:null,boat:null,
  explored:[],status:""
 };
}
export function invCount(s,id){return Math.max(0,Number(s.inventory?.[id]||0))}
export function hasItem(s,id,n=1){return invCount(s,id)>=n}
export function weight(s){return Object.entries(s.inventory).reduce((n,[id,q])=>n+(ITEM_DEFS[id]?.weight||1)*q,0)}
export function capacity(s){return BASE_CAPACITY+Object.values(s.equipment).reduce((n,id)=>n+(ITEM_DEFS[id]?.capacity||0),0)}
export function warmth(s){return Object.values(s.equipment).reduce((n,id)=>n+(ITEM_DEFS[id]?.warmth||0),0)}
export function protection(s){return Object.values(s.equipment).reduce((n,id)=>n+(ITEM_DEFS[id]?.protection||0),0)}
export function canTake(s,id,count=1){return !!ITEM_DEFS[id]&&count>0&&weight(s)+ITEM_DEFS[id].weight*count<=capacity(s)+1e-7}
export function addItem(s,id,count=1){
 if(!canTake(s,id,count))return {ok:false,message:"Pas assez de place dans les vêtements ou le sac."};
 s.inventory[id]=invCount(s,id)+count;
 return {ok:true,message:"+ "+count+" "+ITEM_DEFS[id].label};
}
export function takeItem(s,id,count=1){
 if(!hasItem(s,id,count))return false;
 s.inventory[id]-=count;if(s.inventory[id]<=0)delete s.inventory[id];return true;
}
export function equip(s,id){
 const def=ITEM_DEFS[id];
 if(!def||def.kind!=="clothing"||!hasItem(s,id))return {ok:false,message:"Vêtement introuvable."};
 const previous=s.equipment[def.slot];
 // A garment is removed from the inventory and worn; the replaced one returns to the inventory.
 takeItem(s,id);
 s.equipment[def.slot]=id;
 if(previous)s.inventory[previous]=invCount(s,previous)+1;
 return {ok:true,message:"Équipement : "+def.label,capacity:capacity(s),overloaded:weight(s)>capacity(s)};
}
export function unequip(s,slot){
 if(!EQUIPMENT_SLOTS.includes(slot))return false;
 const item=s.equipment[slot];if(!item)return false;
 s.equipment[slot]=null;s.inventory[item]=invCount(s,item)+1;
 return true;
}
export function consume(s,id){
 if(!hasItem(s,id))return {ok:false,message:"Objet absent."};
 switch(id){
  case "food":case "meat":case "cooked_meat":case "cooked_fish":s.hunger=Math.min(100,s.hunger+(id==="food"?27:id==="cooked_fish"?29:34));break;
  case "berry":s.hunger=Math.min(100,s.hunger+7);s.thirst=Math.min(100,s.thirst+3);break;
  case "water":s.thirst=Math.min(100,s.thirst+38);if(s.beachJourney)s.beachJourney.waterDrunk=true;break;
  case "medkit":s.health=Math.min(100,s.health+50);break;
  case "bandage":s.health=Math.min(100,s.health+19);break;
  case "medicine":s.illness=null;s.infection=Math.max(0,s.infection-75);s.health=Math.min(100,s.health+7);break;
  default:return {ok:false,message:"Cet objet n'est pas consommable."};
 }
 takeItem(s,id);return {ok:true,message:"Utilisé : "+ITEM_DEFS[id].label};
}
export function survivalTick(s,dt,biome="grassland",weather="clear"){
 const f=Math.min(dt,5);
 s.clock=(s.clock+f*.19)%1440;
 s.hunger=Math.max(0,s.hunger-f*.14*(s.foodDrain??1));
 s.thirst=Math.max(0,s.thirst-f*.27*(s.waterDrain??1));
 let environmental=biome==="snow"?-22:biome==="alpine"?-12:biome==="beach"?2:biome==="dry"?7:-2;
 if(weather==="rain")environmental-=8;
 const clothing=warmth(s)*.45;
 const target=37+(environmental+clothing-12)*.085;
 s.temperature+=Math.max(-.12*f,Math.min(.12*f,(target-s.temperature)*f*.036));
 if(s.thirst<=0||s.hunger<=0)s.health=Math.max(0,s.health-f*.7);
 if(s.temperature<35.5&&!s.illness&&Math.random()<f*.0015)s.illness="flu";
 if(s.temperature>40.2)s.thirst=Math.max(0,s.thirst-f*.4);
 if(s.illness){
  const illness=DISEASES[s.illness];
  if(illness){s.infection=Math.min(100,s.infection+f*illness.speed*.3);s.stamina=Math.max(0,s.stamina-f*.35);
   if(s.infection>40)s.health=Math.max(0,s.health-f*illness.speed*.19)}
 }
 if(s.interior==="catacomb"&&Math.random()<f*.001&&!s.illness)s.illness="infection";
 return {health:s.health,hunger:s.hunger,thirst:s.thirst,temp:s.temperature,illness:s.illness};
}
export function rewardLoot(s,seed){
 const table=["water","food","bandage","medicine","wood","stone","cloth","rifle_ammo","jacket","pants","bag","backpack","helmet","vest","saddle","rifle","key_bunker_alpha","key_container","key_bunker_zero","fiber"];
 const id=table[Math.abs(seed)%table.length];
 const quantity=id==="wood"||id==="stone"?3:id==="rifle_ammo"?12:1;
 return {...addItem(s,id,quantity),item:id};
}
export function openLocked(s,poi){
 if(s.opened.includes(poi.id))return {ok:true,message:"Déjà ouvert.",alreadyOpen:true};
 if(poi.key&&!hasItem(s,poi.key))return {ok:false,message:"Accès verrouillé : "+ITEM_DEFS[poi.key]?.label+". Trouve la clé dans les caisses."};
 s.opened.push(poi.id);
 return {ok:true,message:"Ouvert : "+poi.name};
}
export function craft(s,kind,position){
 const recipes={shelter:{wood:6,stone:4},campfire:{wood:4,stone:2},saddle:{fiber:6,cloth:4}};
 const recipe=recipes[kind];if(!recipe)return {ok:false,message:"Plan inconnu."};
 if(!Object.entries(recipe).every(([id,amount])=>hasItem(s,id,amount)))return {ok:false,message:"Matériaux insuffisants : "+Object.entries(recipe).map(([id,n])=>n+" "+ITEM_DEFS[id].label).join(", ")};
 for(const [id,n]of Object.entries(recipe))takeItem(s,id,n);
 if(kind==="saddle")return addItem(s,"saddle",1);
 const build={id:"build-"+Date.now()+"-"+Math.floor(Math.random()*9999),kind,x:position.x,z:position.z};
 s.built.push(build);return {ok:true,message:"Construction : "+kind,build};
}
export const DINO_TYPES=[
 {id:"stegosaur",label:"Stégosaure",speed:11,food:"berry",saddle:true},
 {id:"raptor",label:"Raptor",speed:24,food:"meat",saddle:true},
 {id:"triceratops",label:"Tricératops",speed:13,food:"berry",saddle:true},
 {id:"bront",label:"Titan herbivore",speed:9,food:"berry",saddle:true},
];
export function tame(s,dino){
 if(!dino||dino.tamed)return {ok:false,message:"Créature déjà apprivoisée ou absente."};
 const def=DINO_TYPES.find(x=>x.id===dino.type)||DINO_TYPES[0];
 const food=hasItem(s,def.food)?def.food:(def.food==="meat"&&hasItem(s,"food")?"food":null);
 if(!food)return {ok:false,message:"Pour apprivoiser : il faut "+ITEM_DEFS[def.food].label.toLowerCase()+"."};
 takeItem(s,food);
 dino.trust=Math.min(100,(dino.trust||0)+34);
 if(dino.trust>=100){dino.tamed=true;s.tamed.push({id:dino.id,type:dino.type,name:def.label,hasSaddle:false});return {ok:true,message:def.label+" apprivoisé ! Fabrique ou trouve une selle."}}
 return {ok:true,message:"Apprivoisement "+dino.trust+" %. Continue à nourrir."};
}
export function saddleMount(s,dino){
 const pet=s.tamed.find(x=>x.id===dino.id);
 if(!pet)return {ok:false,message:"Ce dinosaure n'est pas apprivoisé."};
 if(!pet.hasSaddle){
  if(!takeItem(s,"saddle"))return {ok:false,message:"Il faut une selle pour monter."};
  pet.hasSaddle=true;
 }
 s.mounted=dino.id;return {ok:true,message:"Tu montes "+pet.name};
}
export function breed(s,first,second){
 const a=s.tamed.find(x=>x.id===first),b=s.tamed.find(x=>x.id===second);
 if(!a||!b||a.id===b.id||a.type!==b.type)return {ok:false,message:"Il faut deux dinosaures apprivoisés de la même espèce."};
 if(!hasItem(s,"food",2)&&!hasItem(s,"berry",4))return {ok:false,message:"Nourriture d'élevage insuffisante."};
 if(hasItem(s,"berry",4))takeItem(s,"berry",4);else takeItem(s,"food",2);
 const child={id:"offspring-"+Date.now(),type:a.type,name:"Jeune "+a.name,hasSaddle:false,born:s.clock};
 s.tamed.push(child);return {ok:true,message:"Naissance : "+child.name,child};
}
export const SAVE_KEY="anomalia-primeval-outboundun-save-v1";
export function serialize(s){return JSON.stringify(s)}
export function hydrate(text){try{
 const input=JSON.parse(text);if(!input||typeof input!=="object"||!Number.isFinite(input.x)||!Number.isFinite(input.z))return initialState();
 const base=initialState();const v={...base,...input,inventory:{...base.inventory,...(input.inventory||{})},equipment:{...base.equipment,...(input.equipment||{})}};
 for(const k of ["health","hunger","thirst","stamina","infection"]){v[k]=Math.max(0,Math.min(100,Number(v[k])||0))}
 for(const k of ["opened","built","tamed","explored"]){if(!Array.isArray(v[k]))v[k]=[];v[k]=v[k].slice(0,2000)}
 return v;
}catch{return initialState()}}
