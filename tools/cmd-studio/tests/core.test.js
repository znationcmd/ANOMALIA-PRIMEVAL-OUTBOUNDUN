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
  assert.equal(filenameSafe('../../ test.v1'),'______test_v1');
});
