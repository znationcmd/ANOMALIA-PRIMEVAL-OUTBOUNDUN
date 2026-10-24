import test from 'node:test';
import assert from 'node:assert/strict';
import {buildMapCatalog,filterMapCatalog} from '../src/map-catalog.js';
test('affiche uniquement les cartes réellement fournies',()=>{
 const maps=buildMapCatalog([{id:'abc',name:'Ma ville',objects:4}],{linked:true,maps:['World/Capital.umap','../outside.umap','Wrong.exe']});
 assert.equal(maps.length,2);
 assert.deepEqual(maps.map(x=>x.type),['local','ue5']);
 assert.equal(maps[1].key,'World/Capital.umap');
});
test('ne fabrique pas de cartes si Unreal est déconnecté',()=>{
 assert.deepEqual(buildMapCatalog([],{linked:false,maps:['Test.umap']}),[]);
});
test('cherche et filtre sans perdre les chemins UE5',()=>{
 const maps=buildMapCatalog([{id:'x',name:'Littoral',objects:2}],{linked:true,maps:['Maps/Foret.umap']});
 assert.equal(filterMapCatalog(maps,'ue5','forêt').length,0);
 assert.equal(filterMapCatalog(maps,'ue5','foret').length,1);
 assert.equal(filterMapCatalog(maps,'local','litt').length,1);
});
