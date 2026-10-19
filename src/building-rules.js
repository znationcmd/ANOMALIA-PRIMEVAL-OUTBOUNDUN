import {WORLD_HALF} from "./mechanics.js";
export const BUILDING_TYPES={
 hospital:{label:'Hôpital',width:36,depth:26,color:0xc7c8b6},
 police:{label:'Poste de police',width:28,depth:22,color:0x899d9e},
 gendarmerie:{label:'Gendarmerie',width:26,depth:20,color:0x8b9b8a},
 firestation:{label:'Caserne de pompiers',width:36,depth:26,color:0xa17761},
 barracks:{label:'Caserne militaire',width:36,depth:22,color:0x8e9472},
 armory:{label:'Armurerie',width:24,depth:20,color:0x7f8972},
 shop:{label:'Boutique',width:22,depth:18,color:0xb7a585},
 house:{label:'Maison RP',width:20,depth:18,color:0xb4ac98},
 helipad:{label:'Héliport',width:28,depth:28,color:0x777b6d},
 dock:{label:'Port / ponton',width:20,depth:32,color:0x7f7664},
 sandbags:{label:'Couverture de combat',width:5,depth:1.2,color:0x92886a},
 watchtower:{label:'Tour de garde',width:6,depth:6,color:0x707a64},
 barrier:{label:'Barrage routier',width:5,depth:1,color:0x8f9985},
 container:{label:'Conteneur',width:3,depth:7,color:0x637c77}
};
export const RP_SITES=[
 {id:'rp-hospital',type:'hospital',x:90,z:166,yaw:0},
 {id:'rp-police',type:'police',x:-62,z:166,yaw:0},
 {id:'rp-fire',type:'firestation',x:90,z:318,yaw:Math.PI},
 {id:'rp-shop',type:'shop',x:-62,z:242,yaw:0},
 {id:'rp-armory',type:'armory',x:242,z:14,yaw:0},
 {id:'rp-barracks',type:'barracks',x:318,z:-138,yaw:0},
 {id:'rp-military-helipad',type:'helipad',x:394,z:-138,yaw:0},
 {id:'rp-military-tower',type:'watchtower',x:360,z:-190,yaw:0},
 {id:'rp-gendarmerie',type:'gendarmerie',x:-520,z:506,yaw:0},
 {id:'rp-borealis-police',type:'police',x:-2342,z:850,yaw:0},
 {id:'rp-vanta-port',type:'dock',x:4940,z:950,yaw:0},
 {id:'rp-sentinelle-port',type:'dock',x:5820,z:100,yaw:0},
 {id:'rp-village-house',type:'house',x:3500,z:-5815,yaw:0}
];
export function localPoint(object,x,z){const a=object.yaw||0,dx=x-object.x,dz=z-object.z;return {x:dx*Math.cos(a)-dz*Math.sin(a),z:dx*Math.sin(a)+dz*Math.cos(a)}}
export function transformPoint(object,x,z){const a=object.yaw||0;return {x:object.x+x*Math.cos(a)+z*Math.sin(a),z:object.z-x*Math.sin(a)+z*Math.cos(a)}}
export function reserveBuilding(x,z,objects=RP_SITES){return objects.some(o=>{const d=BUILDING_TYPES[o.type];if(!d)return false;const p=localPoint(o,x,z);return Math.abs(p.x)<d.width/2+32&&Math.abs(p.z)<d.depth/2+32})}
export function validatePlacements(value){if(!value||value.schemaVersion!==1||!Array.isArray(value.objects)||value.objects.length>300)throw Error('Plan ANOMALIA invalide (300 objets maximum).');const ids=new Set(RP_SITES.map(o=>o.id));return value.objects.map((o,i)=>{if(!Object.hasOwn(BUILDING_TYPES,o.type)||![o.x,o.z,o.yaw||0].every(Number.isFinite)||Math.abs(o.x)>WORLD_HALF||Math.abs(o.z)>WORLD_HALF)throw Error('Objet de carte invalide : '+i);const id=typeof o.id==='string'?o.id:'placed-'+i;if(ids.has(id))throw Error('Identifiant d’objet dupliqué');ids.add(id);return {id,type:o.type,x:o.x,z:o.z,yaw:o.yaw||0}})}
