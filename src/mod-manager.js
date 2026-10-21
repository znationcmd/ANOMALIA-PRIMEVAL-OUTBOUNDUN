/** Safe, pure mod resolution for ANOMALIA. Does not download or execute untrusted packages. */
const validId=id=>typeof id==='string'&&/^[a-z0-9][a-z0-9._-]{1,79}$/.test(id);
const validHash=hash=>typeof hash==='string'&&/^[a-fA-F0-9]{64}$/.test(hash);
export function validateModManifest(mod){
 if(!mod||!validId(mod.id))throw Error('Invalid mod ID');
 if(typeof mod.version!=='string'||!/^[0-9]+\.[0-9]+\.[0-9]+(?:-[a-zA-Z0-9.-]+)?$/.test(mod.version))throw Error('Invalid mod version');
 if(!validHash(mod.sha256))throw Error('Missing SHA-256 checksum');
 if(!Array.isArray(mod.dependencies)||!mod.dependencies.every(validId))throw Error('Invalid dependencies');
 if(!['solo','cmd-hosting','dedicated'].some(mode=>mod.compatibility?.includes(mode)))throw Error('No supported installation mode');
 if(mod.signed!==true)throw Error('Unsigned mod rejected');
 return true;
}
export function resolveMods(requested,catalog,installed=[]){
 const byId=new Map(catalog.map(mod=>[mod.id,mod]));
 if(byId.size!==catalog.length)throw Error('Duplicate catalog mod IDs');
 const ready=[],visiting=new Set(),visited=new Set();
 function visit(id){
  if(visited.has(id))return;
  if(visiting.has(id))throw Error('Circular mod dependency: '+id);
  const mod=byId.get(id);if(!mod)throw Error('Missing mod dependency: '+id);
  validateModManifest(mod);visiting.add(id);
  for(const dep of mod.dependencies)visit(dep);
  visiting.delete(id);visited.add(id);ready.push(mod);
 }
 for(const id of requested)visit(id);
 const current=new Map(installed.map(mod=>[mod.id,mod]));
 return {required:ready,downloads:ready.filter(mod=>current.get(mod.id)?.sha256!==mod.sha256),alreadyInstalled:ready.filter(mod=>current.get(mod.id)?.sha256===mod.sha256),requiresConsent:true};
}
export function validatePlacementManifest(manifest){
 if(!manifest||!Array.isArray(manifest.files))throw Error('Invalid mapping manifest');
 for(const file of manifest.files){
  if(typeof file!=='string'||file.startsWith('/')||file.includes('..')||file.includes('\\')||/[\x00-\x1f:#?%]/.test(file)||file.split('/').some(part=>!part||/[. ]$/.test(part))||!file.endsWith('.json'))throw Error('Unsafe mapping path');
 }
 return true;
}
