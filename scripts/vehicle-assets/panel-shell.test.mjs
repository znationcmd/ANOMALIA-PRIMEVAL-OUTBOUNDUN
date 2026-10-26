import test from 'node:test';import assert from 'node:assert/strict';
import {panelShell} from './panel-shell.mjs';import {area,boundaryEdges} from './panel-geometry.mjs';
test('One-sided panel acquires inward skin and four closed rims without a diagonal seam',()=>{
 const v=(x,y)=>({POSITION:[x,y,0],NORMAL:[0,0,1],TANGENT:[1,0,0,1],TEXCOORD_0:[x,y]});
 const a=v(0,0),b=v(1,0),c=v(1,1),d=v(0,1),outside=[[a,b,c],[a,c,d]],snapshot=structuredClone(outside);
 const {skin,rim}=panelShell(outside,.02);
 assert.deepEqual(outside,snapshot);assert.equal(skin.length,2);assert.equal(rim.length,8);
 assert.equal(boundaryEdges([...outside,...skin,...rim]).length,0);
 assert.equal(skin.reduce((n,t)=>n+area(t),0),1);
 for(const t of skin)for(const p of t){assert.equal(p.POSITION[2],-.02);assert.equal(p.NORMAL[2],-1);assert.equal(p.TANGENT[3],-1);}
});
test('Reject invalid physical thickness',()=>{for(const t of [0,-1,NaN,Infinity])assert.throws(()=>panelShell([],t));});
