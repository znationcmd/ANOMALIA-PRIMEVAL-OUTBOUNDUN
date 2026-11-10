import test from 'node:test';
import assert from 'node:assert/strict';
import {EDITOR_WORLD_CATALOG,editorCatalogSummary} from '../src/editor-world-catalog.js';

test('ANOMALIA Editor lists 20 original and 3 added worlds',()=>{
 assert.equal(EDITOR_WORLD_CATALOG.length,23);
 assert.equal(new Set(EDITOR_WORLD_CATALOG.map(x=>x.id)).size,23);
 assert.deepEqual(EDITOR_WORLD_CATALOG.slice(-3).map(x=>x.name),
  ['UNKNOWN HORROR X','KÖNIGSBRÜCK','SKJÆRØYÅS']);
 assert.equal(EDITOR_WORLD_CATALOG.find(x=>x.id==='koenigsbrueck').areaKm2,900);
 const nordic=EDITOR_WORLD_CATALOG.find(x=>x.id==='skjaeroyaas');
 assert.equal(nordic.areaKm2,225);
 assert.equal(nordic.widthKm,15);
 assert.equal(nordic.heightKm,15);
 assert.ok(EDITOR_WORLD_CATALOG.every(x=>x.playableLevelVerified===false));
});
test('editor does not assert catalogue maps are loaded or modify existing scene',()=>{
 assert.match(editorCatalogSummary('skjaeroyaas'),/RAW16/);
 assert.match(editorCatalogSummary('skjaeroyaas'),/ne change PAS la scène/);
 assert.match(editorCatalogSummary('koenigsbrueck'),/30 × 30 km/);
 assert.match(editorCatalogSummary(''),/pas chargées/);
});
