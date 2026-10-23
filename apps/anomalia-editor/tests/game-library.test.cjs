'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const os=require('node:os');
const {GameLibrary,category,kindFor,isInside}=require('../desktop/game-library.cjs');
const makeFixture=t=>{
  const root=fs.mkdtempSync(path.join(os.tmpdir(),'anomalia-library-test-'));
  const game=path.join(root,'ANOMALIA');
  fs.mkdirSync(path.join(game,'Content','Vehicles'),{recursive:true});
  fs.mkdirSync(path.join(game,'Content','Cities'),{recursive:true});
  fs.mkdirSync(path.join(game,'Content','Maps'),{recursive:true});
  const library=new GameLibrary(path.join(root,'UserData'));
  t.after(()=>fs.rmSync(root,{force:true,recursive:true}));
  return {root,game,library};
};
test('catalogue auto des modeles reels et cartes Unreal, sans les confondre',async t=>{
  const {game,library}=makeFixture(t);
  const glb=path.join(game,'Content','Vehicles','BMW_E39.glb');
  fs.writeFileSync(glb,Buffer.concat([Buffer.from('glTF'),Buffer.alloc(64)]));
  fs.writeFileSync(path.join(game,'Content','Cities','HLM.uasset'),'asset');
  fs.writeFileSync(path.join(game,'Content','Maps','WorldPartition.umap'),'umap');
  fs.writeFileSync(path.join(game,'Content','Maps','quartier.anomalia.json'),JSON.stringify({
    schema:'anomalia-editor',version:1,name:'Quartier',objects:[]
  }));
  library.setFolder(game);
  const state=await library.scan();
  assert.equal(state.total,4);
  assert.equal(state.changed,true);
  const car=state.items.find(x=>x.name==='BMW_E39.glb');
  assert.equal(car.category,'Véhicules');assert.equal(car.canPlace,true);
  const unreal=state.items.find(x=>x.name==='WorldPartition.umap');
  assert.equal(unreal.canOpen,false);
  assert.equal(unreal.category,'Cartes et secteurs');
  await assert.rejects(()=>library.read(unreal.id),/convertie ou ouverte dans Unreal/);
  const buffer=await library.read(car.id);
  assert.equal(buffer.kind,'glb');assert.equal(Buffer.from(buffer.data,'base64').subarray(0,4).toString(),'glTF');
  const district=state.items.find(x=>x.name==='quartier.anomalia.json');
  assert.equal((await library.read(district.id)).kind,'map');
  assert.equal((await library.scan()).changed,false);
  fs.writeFileSync(path.join(game,'Content','Vehicles','motorcycle.glb'),Buffer.concat([Buffer.from('glTF'),Buffer.alloc(64)]));
  const updated=await library.scan();
  assert.equal(updated.total,5);assert.equal(updated.changed,true);
});
test('ne lit pas de fichiers en dehors du dossier autorisé, même via symlink',async t=>{
  const {game,root,library}=makeFixture(t);
  const outside=path.join(root,'private.glb');
  fs.writeFileSync(outside,Buffer.concat([Buffer.from('glTF'),Buffer.alloc(10)]));
  const alias=path.join(game,'Content','Vehicles','linked.glb');
  try{fs.symlinkSync(outside,alias);}catch{return;}
  library.setFolder(game);
  const state=await library.scan();
  assert.equal(state.total,0);
  await assert.rejects(()=>library.read('invalid-token'),/absent du catalogue/);
  assert.equal(isInside(game,outside),false);
});
test('ignore automatiquement le code et les dossiers volumineux du build UE5',async t=>{
  const {game,library}=makeFixture(t);
  fs.mkdirSync(path.join(game,'Intermediate','Build'),{recursive:true});
  fs.writeFileSync(path.join(game,'Intermediate','Build','temporary.glb'),'glTFfake');
  fs.writeFileSync(path.join(game,'Content','Cities','wall.obj'),'wavefront');
  fs.writeFileSync(path.join(game,'Content','Vehicles','empty.glb'),'');
  library.setFolder(game);
  const state=await library.scan();
  assert.equal(state.total,1);
  assert.equal(state.items[0].kind,'source-3d');
  assert.equal(state.items[0].canPlace,false);
});
test('classifie les vrais items plutot que de generer des modeles fictifs',()=>{
  assert.equal(kindFor('world.umap'),'unreal-map');
  assert.equal(kindFor('city.anomalia.json'),'map');
  assert.equal(category('Content/Roads/bridge.glb','glb'),'Routes et infrastructures');
  assert.equal(category('Content/Objects/medical_kit.glb','glb'),'Objets et équipements');
});
