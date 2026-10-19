import * as THREE from 'three';
import concrete from './textures/concrete_wall_001.js';
import grass from './textures/aerial_grass_rock.js';
import asphalt from './textures/asphalt_02.js';
import rock from './textures/rocky_terrain_02.js';
import sand from './textures/sand_01.js';

const shared=material=>{material.userData.shared=true;return material};
export function createGraphics(renderer,scene,camera,sun,hemi,cities){
 const low=matchMedia('(pointer:coarse)').matches;
 const loader=new THREE.TextureLoader(),images=[];
 const texture=(uri)=>{const t=loader.load(uri);t.wrapS=t.wrapT=THREE.RepeatWrapping;t.colorSpace=THREE.SRGBColorSpace;t.anisotropy=Math.min(8,renderer.capabilities.getMaxAnisotropy());images.push(t);return t};
 const concreteMap=texture(concrete),grassMap=texture(grass),roadMap=texture(asphalt),rockMap=texture(rock),sandMap=texture(sand);
 // Diffuse scans provide small relief while explicit geometry provides silhouettes.
 const pbr=(map,color=0xffffff,repeat=1)=>{const tex=map.clone();tex.repeat.set(repeat,repeat);const bump=tex.clone();bump.colorSpace=THREE.NoColorSpace;return shared(new THREE.MeshStandardMaterial({map:tex,bumpMap:bump,bumpScale:.09,color,roughness:.93}))};
 const concreteMaterial=pbr(concreteMap,0xb3aaa0,3),roadMaterial=pbr(roadMap,0xb6b3ac,5),rockMaterial=pbr(rockMap,0xb8b4aa,3);
 const frame=shared(new THREE.MeshStandardMaterial({color:0x716d60,roughness:.85}));
 const glass=shared(new THREE.MeshStandardMaterial({color:0x263c42,roughness:.28,metalness:.45}));
 const dark=shared(new THREE.MeshStandardMaterial({color:0x252a28,roughness:.9}));
 const wood=shared(new THREE.MeshStandardMaterial({map:concreteMap,color:0x544335,roughness:1}));
 const bark=pbr(concreteMap,0x4e4233,4);
 const leaves=shared(new THREE.MeshStandardMaterial({color:0x466036,roughness:1,flatShading:false}));
 const facadeMaps=[];
 for(let style=0;style<4;style++){
  const c=document.createElement('canvas');c.width=c.height=512;const ctx=c.getContext('2d');
  const palette=['#9b9787','#7e8981','#b2a28c','#8a7e70'];ctx.fillStyle=palette[style];ctx.fillRect(0,0,512,512);
  let seed=style+9127;const rnd=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296};
  for(let n=0;n<18000;n++){const v=rnd()>.5?255:0;ctx.fillStyle=`rgba(${v},${v},${v},${rnd()*.065})`;ctx.fillRect(rnd()*512,rnd()*512,1+rnd()*4,1+rnd()*3)}
  for(let row=0;row<4;row++)for(let col=0;col<4;col++){
   const x=col*128+37,y=row*128+29;
   ctx.fillStyle='#5d5d50';ctx.fillRect(x-5,y-5,64,82);
   const gradient=ctx.createLinearGradient(x,y,x+55,y+70);gradient.addColorStop(0,'#52666a');gradient.addColorStop(.5,'#283333');gradient.addColorStop(1,'#151c1c');
   ctx.fillStyle=gradient;ctx.fillRect(x,y,54,69);
   if(rnd()>.7){ctx.fillStyle='#111715';ctx.fillRect(x,y,54,69);ctx.strokeStyle='#80908a';ctx.beginPath();ctx.moveTo(x+10,y);ctx.lineTo(x+32,y+34);ctx.lineTo(x+22,y+69);ctx.stroke()}
   ctx.fillStyle='#78796d';ctx.fillRect(x+25,y,3,69);ctx.fillRect(x,y+34,54,3);
   ctx.fillStyle='#c0bba7';ctx.fillRect(x-7,y+71,68,5);ctx.fillStyle='#575b4d';ctx.fillRect(x-5,y+77,66,3);
   ctx.fillStyle='rgba(27,39,25,.13)';ctx.fillRect(x-7,y+81,68,15+rnd()*16);
  }
  const tex=new THREE.CanvasTexture(c);tex.colorSpace=THREE.SRGBColorSpace;tex.wrapS=tex.wrapT=THREE.RepeatWrapping;tex.anisotropy=4;
  const bump=tex.clone();bump.colorSpace=THREE.NoColorSpace;
  facadeMaps.push(shared(new THREE.MeshStandardMaterial({map:tex,bumpMap:bump,bumpScale:.08,roughness:.85})));
 }
 const terrain=new THREE.MeshStandardMaterial({roughness:1});
 terrain.userData.shared=true;
 terrain.onBeforeCompile=shader=>{
  Object.assign(shader.uniforms,{grassTex:{value:grassMap},rockTex:{value:rockMap},sandTex:{value:sandMap},roadTex:{value:roadMap},citySites:{value:cities.map(c=>new THREE.Vector3(c.x,c.z,c.radius))}});
  shader.vertexShader='varying vec3 terrainWorld; varying vec3 terrainNormal;\n'+shader.vertexShader;
  shader.vertexShader=shader.vertexShader.replace('#include <worldpos_vertex>','#include <worldpos_vertex>\nterrainWorld=(modelMatrix*vec4(transformed,1.0)).xyz;terrainNormal=normalize(mat3(modelMatrix)*objectNormal);');
  shader.fragmentShader=`varying vec3 terrainWorld;varying vec3 terrainNormal;
   uniform sampler2D grassTex;uniform sampler2D rockTex;uniform sampler2D sandTex;uniform sampler2D roadTex;
   uniform vec3 citySites[${cities.length}];\n`+shader.fragmentShader;
  shader.fragmentShader=shader.fragmentShader.replace('#include <map_fragment>',`
   vec2 uv=terrainWorld.xz*.18;
   vec3 grassColor=texture2D(grassTex,uv).rgb;
   vec3 rockColor=texture2D(rockTex,uv*.45).rgb;
   vec3 sandColor=texture2D(sandTex,uv*.7).rgb;
   float slope=1.0-abs(normalize(terrainNormal).y);
   vec3 ground=mix(grassColor,rockColor,smoothstep(.12,.5,slope));
   ground=mix(sandColor,ground,smoothstep(1.0,8.0,terrainWorld.y));
   ground=mix(ground,vec3(.72,.76,.77),smoothstep(540.0,780.0,terrainWorld.y));
   float city=0.0;for(int i=0;i<${cities.length};i++){city=max(city,1.0-smoothstep(citySites[i].z-20.0,citySites[i].z+15.0,distance(terrainWorld.xz,citySites[i].xy)));}
   vec2 grid=abs(mod(terrainWorld.xz-14.0,76.0)-38.0);
   float road=1.0-smoothstep(7.0,8.2,min(grid.x,grid.y));
   float sidewalk=(1.0-smoothstep(10.0,11.0,min(grid.x,grid.y)))-road;
   ground=mix(ground,texture2D(roadTex,terrainWorld.xz*.25).rgb*.65,road*city);
   ground=mix(ground,vec3(.31,.30,.27),sidewalk*city);
   float dash=step(.45,fract(terrainWorld.z/9.0));
   ground=mix(ground,vec3(.62,.57,.36),city*road*(1.0-smoothstep(.10,.22,grid.x))*dash*.65);
   diffuseColor.rgb*=ground;
  `);
 };
 terrain.customProgramCacheKey=()=>`ground-scans-${cities.length}`;
 renderer.shadowMap.enabled=!low;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
 renderer.toneMappingExposure=1.05;
 sun.color.set(0xffe3b0);sun.intensity=3;hemi.color.set(0xa7c7de);hemi.groundColor.set(0x494d38);hemi.intensity=.95;
 sun.castShadow=!low;sun.shadow.mapSize.set(2048,2048);sun.shadow.camera.left=-95;sun.shadow.camera.right=95;sun.shadow.camera.top=95;sun.shadow.camera.bottom=-95;sun.shadow.camera.near=1;sun.shadow.camera.far=450;sun.shadow.bias=-.0003;sun.shadow.normalBias=.15;
 scene.add(sun.target);scene.fog.color.set(0xa7b1ae);scene.fog.density=.00085;
 const sky=new THREE.Mesh(new THREE.SphereGeometry(1500,32,16),new THREE.ShaderMaterial({side:THREE.BackSide,depthWrite:false,uniforms:{sunDir:{value:new THREE.Vector3(-.55,.7,.3).normalize()}},vertexShader:'varying vec3 dir;void main(){dir=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}',fragmentShader:`varying vec3 dir;uniform vec3 sunDir;
 float noise(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
 float smoothNoise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.0-2.0*f);return mix(mix(noise(i),noise(i+vec2(1,0)),f.x),mix(noise(i+vec2(0,1)),noise(i+vec2(1,1)),f.x),f.y);}
 void main(){vec3 d=normalize(dir);float h=max(d.y,0.0);vec3 color=mix(vec3(.66,.72,.72),vec3(.19,.37,.54),pow(h,.45));float glow=pow(max(0.0,dot(d,sunDir)),64.0);color+=vec3(1.0,.67,.3)*glow*.4;
 vec2 p=d.xz/max(.12,d.y)*2.5;float n=smoothNoise(p)*.55+smoothNoise(p*2.1)*.28+smoothNoise(p*4.3)*.17;float cloud=smoothstep(.51,.7,n)*smoothstep(.02,.15,d.y);color=mix(color,vec3(.8,.82,.79),cloud*.75);gl_FragColor=vec4(color,1.0);}` }));
 sky.frustumCulled=false;scene.add(sky);
 const waterMaterial=shared(new THREE.ShaderMaterial({transparent:true,side:THREE.DoubleSide,uniforms:{time:{value:0},eye:{value:camera.position},fog:{value:scene.fog.color}},vertexShader:`varying vec3 wp;void main(){vec4 w=modelMatrix*vec4(position,1.0);wp=w.xyz;gl_Position=projectionMatrix*viewMatrix*w;}`,fragmentShader:`varying vec3 wp;uniform float time;uniform vec3 eye;uniform vec3 fog;
 void main(){vec2 p=wp.xz;float a=sin(p.x*.24+time*.8)*.12+sin(p.y*.32-time*.6)*.09;vec3 n=normalize(vec3(a,1.0,cos(p.x*.18+p.y*.14+time)*.15));vec3 view=normalize(eye-wp);float f=pow(1.0-max(0.0,dot(n,view)),3.0);vec3 color=mix(vec3(.025,.16,.16),vec3(.36,.50,.55),f);float spec=pow(max(0.0,dot(reflect(normalize(vec3(.55,-.7,-.3)),n),view)),96.0);color+=vec3(1.0,.85,.57)*spec*.8;float mist=1.0-exp(-.00085*.00085*distance(eye,wp)*distance(eye,wp));gl_FragColor=vec4(mix(color,fog,mist),.95);}` }));
 const unitBox=new THREE.BoxGeometry(1,1,1);
 function block(parent,x,y,z,w,h,d,material){const o=new THREE.Mesh(unitBox.clone(),material);o.scale.set(w,h,d);o.position.set(x,y,z);o.castShadow=!low;o.receiveShadow=true;parent.add(o);return o}
 function building(parent,x,y,z,w,h,d,style,detailed=true){
  const geo=new THREE.BoxGeometry(w,h,d),uv=geo.attributes.uv;
  for(let face=0;face<6;face++)for(let i=0;i<4;i++){const index=face*4+i;uv.setXY(index,uv.getX(index)*(face<2?d:w)/16,uv.getY(index)*(face<4?h:d)/16)}
  const body=new THREE.Mesh(geo,facadeMaps[style%4]);body.position.set(x,y+h/2,z);body.castShadow=!low;body.receiveShadow=true;body.userData.cameraSolid=true;parent.add(body);
  block(parent,x,y+h+.35,z,w+1,.7,d+1,concreteMaterial);
  if(!detailed)return body;
  block(parent,x,y+.6,z,w+.3,1.2,d+.3,concreteMaterial);
  block(parent,x,y+h+.35,z,w+1,.7,d+1,concreteMaterial);
  block(parent,x-w/2+.3,y+h+1,z,.6,1.2,d,concreteMaterial);block(parent,x+w/2-.3,y+h+1,z,.6,1.2,d,concreteMaterial);
  block(parent,x,y+h+1,z-d/2+.3,w,1.2,.6,concreteMaterial);block(parent,x,y+h+1,z+d/2-.3,w,1.2,.6,concreteMaterial);
  block(parent,x+w*.22,y+h+1.5,z,4,2.3,3,dark);
  block(parent,x,y+1.6,z+d/2+.16,2.2,3.2,.32,dark);block(parent,x,y+3.4,z+d/2+.65,3.3,.25,1.7,frame);
  block(parent,x,y+.15,z+d/2+.8,3,.3,1.8,concreteMaterial);
  if(h<30){const canopy=block(parent,x-w*.25,y+3.2,z+d/2+1.2,w*.38,.3,2.4,wood);canopy.rotation.x=.1;}
  return body;
 }
 function forest(parent,points){
  if(!points.length)return;
  const trunks=new THREE.InstancedMesh(new THREE.CylinderGeometry(.3,.7,1,7),bark,points.length);
  const crowns=new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1,2),leaves,points.length*9);
  const dummy=new THREE.Object3D(),color=new THREE.Color();let idx=0;
  points.forEach((p,i)=>{
   dummy.position.set(p.x,p.y+p.size*.38,p.z);dummy.rotation.set(0,i,Math.sin(i)*.05);dummy.scale.set(1,p.size*.78,1);dummy.updateMatrix();trunks.setMatrixAt(i,dummy.matrix);
   for(let n=0;n<9;n++){
    const angle=n*2.4+i,spread=n===0?0:p.size*.2;
    dummy.position.set(p.x+Math.sin(angle)*spread,p.y+p.size*(.65+(n%3)*.12),p.z+Math.cos(angle)*spread);
    dummy.scale.set(p.size*.24,p.size*(.21+(n%2)*.06),p.size*.23);dummy.rotation.set(n*.4,angle,0);dummy.updateMatrix();crowns.setMatrixAt(idx,dummy.matrix);
    color.setHSL(.23+(i%5)*.009,.25,.15+(n%3)*.025);crowns.setColorAt(idx++,color);
   }
  });
  trunks.castShadow=crowns.castShadow=!low;trunks.receiveShadow=crowns.receiveShadow=true;parent.add(trunks,crowns);
 }
 function groundCover(parent,points){
  if(!points.length)return;
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute([-.15,0,0,.15,0,0,.02,.8,.08,0,0,-.15,0,0,.15,.08,.65,.02],3));g.computeVertexNormals();
  const material=shared(new THREE.MeshStandardMaterial({color:0x66724b,side:THREE.DoubleSide,roughness:1}));
  const mesh=new THREE.InstancedMesh(g,material,points.length),dummy=new THREE.Object3D(),c=new THREE.Color();
  points.forEach((p,i)=>{dummy.position.set(p.x,p.y,p.z);dummy.rotation.y=i*2.4;dummy.scale.setScalar(.7+(i%7)*.18);dummy.updateMatrix();mesh.setMatrixAt(i,dummy.matrix);c.setHSL(.18+(i%5)*.015,.25,.19+(i%4)*.03);mesh.setColorAt(i,c)});mesh.receiveShadow=true;parent.add(mesh);
 }
 function car(parent,x,y,z,seed){
  const paint=shared(new THREE.MeshStandardMaterial({color:[0x454d47,0x6b5142,0x626966][seed%3],roughness:.83,metalness:.25}));
  block(parent,x,y+.65,z,1.9,.65,4.3,paint);block(parent,x,y+1.25,z-.15,1.65,.8,2.1,glass);block(parent,x,y+1.65,z-.15,1.8,.12,2.4,paint);
  for(const dx of [-1,1])for(const dz of [-1.35,1.35]){const wheel=new THREE.Mesh(new THREE.CylinderGeometry(.39,.39,.25,10),dark);wheel.rotation.z=Math.PI/2;wheel.position.set(x+dx,y+.4,z+dz);parent.add(wheel)}
 }
 return {terrain,concrete:concreteMaterial,road:roadMaterial,rock:rockMaterial,wood,glass,frame,dark,building,forest,groundCover,car,water:waterMaterial,
 update(time){waterMaterial.uniforms.time.value=time;sky.position.copy(camera.position);sun.position.set(camera.position.x-90,camera.position.y+135,camera.position.z+60);sun.target.position.set(camera.position.x,camera.position.y,camera.position.z);sun.target.updateMatrixWorld()}};
}
