import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {mergeGeometries} from 'three/addons/utils/BufferGeometryUtils.js';
import {sedanData} from './sedan-asset.js';
let cached;
export function loadSedan(){return cached??=new Promise((resolve,reject)=>{const bytes=Uint8Array.from(atob(sedanData),c=>c.charCodeAt(0));new GLTFLoader().parse(bytes.buffer,'',g=>{
 const root=new THREE.Group(),batches=new Map(),pivots=new Map();g.scene.updateMatrixWorld(true);
 g.scene.traverse(o=>{if(!o.isMesh)return;let geometry=o.geometry.clone().applyMatrix4(o.matrixWorld);if(geometry.index){const indexed=geometry;geometry=geometry.toNonIndexed();indexed.dispose();}for(const key of Object.keys(geometry.attributes))if(!['position','normal'].includes(key))geometry.deleteAttribute(key);if(!geometry.attributes.normal)geometry.computeVertexNormals();
 let group='body';if(/tire|rim|spoke|hub|brake/i.test(o.name)){geometry.computeBoundingBox();const c=geometry.boundingBox.getCenter(new THREE.Vector3()),x=c.x<0?-.94:.94,z=c.z<0?-1.36:1.36;group=`wheel:${x}:${z}`;geometry.translate(-x,-.33,-z);if(!pivots.has(group)){const pivot=new THREE.Group();pivot.position.set(x,.33,z);pivot.userData.wheel=true;pivots.set(group,pivot);root.add(pivot);}}
 const key=group+':'+o.material.uuid;if(!batches.has(key))batches.set(key,{group,material:o.material,geometries:[]});batches.get(key).geometries.push(geometry);
 });
 for(const batch of batches.values()){const geometry=mergeGeometries(batch.geometries);for(const g of batch.geometries)g.dispose();if(!geometry)continue;const material=batch.material.clone();material.metalness=Math.min(material.metalness,.5);const mesh=new THREE.Mesh(geometry,material);(pivots.get(batch.group)||root).add(mesh);}
 const oldMaterials=new Set();g.scene.traverse(o=>{o.geometry?.dispose();if(o.material)oldMaterials.add(o.material)});for(const m of oldMaterials)m.dispose();resolve(root);
 },reject);});}
