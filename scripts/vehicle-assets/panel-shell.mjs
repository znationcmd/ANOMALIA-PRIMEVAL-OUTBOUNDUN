import {area,boundaryEdges} from './panel-geometry.mjs';
/** Add a real inward skin and closed edge strip; original exterior triangles stay intact. */
export function panelShell(triangles,thickness){
 if(!Number.isFinite(thickness)||thickness<=0)throw Error('Positive finite shell thickness required');
 const inner=v=>{const q=structuredClone(v),n=v.NORMAL,l=Math.hypot(...n);if(l<1e-10)throw Error('Panel shell requires normals');
  q.POSITION=v.POSITION.map((x,i)=>x-thickness*n[i]/l);q.NORMAL=n.map(x=>-x/l);
  if(q.TANGENT)q.TANGENT[3]*=-1;return q;};
 const skin=triangles.map(t=>[inner(t[0]),inner(t[2]),inner(t[1])]),rim=[];
 for(const [a,b] of boundaryEdges(triangles)){
  const ai=inner(a),bi=inner(b);
  for(const t of [[a,ai,b],[b,ai,bi]]){
   if(area(t)<1e-12)continue;
   const u=t[1].POSITION.map((x,i)=>x-t[0].POSITION[i]),v=t[2].POSITION.map((x,i)=>x-t[0].POSITION[i]);
   const n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]],l=Math.hypot(...n),tl=Math.hypot(...u);
   rim.push(t.map(p=>{const q=structuredClone(p);q.NORMAL=n.map(x=>x/l);if(q.TANGENT)q.TANGENT=[...u.map(x=>x/tl),1];return q;}));
  }
 }
 return {skin,rim};
}
