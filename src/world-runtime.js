import {WORLD_HALF} from "./mechanics.js";
import * as THREE from 'three';
import {ITEM_DEFS,DINO_TYPES,capacity,weight,addItem} from './systems.js';
import {moveWithCollisions,groundHeight} from './movement.js';
import {VEHICLES,spawnVehicle,enterVehicle,exitVehicle,tickVehicle,togglePerspective} from './vehicles.js';
import {COMPANION_TYPES,adoptCompanion,companionCommand,feedCompanion,tickCompanion} from './companions.js';
import {initializeNPCs,recruitNPC,tickNPCs,bankTransaction} from './ai-bank.js';
import {DEFAULT_XML,parseWorldConfig,readWorldConfig} from './world-config.js';
import {tickEconomy,EVENT_TYPES} from './economy.js';
import {syncInventory,pickupDrop,nearbyDrops} from './inventory.js';
import {vehicleModel} from './vehicle-models.js';
import {buildSurvivor} from './survivor-preview.js';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function createWorldRuntime({state:s,scene,camera,renderer,heightAt,solids,yaw,save,notice,panel,body,title,open,close,cleanup,spawnDino,enemies}){
 let diskConfigPath='';if(location.protocol==='anomalia:')fetch('./config/location.json').then(r=>r.json()).then(d=>diskConfigPath=d.directory).catch(()=>{});
 let docs={...DEFAULT_XML,...s.xmlOverrides},config=parseWorldConfig(docs),time=0,lastEconomy=-99,enterYaw=0,menu='admin',tab='items',editingFile='';
 s.vehicles=Array.isArray(s.vehicles)?s.vehicles.filter(v=>VEHICLES[v.type]&&[v.x,v.z,v.y,v.yaw].every(Number.isFinite)).slice(0,60):[];s.adminCreatures??=[];s.thirdPerson=!!s.thirdPerson;
 function applySettings(){
  renderer.setPixelRatio(Math.min(Number(localStorage.getItem('anomalia-quality'))||2,2,devicePixelRatio*config.settings.resolution/100));renderer.setSize(innerWidth,innerHeight);renderer.shadowMap.enabled=config.settings.shadows&&!matchMedia('(pointer:coarse)').matches;
  s.dinoKibblePreferences=config.creatures.preferredKibble;s.tamingSpeed=config.settings.tamingSpeed;s.aiDamage=config.settings.aiDamage;s.foodDrain=config.settings.foodDrain;s.waterDrain=config.settings.waterDrain;
  s.thirdPersonAllowed=config.settings.thirdPersonAllowed;if(!s.thirdPersonAllowed)s.thirdPerson=false;
 }
 applySettings();if(!s.configSpawnInitialized){s.configSpawnInitialized=true;if(!s.elapsed){s.position={...config.settings.spawn};for(const [id,n]of Object.entries(config.settings.startingItems))if(ITEM_DEFS[id]&&Number.isFinite(n))s.inventory[id]=Math.max(0,Math.min(9999,Math.floor(n)))}}if(s.beachJourney&&!s.beachCarCreated){spawnVehicle(s,'car',410,155,heightAt);s.beachCarCreated=true;}initializeNPCs(s,config.ai);tickEconomy(s,config,Date.now()/1000);
 const objects=new Map(),npcModels=new Map(),wrecks=new Map();let avatar=null,avatarSignature='',petModel=null,petSignature='';
 const lootGeometry=new THREE.BoxGeometry(.35,.22,.35),lootMaterial=new THREE.MeshStandardMaterial({color:0xbaac7b,roughness:.8});
 const lootMesh=new THREE.InstancedMesh(lootGeometry,lootMaterial,600);lootMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);lootMesh.frustumCulled=false;scene.add(lootMesh);
 const atm=new THREE.Group();atm.position.set(52,heightAt(52,180),180);scene.add(atm);
 const atmMat=new THREE.MeshStandardMaterial({color:0x394b4a,metalness:.3,roughness:.6});const cabinet=new THREE.Mesh(new THREE.BoxGeometry(.8,1.7,.7),atmMat);cabinet.position.y=.85;atm.add(cabinet);
 const screen=new THREE.Mesh(new THREE.BoxGeometry(.55,.42,.02),new THREE.MeshStandardMaterial({color:0x64c6b7,emissive:0x247265}));screen.position.set(0,1.2,-.36);atm.add(screen);
 function label(text,color='#cae0c8'){
  const canvas=document.createElement('canvas');canvas.width=384;canvas.height=64;const ctx=canvas.getContext('2d');ctx.fillStyle='#101a1bc9';ctx.fillRect(0,0,384,64);ctx.fillStyle=color;ctx.font='bold 24px system-ui';ctx.textAlign='center';ctx.fillText(String(text).slice(0,28),192,41);
  const tex=new THREE.CanvasTexture(canvas);tex.colorSpace=THREE.SRGBColorSpace;const sprite=new THREE.Sprite(new THREE.SpriteMaterial({map:tex,transparent:true,depthTest:true}));sprite.scale.set(2.8,.47,1);return sprite;
 }
 const atmLabel=label('BANQUE · E');atmLabel.position.set(0,2.2,0);atm.add(atmLabel);
 function dispose(object){object?.dispose?.();object?.root?.removeFromParent()}
 function clearShot(a,b){
  const active=s.vehicles.find(v=>v.id===s.activeVehicle);if(b.player&&active&&active.y>groundHeight(active.x,active.z,heightAt)+5)return false;
  const distance=Math.hypot(b.x-a.x,b.z-a.z),steps=Math.ceil(distance/1.5);for(let i=1;i<steps;i++){const x=a.x+(b.x-a.x)*i/steps,z=a.z+(b.z-a.z)*i/steps;if(solids().some(s=>Math.abs(x-s.x)<s.width/2&&Math.abs(z-s.z)<s.depth/2))return false}return true;
 }
 const move=(p,dx,dz)=>moveWithCollisions(p,dx,dz,solids(),(x,z,nx,nz)=>Math.abs(groundHeight(nx,nz,heightAt)-groundHeight(x,z,heightAt))<2&&groundHeight(nx,nz,heightAt)>-1);
 function configure(nextDocs){const next=parseWorldConfig(nextDocs);docs={...nextDocs};config=next;applySettings();s.xmlOverrides={...nextDocs};s.groundDrops=(s.groundDrops||[]).filter(d=>!d.uid.startsWith('ce-')&&!d.uid.startsWith('event-'));s.worldEvents=[];s.lootTimers={};s.eventTimers={};initializeNPCs(s,next.ai);configurePositions();tickEconomy(s,config,Date.now()/1000);save();}
 readWorldConfig(s.xmlOverrides).then(data=>{docs=data.docs;config=data.config;applySettings();initializeNPCs(s,config.ai);configurePositions();lastEconomy=-99}).catch(e=>notice(e.message));
 function pet(){const p=s.companion;if(!p)return null;if(!petModel||petSignature!==p.species){dispose(petModel);petSignature=p.species;const root=new THREE.Group(),fur=new THREE.MeshStandardMaterial({color:p.species==='wolf'?0x777770:p.species==='raptor'?0x68784a:0x80634d,roughness:1});const mesh=(g,x,y,z)=>{const m=new THREE.Mesh(g,fur);m.position.set(x,y,z);root.add(m);return m};
   mesh(new THREE.SphereGeometry(.5,14,10),0,.65,0).scale.set(.65,.6,1.4);mesh(new THREE.SphereGeometry(.24,14,10),0,1,-.7);mesh(new THREE.BoxGeometry(.23,.18,.35),0,.95,-.92);
   const legs=[];for(const x of [-.23,.23])for(const z of [-.4,.4])legs.push(mesh(new THREE.CapsuleGeometry(.065,.42,4,8),x,.28,z));
   for(const x of [-.15,.15])mesh(new THREE.ConeGeometry(.09,.23,6),x,1.24,-.72);const tail=mesh(new THREE.ConeGeometry(.10,.65,8),0,.8,.95);tail.rotation.x=Math.PI/3;
   const name=label(p.name);name.position.y=1.75;root.add(name);scene.add(root);petModel={root,legs,dispose(){root.traverse(o=>{o.geometry?.dispose();o.material?.map?.dispose();o.material?.dispose()})}};
  }return petModel;
 }
 function configurePositions(){for(const d of [...s.adminCreatures,...config.creatures.spawns])spawnDino(d,false)}configurePositions();
 const vehicle=()=>s.vehicles.find(v=>v.id===s.activeVehicle);
 function drive(forward,strafe,dt,keys){const v=vehicle();if(!v)return false;tickVehicle(v,{forward,turn:-strafe,up:keys.has('Space'),down:keys.has('ControlLeft')||keys.has('ControlRight'),brake:keys.has('KeyX')},dt,{heightAt,solids:solids(),fuelRate:config.globals.VehicleFuelConsumption??.03});s.position={x:v.x,z:v.z};return true}
 function interact(){
  const v=vehicle();if(v){notice(exitVehicle(s,heightAt,solids()).message);save();return true}
  const nearVehicle=s.vehicles.find(v=>Math.hypot(v.x-s.position.x,v.z-s.position.z)<7);
  if(nearVehicle&&!s.underground){const result=enterVehicle(s,nearVehicle.id);enterYaw=yaw();notice(result.message);save();return true}
  if(!s.underground&&Math.hypot(s.position.x-52,s.position.z-180)<4){show('bank');return true}
  const npc=(s.npcs||[]).find(n=>n.alive&&n.faction==='friendly'&&Math.hypot(n.x-s.position.x,n.z-s.position.z)<4);if(npc){notice(recruitNPC(s,npc.id).message);save();return true}
  const drop=nearbyDrops(s).sort((a,b)=>Math.hypot(a.x-s.position.x,a.z-s.position.z)-Math.hypot(b.x-s.position.x,b.z-s.position.z))[0];if(drop&&Math.hypot(drop.x-s.position.x,drop.z-s.position.z)<3){notice(pickupDrop(s,drop.uid).message);save();return true}
  return false;
 }
 function update(dt,now,active){
  time=now;if(active){
   if(now-lastEconomy>2){lastEconomy=now;tickEconomy(s,config,Date.now()/1000)}
   tickNPCs(s,dt,{move,clearShot,now});tickCompanion(s,dt,{heightAt,move,followDistance:config.globals.CompanionFollowDistance??3,teleportDistance:config.globals.CompanionTeleportDistance??90,enemies:enemies()});
   if(s.godMode){s.health=100;s.hunger=100;s.thirst=100;}
  }
  for(const v of s.vehicles){if(!objects.has(v.id)){const model=vehicleModel(v.type);objects.set(v.id,model);scene.add(model.root)}const o=objects.get(v.id);o.setCockpit?.(s.activeVehicle===v.id&&s.vehicleView==='inside');o.root.position.set(v.x,v.y,v.z);o.root.rotation.y=v.yaw;o.update(v.speed,0,now);o.root.visible=!s.underground;}
  for(const [id,model]of objects)if(!s.vehicles.some(v=>v.id===id)){dispose(model);objects.delete(id)}
  let li=0;const dummy=new THREE.Object3D();for(const d of s.groundDrops||[]){if(li>=600)break;if((d.underground||null)!==(s.underground||null)||Math.hypot(d.x-s.position.x,d.z-s.position.z)>100)continue;dummy.position.set(d.x,s.underground?-27.2:Math.max(groundHeight(d.x,d.z,heightAt),0)+.22,d.z);dummy.rotation.y=li;dummy.updateMatrix();lootMesh.setMatrixAt(li++,dummy.matrix)}lootMesh.count=li;lootMesh.instanceMatrix.needsUpdate=true;
  for(const npc of s.npcs||[]){if(Math.hypot(npc.x-s.position.x,npc.z-s.position.z)>240)continue;if(!npcModels.has(npc.id)){const model=buildSurvivor({equipment:{torso:npc.faction==='hostile'?'coat':'jacket',legs:'pants',vest:'vest',head:'helmet'},hands:'rifle'});const sign=label(npc.name,npc.faction==='hostile'?'#e69b82':'#b0d9ad');sign.position.y=2.2;model.root.add(sign);npcModels.set(npc.id,model);scene.add(model.root)}const model=npcModels.get(npc.id);model.root.position.set(npc.x,Math.max(groundHeight(npc.x,npc.z,heightAt),0),npc.z);model.root.rotation.y=npc.yaw;model.root.visible=npc.alive&&!s.underground;}
  for(const [id,model]of npcModels)if(!(s.npcs||[]).some(n=>n.id===id&&Math.hypot(n.x-s.position.x,n.z-s.position.z)<=240)){dispose(model);npcModels.delete(id)}
  const p=s.companion;if(p){const m=pet();m.root.visible=p.hp>0&&(p.underground||null)===(s.underground||null);m.root.position.set(p.x,s.underground?-28:Math.max(groundHeight(p.x,p.z,heightAt),0),p.z);m.root.rotation.y=Math.atan2(s.position.x-p.x,s.position.z-p.z)+Math.PI;for(const [i,leg]of m.legs.entries())leg.rotation.x=p.mode==='follow'&&Math.hypot(p.x-s.position.x,p.z-s.position.z)>3?Math.sin(now*9+i%2*Math.PI)*.3:0;}else if(petModel)petModel.root.visible=false;
  for(const e of s.worldEvents||[]){if(Math.hypot(e.x-s.position.x,e.z-s.position.z)>700)continue;if(!wrecks.has(e.id)){
    const type=e.type==='HelicopterCrash'?'helicopter':e.type==='ShipCrash'?'boat':'trainwreck',m=vehicleModel(type,true);

    const smoke=new THREE.Group();for(let i=0;i<6;i++){const puff=new THREE.Mesh(new THREE.SphereGeometry(2+i*.65,8,6),new THREE.MeshBasicMaterial({color:0x444744,transparent:true,opacity:.12,depthWrite:false}));puff.position.set(Math.sin(i)*1.5,5+i*3,Math.cos(i));smoke.add(puff)}m.root.add(smoke);scene.add(m.root);wrecks.set(e.id,m);
   }const model=wrecks.get(e.id);model.root.position.set(e.x,Math.max(0,heightAt(e.x,e.z)),e.z);model.root.rotation.y=e.yaw;model.root.visible=!s.underground;}
  for(const [id,m]of wrecks)if(!(s.worldEvents||[]).some(e=>e.id===id&&Math.hypot(e.x-s.position.x,e.z-s.position.z)<=700)){dispose(m);wrecks.delete(id)}
  const signature=JSON.stringify(s.equipment)+s.hands;if(!avatar||signature!==avatarSignature){dispose(avatar);avatar=buildSurvivor(s);avatarSignature=signature;scene.add(avatar.root)}
  avatar.root.position.set(s.position.x,s.underground?-28:Math.max(groundHeight(s.position.x,s.position.z,heightAt),0),s.position.z);avatar.root.rotation.y=yaw()+Math.PI;avatar.root.visible=!!s.thirdPerson&&!vehicle();
 }
 function applyCamera(pitch){
  const v=vehicle();if(v){const lookYaw=v.yaw+yaw()-enterYaw;
   if(s.vehicleView==='inside'){camera.position.set(v.x-Math.cos(v.yaw)*.35,v.y+VEHICLES[v.type].eye,v.z+Math.sin(v.yaw)*.35);camera.rotation.set(-pitch,lookYaw,0)}
   else{const distance=VEHICLES[v.type].length*.85+3;camera.position.set(v.x+Math.sin(lookYaw)*distance,v.y+3+Math.sin(pitch)*distance,v.z+Math.cos(lookYaw)*distance);camera.lookAt(v.x,v.y+1.2,v.z)}
  }else if(s.thirdPerson){const y=(s.underground?-28:Math.max(groundHeight(s.position.x,s.position.z,heightAt),0))+1.5;const look=yaw(),desired={x:s.position.x+Math.sin(look)*4,z:s.position.z+Math.cos(look)*4};
   const ray=new THREE.Raycaster(new THREE.Vector3(s.position.x,y,s.position.z),new THREE.Vector3(desired.x-s.position.x,0,desired.z-s.position.z).normalize(),0,4);
   const hits=ray.intersectObjects(scene.children,true).filter(hit=>hit.object.userData.cameraSolid);const distance=hits.length?Math.max(.5,hits[0].distance-.5):4;
   camera.position.set(s.position.x+Math.sin(look)*distance,y+.7+Math.sin(pitch)*2,s.position.z+Math.cos(look)*distance);camera.lookAt(s.position.x,y-Math.sin(pitch)*2,s.position.z);
  }
 }
 function show(which='admin'){
  cleanup();menu=which;panel.classList.add('world-tools');title.textContent=which==='admin'?'ADMINISTRATION SOLO':which==='bank'?'BANQUE · CRÉDITS DU JEU':'COMPAGNONS ET GROUPE';
  const result=r=>{const message=r?.message||'Mis à jour.';notice(message);if(menu==='admin'){s.adminLog??=[];s.adminLog.unshift(new Date().toISOString()+' '+message);s.adminLog=s.adminLog.slice(0,200)}syncInventory(s);save();show(menu)};
  if(which==='bank'){
   const near=!s.underground&&Math.hypot(s.position.x-52,s.position.z-180)<8;
   body.innerHTML=`<h3>Compte du survivant</h3><p>Espèces : <b>${s.cash||0}</b> crédits · Banque : <b>${s.bank||0}</b> crédits</p><p>${near?'Distributeur accessible.':'Approche du distributeur d’Hélion : X 52 / Z 180.'}</p><input id="bankAmount" type="number" min="1" value="100"><button data-bank="deposit" ${near?'':'disabled'}>Déposer</button><button data-bank="withdraw" ${near?'':'disabled'}>Retirer</button><h3>Historique</h3>${(s.bankHistory||[]).slice(0,10).map(t=>`<p>${t.kind==='deposit'?'Dépôt':'Retrait'} : ${t.amount}</p>`).join('')}`;
   body.onclick=e=>{const b=e.target.closest('[data-bank]');if(b&&near)result(bankTransaction(s,b.dataset.bank,body.querySelector('#bankAmount').value))};open();return;
  }
  if(which==='companions'){
   const p=s.companion;body.innerHTML=`<h3>Animal</h3>${p?`<p>${esc(p.name)} · Santé ${Math.round(p.hp)} · Nourriture ${Math.round(p.hunger)} · ${esc(p.mode)}</p><button data-pet="follow">Suivre</button><button data-pet="stay">Attendre</button><button data-pet="guard">Garder</button><button data-pet="feed">Nourrir</button><button data-pet="dismiss">Libérer</button>`:Object.entries(COMPANION_TYPES).map(([id,d])=>`<button data-adopt="${id}">Adopter ${d.name} · 3 rations</button>`).join('')}<h3>Survivants recrutés</h3>${(s.npcs||[]).filter(n=>n.recruited&&n.alive).map(n=>`<p>${esc(n.name)} · ${Math.round(n.hp)} PV <button data-order="${esc(n.id)}" data-mode="follow">Suivre</button><button data-order="${esc(n.id)}" data-mode="stay">Attendre</button></p>`).join('')||'<p>Parle avec E aux survivants alliés pour les recruter.</p>'}`;
   body.onclick=e=>{const b=e.target.closest('button');if(!b)return;if(b.dataset.adopt)return result(adoptCompanion(s,b.dataset.adopt));if(b.dataset.pet==='feed')return result(feedCompanion(s));if(b.dataset.pet==='dismiss'){s.companion=null;return result({message:'Compagnon libéré.'})}if(b.dataset.pet)return result(companionCommand(s,b.dataset.pet));if(b.dataset.order){const n=s.npcs.find(n=>n.id===b.dataset.order);if(n)n.mode=b.dataset.mode;result({message:'Ordre transmis.'})}};open();return;
  }
  body.innerHTML=`<nav class="admin-tabs">${['items','vehicles','creatures','player','xml'].map(id=>`<button data-admin-tab="${id}">${{items:'Objets',vehicles:'Véhicules',creatures:'Créatures / IA',player:'Joueur / positions',xml:'Fichiers / événements'}[id]}</button>`).join('')}</nav><p class="admin-coords">X ${s.position.x.toFixed(1)} · Z ${s.position.z.toFixed(1)} · ${s.vehicles.length} véhicules · ${(s.worldEvents||[]).length} événements</p>
   ${tab==='items'?`<label>Rechercher<input id="adminSearch" placeholder="Nom ou identifiant"></label><label>Quantité<input id="adminQuantity" type="number" value="1" min="1" max="100"></label><div class="admin-catalog">${Object.entries(ITEM_DEFS).map(([id,d])=>`<article data-catalog-id="${id}" data-name="${esc(d.label.toLowerCase())}"><b>${esc(d.label)}</b><small>${id}</small><button data-give="${id}">Donner</button></article>`).join('')}</div>`:''}
   ${tab==='vehicles'?`<p>Création devant toi sur un emplacement libre. Les bateaux nécessitent de l’eau.</p><div class="admin-catalog">${Object.entries(VEHICLES).map(([id,d])=>`<article><b>${d.name}</b><small>${id} · ${Math.round(d.speed*3.6)} km/h max</small><button data-vehicle="${id}">Créer</button></article>`).join('')}</div><h3>Véhicules présents</h3>${s.vehicles.map(v=>`<p>${VEHICLES[v.type].name} · X ${Math.round(v.x)} Z ${Math.round(v.z)} · carburant ${Math.round(v.fuel)} % <button data-goto-vehicle="${v.id}">Rejoindre</button><button data-repair="${v.id}">Réparer / plein</button><button data-delete-vehicle="${v.id}">Supprimer</button></p>`).join('')}`:''}
   ${tab==='creatures'?`<h3>Dinosaures</h3><label><input type="checkbox" id="spawnTamed" checked> Apprivoisé et sellé</label><div class="admin-catalog">${DINO_TYPES.map(d=>`<article><b>${esc(d.label||d.name)}</b><button data-dino="${d.id}">Créer</button></article>`).join('')}</div><h3>Compagnon</h3>${Object.entries(COMPANION_TYPES).map(([id,d])=>`<button data-admin-pet="${id}">${d.name}</button>`).join('')}<h3>Survivants IA</h3><button data-spawn-npc="friendly">Créer un allié recrutable</button><button data-spawn-npc="hostile">Créer un hostile</button>`:''}
   ${tab==='player'?`<h3>Survivant</h3><button data-admin-action="heal">Soigner</button><button data-admin-action="god">Invulnérabilité : ${s.godMode?'OUI':'NON'}</button><button data-admin-action="view">Changer de vue</button><button data-admin-action="credits">Ajouter 1 000 crédits du jeu</button><h3>Téléportation</h3><label>X<input id="teleportX" type="number" value="${Math.round(s.position.x)}" min="${-WORLD_HALF}" max="${WORLD_HALF}"></label><label>Z<input id="teleportZ" type="number" value="${Math.round(s.position.z)}" min="${-WORLD_HALF}" max="${WORLD_HALF}"></label><button data-admin-action="teleport">Se téléporter</button><button data-admin-action="bank">Rejoindre le distributeur</button><h3>Événements actifs</h3>${(s.worldEvents||[]).map(e=>`<p>${EVENT_TYPES[e.type]} · X ${Math.round(e.x)} Z ${Math.round(e.z)} <button data-event-goto="${e.id}">Rejoindre</button></p>`).join('')}`:''}
   ${tab==='xml'?`<h3>Configuration active</h3>${diskConfigPath?`<p>Dossier local : <code>${esc(diskConfigPath)}</code></p>`:''}<p>Modifie un fichier, puis applique les réglages. Sauvegarde locale uniquement : les serveurs distants ne sont pas modifiés. Certaines options expérimentales sont conservées mais pas encore raccordées au moteur.</p><input type="file" id="xmlImport" accept=".xml,.ini,.cfg,.json,text/xml" multiple><button data-admin-action="import-xml">Importer et appliquer</button><div class="admin-catalog">${Object.keys(docs).map(name=>`<article><b>${name}</b><button data-edit-config="${name}">Modifier</button><button data-export-xml="${name}">Télécharger</button></article>`).join('')}</div>${editingFile?`<section class="config-editor"><h3>Modifier ${esc(editingFile)}</h3><textarea id="configEditorText" spellcheck="false" rows="16" style="width:100%;min-height:260px;font-family:monospace;white-space:pre">${esc(docs[editingFile])}</textarea><button data-admin-action="save-config">Valider et appliquer</button><button data-admin-action="cancel-config">Annuler</button></section>`:''}<button data-export-log="adm">Exporter le journal .adm</button><button data-export-log="rpt">Exporter le diagnostic .rpt</button><h3>Événements configurés</h3>${config.events.map(e=>`<p>${esc(e.name)} : ${e.active?'actif':'désactivé'} · ${e.nominal} exemplaires · ${e.lifetime} s</p>`).join('')}`:''}`;
  body.oninput=e=>{if(e.target.id==='adminSearch'){const text=e.target.value.toLowerCase();for(const card of body.querySelectorAll('[data-catalog-id]'))card.hidden=!card.dataset.catalogId.includes(text)&&!card.dataset.name.includes(text)}};
  body.onclick=async e=>{
   const b=e.target.closest('button');if(!b)return;
   if(b.dataset.adminTab){tab=b.dataset.adminTab;show('admin');return}
   if(b.dataset.give){const id=b.dataset.give,n=Math.max(1,Math.min(100,Math.floor(Number(body.querySelector('#adminQuantity').value)||1)));s.inventory[id]=(s.inventory[id]||0)+n;return result({message:n+' '+ITEM_DEFS[id].label+' ajouté(s).'})}
   if(b.dataset.vehicle){const type=b.dataset.vehicle;let found=null;for(let radius=9;radius<=45&&!found;radius+=5)for(let a=0;a<Math.PI*2;a+=Math.PI/4){const x=s.position.x-Math.sin(yaw()+a)*radius,z=s.position.z-Math.cos(yaw()+a)*radius;if(VEHICLES[type].mode!=='water'&&heightAt(x,z)<0)continue;if(VEHICLES[type].mode==='water'&&heightAt(x,z)>2)continue;if(solids().some(b=>Math.abs(x-b.x)<b.width/2+6&&Math.abs(z-b.z)<b.depth/2+6))continue;found={x,z};break}return result(found?spawnVehicle(s,type,found.x,found.z,heightAt):{message:'Aucun emplacement adapté à proximité.'})}
   if(b.dataset.repair){const v=s.vehicles.find(v=>v.id===b.dataset.repair);if(v){v.fuel=100;v.hp=100}return result({message:'Véhicule réparé et ravitaillé.'})}
   if(b.dataset.gotoVehicle){const v=s.vehicles.find(v=>v.id===b.dataset.gotoVehicle);if(v){s.activeVehicle=null;s.position={x:v.x+5,z:v.z}}return result({message:'Téléportation effectuée.'})}
   if(b.dataset.deleteVehicle){s.vehicles=s.vehicles.filter(v=>v.id!==b.dataset.deleteVehicle);if(s.activeVehicle===b.dataset.deleteVehicle)s.activeVehicle=null;return result({message:'Véhicule supprimé.'})}
   if(b.dataset.adminPet)return result(adoptCompanion(s,b.dataset.adminPet,true));
   if(b.dataset.dino){const d={id:'admin-dino-'+Date.now(),type:b.dataset.dino,x:s.position.x-Math.sin(yaw())*8,z:s.position.z-Math.cos(yaw())*8,tamed:body.querySelector('#spawnTamed').checked};s.adminCreatures.push(d);spawnDino(d,true);return result({message:'Dinosaure créé.'})}
   if(b.dataset.spawnNpc){initializeNPCs(s,[{id:'admin-npc-'+Date.now(),name:b.dataset.spawnNpc==='friendly'?'Survivant':'Pillard',faction:b.dataset.spawnNpc,x:s.position.x+8,z:s.position.z+4,recruitCost:100}]);return result({message:'Survivant IA créé.'})}
   if(b.dataset.eventGoto){const event=s.worldEvents.find(x=>x.id===b.dataset.eventGoto);if(event){s.activeVehicle=null;s.position={x:event.x+12,z:event.z+10}}return result({message:'Téléportation près de l’événement.'})}
   if(b.dataset.exportLog){const text=b.dataset.exportLog==='adm'?(s.adminLog||[]).join('\n'):JSON.stringify({version:'0.4.0',position:s.position,vehicles:s.vehicles.length,npcs:s.npcs.length,events:s.worldEvents.length,inventoryWeight:weight(s),runtimeLogs:s.runtimeLogs||[]},null,2);const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([text],{type:'text/plain'}));a.download='ANOMALIA.'+b.dataset.exportLog;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);return}
   if(b.dataset.editConfig){if(Object.hasOwn(docs,b.dataset.editConfig)){editingFile=b.dataset.editConfig;show('admin')}return}
   if(b.dataset.exportXml){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([docs[b.dataset.exportXml]],{type:'application/xml'}));a.download=b.dataset.exportXml;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);return}
   const act=b.dataset.adminAction;
   if(act==='heal'){s.health=s.hunger=s.thirst=s.stamina=100;s.illness=null;s.infection=0;return result({message:'Survivant soigné.'})}
   if(act==='god'){s.godMode=!s.godMode;return result({message:'Invulnérabilité '+(s.godMode?'activée.':'désactivée.')})}
   if(act==='view')return result(togglePerspective(s));
   if(act==='credits'){s.cash=(s.cash||0)+1000;return result({message:'1 000 crédits du jeu ajoutés.'})}
   if(act==='bank'){s.activeVehicle=null;s.position={x:52,z:177};return result({message:'Téléportation à la banque.'})}
   if(act==='teleport'){const x=Number(body.querySelector('#teleportX').value),z=Number(body.querySelector('#teleportZ').value);if(!Number.isFinite(x)||!Number.isFinite(z)||Math.abs(x)>WORLD_HALF||Math.abs(z)>WORLD_HALF)return notice('Coordonnées invalides.');s.activeVehicle=null;s.position={x,z};return result({message:'Téléportation effectuée.'})}
   if(act==='import-xml'){try{const next={...docs};for(const file of body.querySelector('#xmlImport').files){if(!Object.hasOwn(DEFAULT_XML,file.name))throw Error('Fichier inconnu : '+file.name);next[file.name]=await file.text()}configure(next);result({message:'Configuration appliquée.'})}catch(error){notice(error.message)}}
  };open();
 }
 function cleanupMenu(){panel.classList.remove('world-tools');body.onclick=null;body.oninput=null;}
 return {update,drive,interact,applyCamera,show,cleanup:cleanupMenu,vehicle,toggleView:()=>{if(!s.activeVehicle&&s.thirdPersonAllowed===false)return notice('Troisième personne désactivée dans la configuration.');notice(togglePerspective(s).message);save()},isAirborne:()=>{const v=vehicle();return v&&v.y>groundHeight(v.x,v.z,heightAt)+5},hostiles:()=>s.npcs.filter(n=>n.alive&&n.faction==='hostile'),debug:()=>({vehicles:s.vehicles.length,npcs:s.npcs.length,companion:s.companion,activeVehicle:s.activeVehicle,vehicleView:s.vehicleView,recruited:s.npcs.filter(n=>n.recruited).length,cash:s.cash,bank:s.bank,thirdPerson:s.thirdPerson,events:s.worldEvents.length})};
}
