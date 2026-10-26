/** Same E39, same validated driver leaf/wheels; derive the remaining five real panels. */
import {NodeIO} from '@gltf-transform/core';import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {getBounds,prune,transformMesh} from '@gltf-transform/functions';
import {readFile,writeFile,mkdir} from 'node:fs/promises';import {createHash} from 'node:crypto';
import path from 'node:path';import {fileURLToPath} from 'node:url';
import {panelShell} from './panel-shell.mjs';
import {triangleIslands} from './mesh-islands.mjs';import {partitionTriangle,triangulate,area,gltfToUnreal} from './panel-geometry.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..'),base=path.join(root,'unreal/SourceAssets/BMWE39Review_v2'),out=path.join(root,'unreal/SourceAssets/BMWE39Review_v5');
const previous=JSON.parse(await readFile(path.join(base,'manifest.json'),'utf8')),parent=previous.models.find(m=>m.id==='body');
const hash=b=>createHash('sha256').update(b).digest('hex'),bytes=await readFile(path.join(base,parent.file));
if(previous.source.sha256!=='984a9daab49b5a31c45bbc284c657fa5898a010f2201c003358cb6b6f411751d'||hash(bytes)!==parent.sha256)throw Error('Same reviewed E39 with validated driver leaf required');
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS);await mkdir(out,{recursive:true});
async function preserve(n,b){try{if(!Buffer.from(b).equals(await readFile(path.join(out,n))))throw Error('Existing prepared E39 preserved: '+n);}catch(e){if(e.code!=='ENOENT')throw e;await writeFile(path.join(out,n),b);}}
const defs=[
 {id:'door_front_right',pivot:[.924,.90,.80],axis:[0,0,1],angle:-70,side:1,front:true,aperture:[20,80,110],normal:[0,1,0],stand:[210,230,100]},
 {id:'door_rear_left',pivot:[-.172,.90,-.80],axis:[0,0,1],angle:70,side:-1,front:false,aperture:[-85,-80,110],normal:[0,-1,0],stand:[-70,-230,100]},
 {id:'door_rear_right',pivot:[-.172,.90,.80],axis:[0,0,1],angle:-70,side:1,front:false,aperture:[-85,80,110],normal:[0,1,0],stand:[-70,230,100]},
 {id:'hood',pivot:[.927,.978,0],axis:[0,1,0],angle:-65,aperture:[210,0,85],normal:[1,0,1],stand:[350,0,100]},
 {id:'trunk',pivot:[-1.736,1.063,0],axis:[0,1,0],angle:65,aperture:[-228,0,80],normal:[-1,0,0],stand:[-380,0,100]}
];
function hull(points){
 const unique=[...new Map(points.map(p=>[p.join(','),p])).values()].sort((a,b)=>a[0]-b[0]||a[1]-b[1]);
 const cross=(a,b,c)=>(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);
 const half=p=>{const h=[];for(const q of p){while(h.length>1&&cross(h.at(-2),h.at(-1),q)<=0)h.pop();h.push(q);}return h;};
 const a=half(unique),b=half([...unique].reverse());return [...a.slice(0,-1),...b.slice(0,-1)];
}
const template=await io.readBinary(bytes);
for(const def of defs.filter(x=>x.side)){
 const points=[];
 for(const p of template.getRoot().listMeshes()[0].listPrimitives()){
  if(p.getMaterial()?.getName()!=='window')continue;const pos=p.getAttribute('POSITION'),ids=p.getIndices()?.getArray()??Uint32Array.from({length:pos.getCount()},(_,i)=>i);
  for(const g of triangleIslands(pos.getArray(),ids)){
   const side=def.side<0?g.max[2]<-.55:g.min[2]>.55;
   if(!side||(def.front?!(g.min[0]>-.30&&g.max[0]<1):!(g.min[0]<-1&&g.max[0]<0)))continue;
   for(const i of g.triangleOffsets)for(let k=0;k<3;k++){const v=pos.getElement(ids[i+k],[]);points.push(v.slice(0,2));}
  }
 }
 const poly=hull(points);if(poly.length<3)throw Error('Original door glazing required: '+def.id);
 def.framePlanes=poly.map((a,i)=>{const b=poly[(i+1)%poly.length],dx=b[0]-a[0],dy=b[1]-a[1];return p=>dx*(p[1]-a[1])-dy*(p[0]-a[0])+.025*Math.hypot(dx,dy);});
 def.framePlanes.push(p=>def.side*p[2]-.55);
}
const hoodPlanes=[p=>p[0]-2.05,p=>2.35-p[0],p=>p[1]-.52,p=>1.02-p[1],p=>p[2]+.33,p=>.33-p[2]];
const trunkPlanes=[p=>p[0]+2.34,p=>-1.72-p[0],p=>p[1]-.62,p=>1.065-p[1],p=>p[2]+.615,p=>.615-p[2]];
const hoodTrim=new Set(['black','chrome','matte_colors','matte_colors.001','matte_colors.002','frame','plastic','reflector']);
const trunkTrim=new Set(['detail_glass_clear','detail_glass_red','lights_glass','plastic2','reflector','reverse_light_lod0','mirrorRight','tail_light_lod0','frame']);
function wholePanel(g,name){
 for(const d of defs.filter(x=>x.side)){
  const side=d.side<0?g.max[2]<-.55:g.min[2]>.55,deep=d.side<0?g.max[2]<-.66:g.min[2]>.66;
  const longitudinal=d.front?g.min[0]>=-.285&&g.max[0]<=.95:g.min[0]>=-1.31&&g.max[0]<=-.16;
  if(side&&longitudinal&&g.min[1]>=.50&&g.max[1]<=1.39&&(deep||name==='window'))return d.id;
 }
 const width=Math.max(Math.abs(g.min[2]),Math.abs(g.max[2]));
 if(name==='body'&&g.min[0]>.90&&g.max[0]<2.33&&g.min[1]>.50&&g.max[1]<1.02&&width<.80)return 'hood';
 if(name==='emblem'&&g.min[0]>2.1&&g.min[1]>.65&&width<.1)return 'hood';
 if(g.min[0]>-2.34&&g.max[0]<-1.72&&g.min[1]>.62&&g.max[1]<1.065&&width<.65)return 'trunk';
 return null;
}
function rulesFor(g,name){
 const rules=[];
 const frame=name==='body'&&g.min[2]<-.8&&g.max[2]>.8&&g.max[1]>1.2;
 for(const d of defs.filter(x=>x.side)){
  const side=d.side<0?g.max[2]<-.55:g.min[2]>.55;
  if(frame||(side&&g.min[1]>.70))rules.push({id:d.id,planes:frame?[...d.framePlanes,p=>p[1]-.99]:d.framePlanes});
 }
 if(hoodTrim.has(name)&&g.min[0]>2.05&&g.max[0]<2.35)rules.push({id:'hood',planes:hoodPlanes});
 if((trunkTrim.has(name)&&g.max[0]<-2&&g.min[1]>.65&&g.max[1]<.95)||(name==='mottled'&&g.max[0]<-1.72&&g.min[1]>.62&&g.max[1]<1.065))rules.push({id:'trunk',planes:trunkPlanes});
 return rules;
}
let partition;const models=[];
for(const selection of ['body',...defs.map(d=>d.id)]){
 const doc=await io.readBinary(bytes),scene=doc.getRoot().getDefaultScene(),original=scene.listChildren()[0].getMesh(),mesh=doc.createMesh(selection),buffer=doc.getRoot().listBuffers()[0];
 const areas=Object.fromEntries(['body',...defs.map(d=>d.id)].map(x=>[x,0])),counts={...areas};let sourceArea=0;const shell={skinTriangles:0,rimTriangles:0,addedArea:0};
 function append(tris,material){if(!tris.length)return;const p=doc.createPrimitive().setMaterial(material);
  for(const semantic of Object.keys(tris[0][0])){const size=tris[0][0][semantic].length,data=[];
   for(const tri of tris)for(const vertex of tri){let a=[...vertex[semantic]];if(semantic==='NORMAL'||semantic==='TANGENT'){const length=Math.hypot(...a.slice(0,3));if(length<1e-10)throw Error('Invalid normal');for(let k=0;k<3;k++)a[k]/=length;}data.push(...a);}
   p.setAttribute(semantic,doc.createAccessor().setType(size===1?'SCALAR':'VEC'+size).setBuffer(buffer).setArray(new Float32Array(data)));
  }mesh.addPrimitive(p);
 }
 for(const p of original.listPrimitives()){
  const pos=p.getAttribute('POSITION'),indices=p.getIndices()?.getArray()??Uint32Array.from({length:pos.getCount()},(_,i)=>i),name=p.getMaterial()?.getName()??'',selected=[];
  const vertex=i=>Object.fromEntries(p.listSemantics().map(k=>[k,p.getAttribute(k).getElement(i,[])]));
  function accept(id,tris){for(const t of tris)areas[id]+=area(t);counts[id]+=tris.length;if(id===selection)selected.push(...tris);}
  for(const g of triangleIslands(pos.getArray(),indices)){
   const whole=wholePanel(g,name),rules=whole?[]:rulesFor(g,name);
   for(const offset of g.triangleOffsets){const tri=[0,1,2].map(k=>vertex(indices[offset+k]));sourceArea+=area(tri);
    if(whole){accept(whole,[tri]);continue;}
    let rest=[tri];for(const rule of rules){const next=[];for(const t of rest){const r=partitionTriangle(t,rule.planes);accept(rule.id,triangulate(r.inside));next.push(...triangulate(r.outside));}rest=next;}
    accept('body',rest);
   }
  }
  append(selected,p.getMaterial());
  if(selection!=='body'&&selected.length&&(name==='body'||name==='window')){
   const extra=panelShell(selected,name==='window'?.0015:.0012);
   const innerMaterial=name==='window'?p.getMaterial():doc.getRoot().listMaterials().find(m=>m.getName()==='mottled')??p.getMaterial();
   append(extra.skin,innerMaterial);append(extra.rim,innerMaterial);
   shell.skinTriangles+=extra.skin.length;shell.rimTriangles+=extra.rim.length;
   shell.addedArea+=[...extra.skin,...extra.rim].reduce((n,t)=>n+area(t),0);
  }
 }
 if(Math.abs(Object.values(areas).reduce((a,b)=>a+b,0)-sourceArea)>1e-6||defs.some(d=>areas[d.id]<.25)||areas.body<50)throw Error('Incomplete same-E39 surface partition');
 const def=defs.find(d=>d.id===selection);if(def)transformMesh(mesh,[1,0,0,0,0,1,0,0,0,0,1,0,...def.pivot.map(v=>-v),1]);
 for(const n of scene.listChildren())scene.removeChild(n);scene.addChild(doc.createNode(selection).setMesh(mesh));await doc.transform(prune());
 const data=await io.writeBinary(doc),b=getBounds(scene);await preserve(selection+'.glb',data);
 models.push({id:selection,file:selection+'.glb',bytes:data.length,sha256:hash(data),triangles:counts[selection]+shell.skinTriangles+shell.rimTriangles,originalTriangles:counts[selection],addedShell:shell,dimensionsMetresYUp:b.max.map((v,i)=>v-b.min[i]),originMetresYUp:b.max.map((v,i)=>(v+b.min[i])/2),objectPath:'/Game/Anomalia/BMWE39Review_v5/'+selection+'/SM_'+selection});
 partition={sourceArea,areas,triangles:counts};
}
for(const m of previous.models.filter(m=>m.id==='door_driver'||m.id.startsWith('wheel_'))){const b=await readFile(path.join(base,m.file));if(hash(b)!==m.sha256)throw Error('Validated E39 part changed');await preserve(m.file,b);models.push({...m,objectPath:'/Game/Anomalia/BMWE39Review_v5/'+m.id+'/SM_'+m.id});}
const panels=[{...previous.panels[0],hingeAxis:[0,0,1]},...defs.map(d=>({id:d.id,pivotCm:gltfToUnreal(d.pivot),hingeAxis:d.axis,openAngleDegrees:d.angle,apertureCm:d.aperture,traceOutward:d.normal,fixtureStandCm:d.stand,fixtureAimCm:d.id.startsWith('door_rear')?[-70,d.pivot[2]*100,75]:gltfToUnreal(models.find(m=>m.id===d.id).originMetresYUp.map((v,i)=>v+d.pivot[i]))}))];
const manifest={schemaVersion:4,source:previous.source,parentBodySha256:parent.sha256,models,panels,wheelHubsCm:previous.wheelHubsCm,closedBodyBoundsCm:previous.closedBodyBoundsCm,surfacePartition:partition,driverDoorPartition:previous.sourceCoverage.partition,completeVehicleAccepted:false,gameplayVerified:false};
await preserve('manifest.json',JSON.stringify(manifest,null,2)+'\n');await preserve('CREDITS.md',(await readFile(path.join(base,'CREDITS.md'),'utf8'))+'\nAdditional changes: same-source passenger/rear leaves, hood and trunk separated with authored glazing silhouettes and conserved original area. Added inward metal skins (1.2 mm) and glass skins (1.5 mm) close formerly one-sided surfaces; added geometry is accounted separately. Driver leaf and four wheels remain byte-identical to v2. Native motion/collision/interactions and final art still require acceptance.\n');
console.log(JSON.stringify({state:'SAME_E39_ALL_PANELS_PREPARED_NOT_GAME_VERIFIED',partition,panels:panels.map(p=>p.id)}));
