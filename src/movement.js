// Shared geometry rules for the renderer and player controller (metres).
export const BRIDGES=[
 {x1:4350,z1:0,x2:5850,z2:0,width:22},
 {x1:-3400,z1:2733.3333333333335,x2:-6850,z2:3883.3333333333335,width:22}
];
export function movementVector(forward,strafe,yaw){
 const x=-Math.sin(yaw)*forward+Math.cos(yaw)*strafe;
 const z=-Math.cos(yaw)*forward-Math.sin(yaw)*strafe;
 const scale=Math.max(1,Math.hypot(x,z));
 return {x:x/scale,z:z/scale};
}
export function bridgeSurface(x,z,heightAt){
 for(const b of BRIDGES){
  const dx=b.x2-b.x1,dz=b.z2-b.z1,len2=dx*dx+dz*dz;
  const t=((x-b.x1)*dx+(z-b.z1)*dz)/len2;
  if(t<0||t>1)continue;
  if(Math.hypot(x-(b.x1+t*dx),z-(b.z1+t*dz))>b.width/2)continue;
  const a=Math.max(8,heightAt(b.x1,b.z1)),c=Math.max(8,heightAt(b.x2,b.z2));
  const deck=Math.max(a,c,8);
  return t<.15?a+(deck-a)*t/.15:t>.85?deck+(c-deck)*(t-.85)/.15:deck;
 }
 return null;
}
export function groundHeight(x,z,heightAt){return Math.max(heightAt(x,z),bridgeSurface(x,z,heightAt)??-Infinity)}
export function moveWithCollisions(position,dx,dz,solids,canStep=()=>true,radius=.65){
 let {x,z}=position;
 const blocked=(px,pz)=>solids.some(b=>{const a=b.yaw||0,dx=px-b.x,dz=pz-b.z,x=dx*Math.cos(a)-dz*Math.sin(a),z=dx*Math.sin(a)+dz*Math.cos(a);return Math.abs(x)<b.width/2+radius&&Math.abs(z)<b.depth/2+radius});
 const steps=Math.max(1,Math.ceil(Math.hypot(dx,dz)/.4));
 for(let i=0;i<steps;i++){
  const nx=x+dx/steps;if(!blocked(nx,z)&&canStep(x,z,nx,z))x=nx;
  const nz=z+dz/steps;if(!blocked(x,nz)&&canStep(x,z,x,nz))z=nz;
 }
 return {x,z};
}
