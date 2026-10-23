import test from 'node:test';
import assert from 'node:assert/strict';
import { newProject, makeObject, addToProject, updateTransform, removeFromProject, History, validateProject, makeCSV } from '../src/model.js';
test('projet neuf indépendant',()=>{
  const a=newProject('Maison privée');
  const b=newProject();
  const object=makeObject('house',{x:1,y:0,z:2});
  a.objects.push(object);
  assert.equal(b.objects.length,0);
  assert.equal(a.name,'Maison privée');
  assert.equal(validateProject(a).objects.length,1);
});
test('ajout, déplacement, duplication et suppression indépendants',()=>{
  let p=addToProject(newProject(),makeObject('car',{x:0,y:0,z:0}));
  p=updateTransform(p,p.objects[0].id,'position','x',30);
  assert.equal(p.objects[0].position.x,30);
  const copy=structuredClone(p.objects[0]);copy.id=crypto.randomUUID();
  p=addToProject(p,copy);
  assert.equal(p.objects.length,2);
  p=removeFromProject(p,copy.id);
  assert.equal(p.objects.length,1);
});
test('historique annuler et refaire',()=>{
  const h=new History();
  h.commit(addToProject(h.project,makeObject('tree')));
  assert.equal(h.project.objects.length,1);
  assert.equal(h.undo().objects.length,0);
  assert.equal(h.redo().objects.length,1);
  h.undo();
  h.commit(addToProject(h.project,makeObject('rock')));
  assert.equal(h.redo(),null);
});
test('refuse fichiers invalides et valeurs arbitraires',()=>{
  assert.throws(()=>validateProject({schema:'other',version:1,objects:[]}));
  const p=addToProject(newProject(),makeObject('boat'));
  p.objects[0].scale.x=-2;
  assert.throws(()=>validateProject(p));
  p.objects[0].scale.x=1;
  p.objects[0].id='other';
  p.objects.push(structuredClone(p.objects[0]));
  assert.throws(()=>validateProject(p));
});
test('CSV contient identifiants, positions et rotations',()=>{
  const p=addToProject(newProject(),makeObject('wall',{x:5,y:0,z:-2}));
  assert.match(makeCSV(p),/x_m,y_m,z_m/);
  assert.match(makeCSV(p),/"5","0","-2"/);
});
