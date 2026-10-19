import * as THREE from 'three';
export function survivorPreview(host,state){
 const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(34,1,.1,30),renderer=new THREE.WebGLRenderer({alpha:true,antialias:true});
 renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;
 host.append(renderer.domElement);scene.add(new THREE.HemisphereLight(0xc7e5ec,0x2b3029,2));const light=new THREE.DirectionalLight(0xffebd2,3);light.position.set(-3,4,4);scene.add(light);
 const root=new THREE.Group();scene.add(root);root.rotation.y=-.2;
 const fabric=new THREE.MeshStandardMaterial({color:state.equipment.torso==='coat'?0x5d5143:0x56634d,roughness:1});
 const pants=new THREE.MeshStandardMaterial({color:state.equipment.legs==='jeans'?0x3f4a54:0x5a6150,roughness:1});
 const skin=new THREE.MeshStandardMaterial({color:0x9d7860,roughness:.95});const dark=new THREE.MeshStandardMaterial({color:0x272c29,roughness:.8});const gear=new THREE.MeshStandardMaterial({color:0x6f7156,roughness:1});
 const part=(geo,x,y,z,mat)=>{const m=new THREE.Mesh(geo,mat);m.position.set(x,y,z);root.add(m);return m};
 const box=(x,y,z,w,h,d,mat)=>part(new THREE.BoxGeometry(w,h,d),x,y,z,mat);
 const limb=(x,y,z,r,length,mat)=>part(new THREE.CapsuleGeometry(r,length,6,12),x,y,z,mat);
 part(new THREE.SphereGeometry(.14,20,16),0,1.75,0,skin).scale.set(.83,1.15,.9);
 limb(0,1.40,0,.22,.30,fabric).scale.set(1,.9,.65);limb(0,1.16,0,.16,.12,pants).scale.set(1.2,1,.8);
 for(const sign of [-1,1]){
  limb(sign*.12,.87,0,.095,.32,pants);limb(sign*.12,.43,0,.078,.32,pants);
  box(sign*.12,.12,.055,.18,.19,.30,dark);
  const upper=limb(sign*.28,1.40,0,.075,.22,fabric);upper.rotation.z=sign*.13;
  const arm=limb(sign*.31,1.13,.04,.059,.23,fabric);arm.rotation.x=-.13;
  limb(sign*.31,.93,.08,.055,.06,skin);
  box(sign*.12,1.06,0,.20,.045,.23,dark);
 }
 if(state.equipment.vest){box(0,1.42,.15,.40,.40,.12,gear);for(const x of [-.13,0,.13])box(x,1.32,.23,.10,.17,.07,gear)}
 if(state.equipment.back){box(0,1.37,-.20,.39,.43,.22,gear);for(const x of [-.17,.17])box(x,1.49,.14,.045,.33,.04,gear)}
 if(state.equipment.head){const helmet=part(new THREE.SphereGeometry(.151,20,14,0,Math.PI*2,0,Math.PI*.58),0,1.82,0,gear);helmet.scale.z=.95;}
 if(state.hands==='pistol'||state.hands==='rifle'){const gun=box(.31,1.02,.23,.06,.09,state.hands==='rifle'?.60:.22,dark);gun.rotation.x=.3;box(.31,.96,.17,.045,.14,.07,dark)}
 camera.position.set(0,1.18,3.8);camera.lookAt(0,1.05,0);
 let dragging=false,last=0;const down=e=>{dragging=true;last=e.clientX;host.setPointerCapture?.(e.pointerId)},move=e=>{if(dragging){root.rotation.y+=(e.clientX-last)*.012;last=e.clientX}},up=()=>dragging=false;
 host.addEventListener('pointerdown',down);host.addEventListener('pointermove',move);host.addEventListener('pointerup',up);
 const size=()=>{const w=host.clientWidth||280,h=host.clientHeight||440;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix()};const observer=new ResizeObserver(size);observer.observe(host);size();
 let frame;function render(){frame=requestAnimationFrame(render);renderer.render(scene,camera)}render();
 return ()=>{cancelAnimationFrame(frame);observer.disconnect();host.removeEventListener('pointerdown',down);host.removeEventListener('pointermove',move);host.removeEventListener('pointerup',up);scene.traverse(o=>o.geometry?.dispose());for(const m of [fabric,pants,skin,dark,gear])m.dispose();renderer.forceContextLoss();renderer.dispose();renderer.domElement.remove()};
}
