import {defineConfig} from 'vite';
import {execFileSync} from 'node:child_process';
import {writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';

const appRoot=path.dirname(fileURLToPath(import.meta.url));
function sourceRevision(){
  const env=String(process.env.ANOMALIA_WEB_REVISION||'').trim();
  if(/^[a-zA-Z0-9._-]{6,100}$/.test(env))return env;
  try{
    const git=execFileSync('git',['rev-parse','HEAD'],{
      cwd:appRoot,encoding:'utf8',stdio:['ignore','pipe','ignore']
    }).trim();
    if(/^[0-9a-f]{40}$/.test(git))return git;
  }catch{}
  return 'local-dev';
}
export default defineConfig(({command})=>{
  const revision=sourceRevision();
  if(command==='build'){
    // Vite copies this file to dist/release.json, beside the public PWA.
    // Both the running JS bundle and remote release endpoint get the SAME ID.
    writeFileSync(path.join(appRoot,'public','release.json'),
      JSON.stringify({schema:1,app:'ANOMALIA Editor PWA',revision})+'\n');
  }
  return {
    base:'./',
    define:{__ANOMALIA_WEB_BUILD__:JSON.stringify(revision)},
    build:{outDir:'dist',emptyOutDir:true,target:'es2022',assetsInlineLimit:0},
    server:{strictPort:true,port:4174},
  };
});
