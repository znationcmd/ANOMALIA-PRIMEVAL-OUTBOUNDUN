'use strict';
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..'),ui=path.join(root,'ui'),out=path.join(root,'mobile-dist');
fs.rmSync(out,{recursive:true,force:true});
fs.mkdirSync(path.join(out,'generated'),{recursive:true});
for(const name of ['index.html','style.css','ui.js','mobile-api.js','manifest.webmanifest','icon.svg','sw.js']){
 fs.copyFileSync(path.join(ui,name),path.join(out,name));
}
for(const name of ['viewer.bundle.js','hero.jpg','search.jpg','projects.jpg']){
 const src=path.join(ui,'generated',name);
 if(fs.existsSync(src))fs.copyFileSync(src,path.join(out,'generated',name));
 else if(name==='viewer.bundle.js')throw Error('Three.js viewer not compiled');
}
console.log('CMD Studio private mobile PWA ready in mobile-dist (NOT published publicly).');
