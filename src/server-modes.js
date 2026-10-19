/** ANOMALIA PRIMEVAL OUTBOUNDUN — server-owned gameplay rules. */
export const GAME_MODES=Object.freeze({
 rp:{label:"Roleplay (RP)",playerDamage:false,construction:true,adminEditor:true,description:"Rôles et villes RP : aucun dégât entre joueurs sans événement dédié."},
 pvp:{label:"Survie PVP",playerDamage:true,construction:true,adminEditor:true,description:"Combats entre joueurs hors zones protégées désactivées."},
 pve:{label:"Coopération PVE",playerDamage:false,construction:true,adminEditor:true,description:"Survie commune, sans dégâts infligés aux joueurs."},
 mixed:{label:"Mixte RP / PVP / PVE",playerDamage:true,construction:true,adminEditor:true,description:"PVP en dehors des villes protégées ; centres urbains réservés au RP/PVE."}
});
export const SAFE_ZONES=Object.freeze([
 {id:"helion-centre",label:"Centre-ville RP",x:0,z:180,radius:320},
 {id:"borealis-hospital",label:"Hôpital Boréalis",x:-2342,z:850,radius:170},
 {id:"vanta-port",label:"Port de Vanta",x:4940,z:950,radius:190},
 {id:"sentinelle-port",label:"Port Sentinelle",x:5820,z:100,radius:170}
]);
export function validGameMode(mode){return typeof mode==="string"&&Object.hasOwn(GAME_MODES,mode)?mode:"pve"}
export function protectedZone(x,z){return SAFE_ZONES.find(zone=>Math.hypot(zone.x-x,zone.z-z)<zone.radius)||null}
export function canPlayerDamage(mode,attacker,victim){
 const selected=validGameMode(mode);
 if(!GAME_MODES[selected].playerDamage)return false;
 if(!attacker||!victim||attacker.id===victim.id)return false;
 if(selected==="mixed"&&(protectedZone(attacker.x,attacker.z)||protectedZone(victim.x,victim.z)))return false;
 return true;
}
export function permissionsFor(role="player",mode="pve"){
 const admin=role==="owner"||role==="admin";
 return {
  role:admin?role:"player",mode:validGameMode(mode),
  canEditWorld:admin,
  canConfigureServer:role==="owner",
  canKickPlayers:admin,
  canBuild:GAME_MODES[validGameMode(mode)].construction,
  canDamagePlayers:GAME_MODES[validGameMode(mode)].playerDamage
 };
}
