import test from 'node:test';
import assert from 'node:assert/strict';
import {RACCONIA_VARKOVIA as map} from '../src/racconia-varkovia.js';
test('RACCONIA-VARKOVIA keeps SKARVIK independent and 16 x 16 km',()=>{
 assert.equal(map.id,'racconia-varkovia');
 assert.equal(map.widthKm*map.heightKm,256);
 assert.equal(map.replaces,null);
 assert.equal(map.landFraction+map.seaFraction,1);
 assert.equal(map.plannedSites,29);
 assert.equal(Object.values(map.regions).flat().length,29);
 assert.equal(new Set(Object.values(map.regions).flat()).size,29);
 assert.equal(map.playable,false);
});
