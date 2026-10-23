import test from 'node:test';
import assert from 'node:assert/strict';
import {newProject,makeObject,addToProject,validateProject,History} from '../src/model.js';
test('scène légère : références de modèles liés sans énorme base64',()=>{
  const id='abcdef0123456789abcdef01';
  const item=makeObject('linked-glb',{x:2,y:0,z:12},{libraryId:id,filename:'BMW_E39.glb'});
  assert.equal(item.preset,'linked-glb');
  const scene=addToProject(newProject('Quartier ANOMALIA'),item);
  assert.equal(scene.objects.length,1);
  assert.equal(scene.objects[0].asset.libraryId,id);
  assert.ok(JSON.stringify(scene).length<1500);
  const parsed=validateProject(JSON.parse(JSON.stringify(scene)));
  assert.equal(parsed.objects[0].asset.filename,'BMW_E39.glb');
});
test('le modèle lié ne peut pas charger des chemins arbitraires',()=>{
  const p=newProject();
  const item=makeObject('linked-glb',{x:0,y:0,z:0},{libraryId:'../Documents/private.txt',filename:'private.glb'});
  p.objects.push(item);
  assert.throws(()=>validateProject(p),/Référence de bibliothèque ANOMALIA invalide/);
});
test('annuler et rétablir sont conservés avec des GLB liés',()=>{
  const h=new History(newProject());
  const item=makeObject('linked-glb',{x:0,y:0,z:0},{libraryId:'bbccdd112233445566778899',filename:'car.glb'});
  h.commit(addToProject(h.project,item));
  assert.equal(h.project.objects.length,1);
  assert.equal(h.undo().objects.length,0);
  assert.equal(h.redo().objects.length,1);
});
