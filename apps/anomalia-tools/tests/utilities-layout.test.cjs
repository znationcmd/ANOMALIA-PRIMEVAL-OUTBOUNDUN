'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const {PNG}=require('pngjs');
const {AnomaliaTools}=require('../core.cjs');
const root=path.join(__dirname,'..');
function workspace(){
 const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'anomalia-tools-utils-'));
 const app=new AnomaliaTools(path.join(tmp,'private-workspaces'));
 const p=app.createProject({name:'Test Utilities'});
 const home=app.getProjectPath(p.id);
 return {tmp,app,projectId:p.id,home};
}
test('real heightmap processor produces a new valid PNG without overwriting source',()=>{
 const t=workspace();
 try{
  const png=new PNG({width:16,height:16});
  for(let y=0;y<16;y++)for(let x=0;x<16;x++){
   const k=4*(y*16+x);png.data[k]=png.data[k+1]=png.data[k+2]=x*10+y;png.data[k+3]=255;
  }
  const input=path.join(t.home,'Content','Terrain','test.png');
  const initial=PNG.sync.write(png);fs.writeFileSync(input,initial);
  for(const mode of ['normalize','invert','smooth']){
   const o=t.app.processTerrain({projectId:t.projectId,source:'Content/Terrain/test.png',mode});
   assert.equal(o.saved,true);
   const output=PNG.sync.read(fs.readFileSync(path.join(t.home,o.path)));
   assert.equal(output.width,16);assert.equal(output.height,16);
  }
  assert.deepEqual(fs.readFileSync(input),initial);
 }finally{fs.rmSync(t.tmp,{recursive:true,force:true});}
});
test('PNG to TGA converter emits true-color BGRA 32-bit image, not fake PAA',()=>{
 const t=workspace();
 try{
  const img=new PNG({width:2,height:1});
  img.data.set([255,0,10,255,0,255,20,100]);
  fs.writeFileSync(path.join(t.home,'Content','Textures','sample.png'),PNG.sync.write(img));
  const r=t.app.convertTexture({projectId:t.projectId,source:'Content/Textures/sample.png'});
  const output=fs.readFileSync(path.join(t.home,r.path));
  assert.equal(output[2],2);assert.equal(output.readUInt16LE(12),2);
  assert.equal(output.readUInt16LE(14),1);assert.equal(output[16],32);
  assert.deepEqual([...output.subarray(18,22)],[10,0,255,255]);
  assert.match(r.note,/n’est pas un .paa/);
 }finally{fs.rmSync(t.tmp,{recursive:true,force:true});}
});
test('config converter reads INI and JSON without changing original',()=>{
 const t=workspace();
 try{
  const input=path.join(t.home,'Config','Game.ini');
  fs.writeFileSync(input,'[Survival]\nCold=5\nFood=3\n');
  const out=t.app.convertConfig({projectId:t.projectId,source:'Config/Game.ini'});
  const data=JSON.parse(fs.readFileSync(path.join(t.home,out.path),'utf8'));
  assert.equal(data.data.Survival.Cold,'5');
  assert.equal(data.schema,'anomalia-converted-config');
  assert.match(fs.readFileSync(input,'utf8'),/Food=3/);
  assert.throws(()=>t.app.convertConfig({projectId:t.projectId,source:'../etc/passwd'}));
  assert.throws(()=>t.app.processTerrain({projectId:t.projectId,source:'Config/Game.ini'}));
 }finally{fs.rmSync(t.tmp,{recursive:true,force:true});}
});
test('all DayZ Tools reference buttons are visible and scroll does not clip sidebar',()=>{
 const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
 const css=fs.readFileSync(path.join(root,'src','tools-workspace-fix.css'),'utf8');
 const renderer=fs.readFileSync(path.join(root,'src','renderer.js'),'utf8');
 for(const key of ['terrainProcessor','bankrev','imagepaa','cfgconvert','dsutils','texview','navmesh']){
   assert.match(html,new RegExp('data-utility="'+key+'"'));
   assert.match(html,new RegExp('data-util-panel="'+key+'"'));
 }
 for(const item of ['File','View','Settings','Tools','Help'])assert.match(html,new RegExp('>'+item+'<\\/button>'));
 assert.match(css,/\.sidebar \.sidebarNav\{[^}]*overflow-y:auto/s);
 assert.match(css,/\.shell\{height:100dvh!important;min-height:0!important/);
 assert.match(css,/max-height:100dvh!important/);
 assert.match(renderer,/setupToolsUtilities/);
});
