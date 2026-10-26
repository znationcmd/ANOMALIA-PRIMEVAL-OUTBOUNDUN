/** Partition triangles by a convex volume, interpolating original vertex data. */
export function splitPolygon(vertices, plane) {
 const inside=[],outside=[];
 for(let i=0;i<vertices.length;i++){
  const a=vertices[i],b=vertices[(i+1)%vertices.length],da=plane(a.POSITION),db=plane(b.POSITION);
  (da>=0?inside:outside).push(a);
  if((da>=0)!==(db>=0)){
   const t=da/(da-db),v={};
   for(const key of Object.keys(a))v[key]=a[key].map((x,j)=>x+(b[key][j]-x)*t);
   inside.push(v);outside.push(v);
  }
 }
 return {inside,outside};
}
export function partitionTriangle(vertices,planes){
 let inside=vertices;const outside=[];
 for(const plane of planes){
  if(inside.length<3)break;
  const split=splitPolygon(inside,plane);inside=split.inside;
  if(split.outside.length>=3)outside.push(split.outside);
 }
 return {inside:inside.length>=3?[inside]:[],outside};
}
export function area(vertices){
 const [a,b,c]=vertices.map(v=>v.POSITION),u=b.map((x,i)=>x-a[i]),v=c.map((x,i)=>x-a[i]);
 return Math.hypot(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])/2;
}
export function triangulate(polygons){
 const result=[];for(const p of polygons)for(let i=1;i<p.length-1;i++){
  const triangle=[p[0],p[i],p[i+1]];if(area(triangle)>1e-12)result.push(triangle);
 }return result;
}
export function boundaryEdges(triangles){
 const edges=new Map(),key=v=>v.POSITION.map(x=>Math.round(x*1e6)).join(',');
 for(const tri of triangles)for(let i=0;i<3;i++){
  const a=tri[i],b=tri[(i+1)%3],ka=key(a),kb=key(b);if(ka===kb)continue;
  const k=[ka,kb].sort().join('|'),entry=edges.get(k);
  if(entry)entry.count++;else edges.set(k,{count:1,a,b});
 }
 return [...edges.values()].filter(e=>e.count===1).map(e=>[e.a,e.b]);
}
export const driverDoorPlanes=[
 p=>p[2]-.72, p=>p[1]-.298, p=>.975-p[1], p=>.118-p[0],
 // Follow the original front shut-line around the wheel arch.
 p=>p[0]+1.29, p=>p[0]+1.25+(p[1]-.75)*(.25/.452),
];
