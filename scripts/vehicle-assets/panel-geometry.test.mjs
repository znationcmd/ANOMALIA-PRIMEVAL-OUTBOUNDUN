import test from 'node:test';
import assert from 'node:assert/strict';
import {partitionTriangle,triangulate,area,boundaryEdges,driverDoorPlanes} from './panel-geometry.mjs';
const vertex=(x,y,z=1)=>({POSITION:[x,y,z],NORMAL:[0,0,1],TEXCOORD_0:[x,y]});
test('partial cut preserves area and interpolated UV coordinates',()=>{
 const original=[vertex(-2,0),vertex(2,0),vertex(0,2)];
 const p=partitionTriangle(original,[v=>v[0]+.5,v=>.5-v[0],v=>v[1]-.2]);
 const inside=triangulate(p.inside),outside=triangulate(p.outside);
 assert(inside.length>0&&outside.length>0);
 assert(Math.abs([...inside,...outside].reduce((n,t)=>n+area(t),0)-area(original))<1e-10);
 for(const tri of [...inside,...outside])for(const v of tri)assert.deepEqual(v.TEXCOORD_0,v.POSITION.slice(0,2));
});
test('shared triangulation diagonal is not extruded as an external door edge',()=>{
 const a=vertex(0,0),b=vertex(1,0),c=vertex(1,1),d=vertex(0,1);
 assert.equal(boundaryEdges([[a,b,c],[a,c,d]]).length,4);
});
test('driver door cut excludes opposite side, wheel arch, roof and rear door',()=>{
 const inside=p=>driverDoorPlanes.every(f=>f(p)>=0);
 assert(inside([-.5,.6,.9]));
 for(const p of [[-.5,.6,-.9],[-1.2,.4,.9],[-.5,1.3,.9],[.6,.6,.9]])assert(!inside(p));
});
test('deterministic oblique cuts preserve area for a family of boundary crossings',()=>{
 for(let i=1;i<60;i++){
  const t=[vertex(-1,i/80),vertex(.3,-.2),vertex(.8,1.3)];
  const p=partitionTriangle(t,[v=>v[0]+v[1]-.5,v=>.7-v[0]]);
  assert(Math.abs(triangulate([...p.inside,...p.outside]).reduce((n,a)=>n+area(a),0)-area(t))<1e-9);
 }
});
