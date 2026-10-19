import test from 'node:test';
import assert from 'node:assert/strict';
import {RP_SITES,BUILDING_TYPES,reserveBuilding,validatePlacements,localPoint,transformPoint} from '../src/building-rules.js';
import {moveWithCollisions} from '../src/movement.js';
test('RP sites reserve footprints and rotated editor placements round-trip coordinates',()=>{for(const o of RP_SITES){assert.ok(BUILDING_TYPES[o.type]);assert.ok(reserveBuilding(o.x,o.z));}const o={x:30,z:50,yaw:1.2};const p=transformPoint(o,3,7),l=localPoint(o,p.x,p.z);assert.ok(Math.abs(l.x-3)<1e-8&&Math.abs(l.z-7)<1e-8);});
test('import rejects unknown models, nonfinite positions, duplicates and overwriting protected sites',()=>{const o={id:'custom',type:'hospital',x:50,z:50,yaw:1};assert.equal(validatePlacements({schemaVersion:1,objects:[o]})[0].type,'hospital');for(const objects of [[{...o,type:'nope'}],[{...o,x:Infinity}],[o,o],[{...o,id:RP_SITES[0].id}]])assert.throws(()=>validatePlacements({schemaVersion:1,objects}));});
test('rotated walls block passage across their full length',()=>{const p=moveWithCollisions({x:0,z:0},10,0,[{x:5,z:0,width:10,depth:.5,yaw:Math.PI/2}]);assert.ok(p.x<4.2);});
