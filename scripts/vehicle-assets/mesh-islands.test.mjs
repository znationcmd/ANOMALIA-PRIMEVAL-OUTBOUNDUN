import test from 'node:test';import assert from 'node:assert/strict';
import {triangleIslands} from './mesh-islands.mjs';
test('UV seam duplicates remain one physical panel island',()=>{
 const p=[0,0,0,1,0,0,0,1,0,1,0,0,1,1,0,0,1,0];
 assert.deepEqual(triangleIslands(p,[0,1,2,3,4,5]).map(g=>g.triangleOffsets),[[0,3]]);
});
test('overlapping bounds alone do not join disconnected door and cabin surfaces',()=>{
 const p=[0,0,0,2,0,0,0,2,0,.25,.25,.01,1,.25,.01,.25,1,.01];
 assert.equal(triangleIslands(p,[0,1,2,3,4,5]).length,2);
 assert.throws(()=>triangleIslands(p,[0,1,99]));
});
