'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const os=require('node:os');
const crypto=require('node:crypto');
const yazl=require('yazl');
const {importArchive,safeEntry}=require('../desktop/pack-import.cjs');
const {GameLibrary}=require('../desktop/game-library.cjs');
function fixture(t){
 const folder=fs.mkdtempSync(path.join(os.tmpdir(),'anomalia-pack-tests-'));
 t.after(()=>fs.rmSync(folder,{force:true,recursive:true}));
 return folder;
}
function zipFile(output,files){
 return new Promise((resolve,reject)=>{
  const zip=new yazl.ZipFile();
  for(const [name,bytes] of Object.entries(files))zip.addBuffer(Buffer.from(bytes),name);
  zip.outputStream.pipe(fs.createWriteStream(output)).on('finish',resolve).on('error',reject);
  zip.end();
 });
}
test('import réel d un ZIP dans la bibliothèque privée sans supprimer la source',async t=>{
 const root=fixture(t),zip=path.join(root,'ANOMALIA_ASSETS_3D_PBR.zip');
 await zipFile(zip,{'RealismValidation_v2/BMW_E39.glb':Buffer.concat([Buffer.from('glTF'),Buffer.alloc(900)]),
   'RealismValidation_v2/CREDITS.md':'Crédits et licences', 'RealismValidation_v2/manifest.json':'{"schemaVersion":1}'});
 const original=fs.statSync(zip).size;
 const imported=await importArchive(zip,path.join(root,'userdata'));
 assert.equal(imported.files,3);
 assert.equal(imported.duplicate,false);
 assert.equal(fs.statSync(zip).size,original);
 const library=new GameLibrary(path.join(root,'userdata'));
 const result=await library.scan();
 assert.equal(result.total,1);
 assert.equal(result.packCount,1);
 assert.equal(result.items[0].name,'BMW_E39.glb');
 assert.equal(result.items[0].canPlace,true);
 assert.equal((await library.read(result.items[0].id)).kind,'glb');
 const again=await importArchive(zip,path.join(root,'userdata'));
 assert.equal(again.duplicate,true);
 assert.equal(again.folder,imported.folder);
});
test('protection ZIP contre traversal, fichiers cachés, chemins absolus',()=>{
 for(const name of ['../secret.glb','a/../../secret.glb','C:/secret.glb','/secret.glb','a\\..\\evil.glb','a//b.glb']){
   assert.throws(()=>safeEntry(name));
 }
 assert.deepEqual(safeEntry('RealismValidation_v2/box_truck.glb'),['RealismValidation_v2','box_truck.glb']);
});
test('pack et dossier Unreal sont fusionnés dans le catalogue sans modifier les originaux',async t=>{
 const root=fixture(t),archive=path.join(root,'batch.zip'),game=path.join(root,'game');
 fs.mkdirSync(game);
 fs.writeFileSync(path.join(game,'WorldPartition.umap'),'UE5');
 await zipFile(archive,{'RealismValidation_v2/house.glb':Buffer.concat([Buffer.from('glTF'),Buffer.alloc(300)])});
 const library=new GameLibrary(path.join(root,'user'));
 library.setFolder(game);
 const result=await library.importPack(archive);
 assert.equal(result.library.total,2);
 assert.ok(result.library.items.find(x=>x.rootTag==='pack'));
 assert.ok(result.library.items.find(x=>x.kind==='unreal-map'));
});

test('empreintes SHA-256 de vrais packs GLB : 1 valide puis 1 falsifié',async t=>{
 const root=fixture(t),pack=path.join(root,'verified.zip'),bad=path.join(root,'tampered.zip');
 const glb=Buffer.concat([Buffer.from('glTF'),Buffer.alloc(250)]);
 const record={schemaVersion:1,models:[{file:'vehicle.glb',bytes:glb.length,sha256:crypto.createHash('sha256').update(glb).digest('hex')}]};
 await zipFile(pack,{'models/vehicle.glb':glb,'models/manifest.json':JSON.stringify(record)});
 const result=await importArchive(pack,path.join(root,'valid'));
 assert.equal(result.verified,1);
 const changed=Buffer.from(glb);changed[5]=42;
 await zipFile(bad,{'models/vehicle.glb':changed,'models/manifest.json':JSON.stringify(record)});
 await assert.rejects(()=>importArchive(bad,path.join(root,'invalid')),/SHA-256 non conforme/);
 const dest=path.join(root,'invalid','imported-ANOMALIA-packs');
 if(fs.existsSync(dest))assert.ok(fs.readdirSync(dest).every(n=>!n.includes('tampered')));
});
