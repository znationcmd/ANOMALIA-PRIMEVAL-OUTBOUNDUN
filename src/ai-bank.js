export function initializeNPCs(s,definitions){s.npcs??=[];for(const d of definitions)if(!s.npcs.some(n=>n.id===d.id))s.npcs.push({...d,homeX:d.x,homeZ:d.z,hp:100,alive:true,mode:'patrol',recruited:false,cooldown:0,yaw:0});s.cash=Number.isFinite(s.cash)?Math.max(0,s.cash):250;s.bank=Number.isFinite(s.bank)?Math.max(0,s.bank):0;s.bankHistory=Array.isArray(s.bankHistory)?s.bankHistory:[];}
export function bankTransaction(s,kind,amount){const n=Math.floor(Number(amount));if(!Number.isFinite(n)||n<=0||n>1e8)return {ok:false,message:'Montant invalide.'};if(!['deposit','withdraw'].includes(kind))return {ok:false,message:'Opération inconnue.'};const from=kind==='deposit'?'cash':'bank',to=from==='cash'?'bank':'cash';if((s[from]||0)<n)return {ok:false,message:'Solde insuffisant.'};s[from]-=n;s[to]=(s[to]||0)+n;s.bankHistory??=[];s.bankHistory.unshift({kind,amount:n,time:Date.now()});s.bankHistory=s.bankHistory.slice(0,50);return {ok:true,message:kind==='deposit'?'Crédits déposés.':'Crédits retirés.'}}
export function recruitNPC(s,id){const n=(s.npcs||[]).find(n=>n.id===id&&n.alive);if(!n||n.faction!=='friendly'||Math.hypot(n.x-s.position.x,n.z-s.position.z)>5)return {ok:false,message:'Approche d’un survivant allié.'};if(n.recruited){n.mode=n.mode==='follow'?'stay':'follow';return {ok:true,message:n.mode==='follow'?'Il te suit.':'Il attend ici.'}}const cost=n.recruitCost||0;if((s.cash||0)<cost)return {ok:false,message:cost+' crédits en espèces nécessaires.'};s.cash-=cost;n.recruited=true;n.mode='follow';return {ok:true,message:n.name+' rejoint ton groupe.'}}
export function tickNPCs(s,dt,{move,clearShot,now=0}){
 dt=Math.min(.1,Math.max(0,dt));for(const n of s.npcs||[]){if(!n.alive)continue;n.cooldown=Math.max(0,(n.cooldown||0)-dt);
  const distance=Math.hypot(n.x-s.position.x,n.z-s.position.z);let tx=n.x,tz=n.z;
  const target=n.faction==='hostile'?{x:s.position.x,z:s.position.z,player:true}:(s.npcs||[]).find(e=>e.alive&&e.faction==='hostile'&&Math.hypot(e.x-n.x,e.z-n.z)<22);
  const range=target?Math.hypot(target.x-n.x,target.z-n.z):Infinity;
  if(target&&range<35&&!s.underground&&clearShot(n,target)){
   if(range>12){tx=target.x;tz=target.z}
   if(range<27&&n.cooldown===0){n.cooldown=1.5;if(target.player){if(!s.godMode)s.health=Math.max(0,s.health-7*(s.aiDamage??1))}else{target.hp-=18;if(target.hp<=0){target.alive=false;if(!target.rewarded){target.rewarded=true;s.cash=(s.cash||0)+25}}}}
  }else if(n.recruited&&n.mode==='follow'&&distance>4){tx=s.position.x;tz=s.position.z;if(distance>100){n.x=s.position.x+3;n.z=s.position.z+3}}
  else if(!n.recruited){tx=n.homeX+Math.sin(now*.025+n.homeX)*12;tz=n.homeZ+Math.cos(now*.025+n.homeX)*12}
  const d=Math.hypot(tx-n.x,tz-n.z);if(d>.5){const step=Math.min(d,dt*(n.recruited?4.8:2.4));const p=move({x:n.x,z:n.z},(tx-n.x)/d*step,(tz-n.z)/d*step);n.x=p.x;n.z=p.z;n.yaw=Math.atan2(tx-n.x,tz-n.z)}
 }
}
