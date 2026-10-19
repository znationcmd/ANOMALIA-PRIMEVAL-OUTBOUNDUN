export const BEACH_SPAWN={x:435,z:90};
export function startBeachJourney(s){
 Object.assign(s,{position:{...BEACH_SPAWN},yaw:0,health:90,stamina:80,hunger:65,thirst:25,temperature:35.8,ammo:0,hands:null,weapon:'pistol',inventory:{wood:5,cloth:2,food:1,bandage:1},inventoryStacks:[],equipment:{head:null,torso:'shirt',vest:null,legs:'jeans',feet:'boots',back:null},ecologyStarterKit:true,inventoryMigration:true,beachJourney:{waterDrunk:false,completed:false}});
 s.groundDrops=[{uid:'beach-water',id:'water',count:1,x:435,z:88,underground:null},{uid:'beach-coat',id:'coat',count:1,x:435,z:78,underground:null},{uid:'beach-bandage',id:'bandage',count:2,x:428,z:81,underground:null}];
 return s;
}
export function beachObjective(s){
 if(!s.beachJourney)return null;
 if(!s.beachJourney.waterDrunk)return {title:'Réveil sur la plage',description:(s.inventory.water||0)>0?'Bois l’eau potable : ouvre le sac (I), sélectionne l’eau et clique sur Utiliser.':'Tu as froid et soif. Fouille les affaires échouées devant toi : approche-toi, puis E pour récupérer l’eau potable.'};
 if(!['coat','jacket'].includes(s.equipment?.torso))return {title:'Trouver des vêtements chauds',description:'Cherche le manteau près des affaires échouées. Récupère-le avec E puis équipe-le depuis le sac (I).'};
 s.beachJourney.completed=true;
 return {title:'Prêt à quitter la plage',description:'Tu as bu et trouvé des vêtements chauds. Rejoins Hélion à l’ouest pour chercher des provisions, un abri et des véhicules.'};
}
export function reserveBeach(x,z){return Math.hypot(x-BEACH_SPAWN.x,z-BEACH_SPAWN.z)<105;}
