'use strict';
// Génère les icônes Windows à partir du symbole du logo ANOMALIA Tools approuvé.
// La source est un recadrage du logo orange métallique : emblème A, engrenage, clé et tournevis.
const fs=require('node:fs');
const path=require('node:path');
const {PNG}=require('pngjs');
const sourcePath=path.join(__dirname,'..','assets','anomalia-tools-icon.png');
const outPath=path.join(__dirname,'..','assets','anomalia-tools.ico');
const source=PNG.sync.read(fs.readFileSync(sourcePath));
if(source.width!==96||source.height!==96)throw new Error('Image d’icône source inattendue');
const sizes=[16,24,32,48,64,96,128,256];
const images=[];
function constrain(n,min,max){return Math.min(max,Math.max(min,n));}
function makePNG(size){
  const result=new PNG({width:size,height:size});
  for(let y=0;y<size;y++)for(let x=0;x<size;x++){
    const xx=(x+.5)*source.width/size-.5,yy=(y+.5)*source.height/size-.5;
    const ax=constrain(Math.floor(xx),0,source.width-1);
    const ay=constrain(Math.floor(yy),0,source.height-1);
    const bx=constrain(ax+1,0,source.width-1);
    const by=constrain(ay+1,0,source.height-1);
    const tx=constrain(xx-Math.floor(xx),0,1);
    const ty=constrain(yy-Math.floor(yy),0,1);
    for(let c=0;c<4;c++){
      const pix=(px,py)=>source.data[(py*source.width+px)*4+c];
      const a=pix(ax,ay)*(1-tx)+pix(bx,ay)*tx;
      const b=pix(ax,by)*(1-tx)+pix(bx,by)*tx;
      result.data[(y*size+x)*4+c]=Math.round(a*(1-ty)+b*ty);
    }
  }
  return PNG.sync.write(result);
}
for(const size of sizes)images.push(makePNG(size));
const header=Buffer.alloc(6+16*sizes.length);
header.writeUInt16LE(1,2);
header.writeUInt16LE(sizes.length,4);
let offset=header.length;
for(let i=0;i<sizes.length;i++){
  const size=sizes[i],png=images[i],index=6+16*i;
  header.writeUInt8(size===256?0:size,index);
  header.writeUInt8(size===256?0:size,index+1);
  header.writeUInt16LE(1,index+4);
  header.writeUInt16LE(32,index+6);
  header.writeUInt32LE(png.length,index+8);
  header.writeUInt32LE(offset,index+12);
  offset+=png.length;
}
fs.writeFileSync(outPath,Buffer.concat([header,...images]));
console.log('ANOMALIA Tools : icône multi-tailles Windows créée : '+outPath);
