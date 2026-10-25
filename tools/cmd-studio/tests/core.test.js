'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { Studio, fileCandidates, filenameSafe } = require('../core');
function sandbox(t) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'cmd-studio-test-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  return { dir, studio: new Studio(dir, path.join(__dirname, '..', 'scripts')) };
}
test('instanciation : configuration et bibliothèque vides', t => {
  const { studio } = sandbox(t);
  assert.deepEqual(studio.status(), { blender:false, unreal:false, project:false, assets:0, projects:0 });
  assert.ok(fs.existsSync(studio.libraryPath));
});
test('import local réel, hash et anti-doublons, persistance', async t => {
  const { dir, studio } = sandbox(t);
  const input = path.join(dir, 'house.glb');
  fs.writeFileSync(input, Buffer.from('glTF-example-data'));
  const [first] = await studio.import({ files: [input] });
  assert.equal(first.license,'À vérifier avant utilisation');
  assert.ok(fs.existsSync(first.path));
  assert.equal((await studio.import({ files:[input] }))[0].id,first.id);
  assert.equal(studio.assets().length,1);
  const reopened = new Studio(dir,studio.scriptsDir);
  assert.equal(reopened.assets().length,1);
});
test('refuse un exécutable absent et format non supporté', async t => {
  const { dir, studio } = sandbox(t);
  assert.throws(()=>studio.configure({ blenderPath:path.join(dir,'missing.exe') }),/introuvable/);
  const file=path.join(dir,'unsafe.exe');
  fs.writeFileSync(file,'anything');
  await assert.rejects(()=>studio.import({files:[file]}),/Format non pris en charge/);
});
test('ajoute un projet Unreal sans modifier son contenu', t => {
  const { dir, studio } = sandbox(t);
  const project=path.join(dir,'AnomaliaPrimeval.uproject');
  const content='{"FileVersion":3}';
  fs.writeFileSync(project,content);
  studio.addProject({file:project});
  assert.equal(studio.status().project,true);
  assert.equal(fs.readFileSync(project,'utf8'),content);
});
test('découverte de fichiers Poly Haven sans liens arbitraires', () => {
  const candidates=fileCandidates({blend:{'1k':{blend:{url:'https://cdn.polyhaven.com/x.blend',size:123}}}});
  assert.equal(candidates.length,1);
  assert.equal(candidates[0].extension,'.blend');
  assert.equal(filenameSafe('../../ test.v1'),'_______test_v1');
});

test('prévisualisation locale : vrai fichier GLB, sans accès aux autres dossiers', async t => {
  const {dir,studio}=sandbox(t);
  const glb=path.join(dir,'house.glb');
  fs.writeFileSync(glb,Buffer.from('glTF012345'));
  const asset=(await studio.import({files:[glb]}))[0];
  const preview=studio.previewAsset({id:asset.id});
  assert.equal(preview.format,'glb');
  assert.equal(Buffer.from(preview.data,'base64').toString('utf8'),'glTF012345');
  assert.throws(()=>studio.previewAsset({id:'other-user-asset'}),/Ressource absente/);
});
test('prévisualisation refusée pour formats non 3D visualisables', async t => {
  const {dir,studio}=sandbox(t);
  const other=path.join(dir,'shape.fbx');
  fs.writeFileSync(other,'fake FBX');
  const asset=(await studio.import({files:[other]}))[0];
  assert.throws(()=>studio.previewAsset({id:asset.id}),/uniquement pour GLB/);
});

test('ANOMALIA apparaît par défaut sans inventer un fichier local existant', t => {
  const {dir}=sandbox(t);
  const fakeScripts=path.join(dir,'tools','cmd-studio','scripts');
  const localStudio=new Studio(dir,fakeScripts);
  const featured=localStudio.projects().featured;
  assert.equal(featured.name,'ANOMALIA PRIMEVAL OUTBOUNDUN');
  assert.equal(featured.available,false);
  assert.equal(featured.linked,false);
  assert.equal(featured.status,'a-associer');
  assert.equal(localStudio.projects().items.length,0);
});

test('ANOMALIA lié à un véritable .uproject et sélection conservée sans toucher au projet', t => {
  const {dir}=sandbox(t);
  const localStudio=new Studio(dir,path.join(dir,'scripts'));
  const unreal=path.join(dir,'AnomaliaPrimeval.uproject');
  const original='{"FileVersion":3,"Description":"Test UE5"}';
  fs.writeFileSync(unreal,original);
  localStudio.addProject({file:unreal});
  assert.equal(localStudio.projects().featured.linked,true);
  assert.equal(localStudio.projects().featured.available,true);
  assert.equal(localStudio.projects().featured.name,'ANOMALIA PRIMEVAL OUTBOUNDUN');
  assert.equal(localStudio.projects().items[0].name,'ANOMALIA PRIMEVAL OUTBOUNDUN');
  const other=path.join(dir,'AutreJeu.uproject');
  fs.writeFileSync(other,'{"FileVersion":3}');
  localStudio.addProject({file:other});
  assert.equal(localStudio.projects().active,other);
  localStudio.selectProject({file:unreal});
  assert.equal(localStudio.projects().active,unreal);
  assert.equal(fs.readFileSync(unreal,'utf8'),original);
  const reopened=new Studio(dir,path.join(dir,'scripts'));
  assert.equal(reopened.projects().active,unreal);
  assert.equal(reopened.projects().featured.linked,true);
  assert.throws(()=>localStudio.selectProject({file:path.join(dir,'missing.uproject')}),/non enregistré/);
});

test('CMD Studio montre ANOMALIA sur son accueil, dans le menu et les projets', () => {
  const html=fs.readFileSync(path.join(__dirname,'..','ui','index.html'),'utf8');
  const ui=fs.readFileSync(path.join(__dirname,'..','ui','ui.js'),'utf8');
  const main=fs.readFileSync(path.join(__dirname,'..','main.js'),'utf8');
  assert.match(html,/id="navAnomalia"/);
  assert.match(html,/id="anomaliaDashboard"/);
  assert.match(html,/generated\/anomalia-logo\.jpg/);
  assert.match(ui,/function renderProjects\(data\)/);
  assert.match(ui,/chooseAnomaliaProject/);
  assert.match(ui,/openAnomalia/);
  assert.match(main,/'selectProject'/);
  assert.doesNotMatch(html,/onerror=/);
});
