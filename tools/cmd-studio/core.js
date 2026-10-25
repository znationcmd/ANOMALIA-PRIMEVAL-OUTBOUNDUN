'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { spawn } = require('node:child_process');
const { pipeline } = require('node:stream/promises');
const { Readable, Transform } = require('node:stream');

const ANOMALIA_UPROJECT = 'AnomaliaPrimeval.uproject';
const ANOMALIA_TITLE = 'ANOMALIA PRIMEVAL OUTBOUNDUN';
const FORMATS = new Set(['.glb','.gltf','.fbx','.obj','.blend','.usd','.usdz','.png','.jpg','.jpeg','.tga','.exr','.hdr']);
const UNREAL_FORMATS = new Set(['.glb','.gltf','.fbx','.obj','.usd']);
const MAX_DOWNLOAD = 350 * 1024 * 1024;
const ALLOWED_DOWNLOAD_HOSTS = new Set(['cdn.polyhaven.com','dl.polyhaven.org','polyhaven.com','api.polyhaven.com']);

function readJSON(filename, fallback) {
  try { return JSON.parse(fs.readFileSync(filename, 'utf8')); }
  catch { return fallback; }
}
function atomicWrite(filename, data) {
  fs.mkdirSync(path.dirname(filename), { recursive: true });
  const temp = filename + '.' + crypto.randomUUID() + '.tmp';
  fs.writeFileSync(temp, JSON.stringify(data, null, 2), 'utf8');
  fs.renameSync(temp, filename);
}
function assertFile(filename, ext = null) {
  if (typeof filename !== 'string' || !fs.existsSync(filename) || !fs.statSync(filename).isFile()) throw new Error('Fichier introuvable : ' + filename);
  if (ext && path.extname(filename).toLowerCase() !== ext) throw new Error('Extension attendue : ' + ext);
  return path.resolve(filename);
}
async function hashFile(filename) {
  const hash = crypto.createHash('sha256');
  for await (const chunk of fs.createReadStream(filename)) hash.update(chunk);
  return hash.digest('hex');
}
async function jsonGet(url) {
  const response = await fetch(url, { headers: { 'User-Agent': 'CMD-Studio/0.1', Accept: 'application/json' }, signal: AbortSignal.timeout(20000), redirect: 'error' });
  if (!response.ok) throw new Error('Catalogue indisponible (HTTP ' + response.status + ')');
  return response.json();
}
function filenameSafe(value) { return String(value).replace(/[^a-z0-9_-]/gi, '_').slice(0, 75); }
function run(command, args, env, timeout = 600000) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { shell: false, windowsHide: true, env: { ...process.env, ...env } });
    let output = '';
    let ended = false;
    const timer = setTimeout(() => { child.kill(); }, timeout);
    for (const stream of [child.stdout, child.stderr]) {
      stream?.on('data', chunk => { output = (output + chunk.toString()).slice(-14000); });
    }
    child.on('error', e => { if (!ended) { ended = true; clearTimeout(timer); reject(e); } });
    child.on('close', code => {
      if (ended) return;
      ended = true; clearTimeout(timer);
      if (code === 0) resolve({ ok: true, log: output.slice(-4000) });
      else reject(new Error('Exécution échouée (code ' + code + ') :\n' + output.slice(-1800)));
    });
  });
}
function fileCandidates(node, parents = []) {
  if (!node || typeof node !== 'object') return [];
  const found = [];
  if (typeof node.url === 'string' && /^https:\/\//i.test(node.url)) {
    const url = new URL(node.url);
    const extension = path.extname(url.pathname).toLowerCase();
    if (['.blend','.glb','.fbx','.obj','.usd','.zip'].includes(extension))
      found.push({ url: node.url, extension, parents, size: Number(node.size || 0) });
  }
  for (const [key, value] of Object.entries(node))
    if (value && typeof value === 'object') found.push(...fileCandidates(value, [...parents, key]));
  return found;
}

class Studio {
  constructor(dataDir, scriptsDir) {
    this.dataDir = dataDir;
    this.scriptsDir = scriptsDir;
    this.configPath = path.join(dataDir, 'studio.json');
    this.libraryPath = path.join(dataDir, 'assets');
    this.settingsData = readJSON(this.configPath, { blenderPath: '', unrealPath: '', projects: [], activeProject: '' });
    this.catalogPath = path.join(dataDir, 'catalog.json');
    this.catalog = readJSON(this.catalogPath, []);
    fs.mkdirSync(this.libraryPath, { recursive: true });
  }
  settings() { return { ...this.settingsData, libraryPath: this.libraryPath }; }
  status() {
    const settings = this.settings();
    return {
      blender: Boolean(settings.blenderPath && fs.existsSync(settings.blenderPath)),
      unreal: Boolean(settings.unrealPath && fs.existsSync(settings.unrealPath)),
      project: settings.projects.some(p => p.path === settings.activeProject && fs.existsSync(p.path)),
      assets: this.catalog.length,
      projects: settings.projects.length
    };
  }
  configure({ blenderPath, unrealPath } = {}) {
    if (blenderPath !== undefined) this.settingsData.blenderPath = blenderPath ? assertFile(blenderPath) : '';
    if (unrealPath !== undefined) this.settingsData.unrealPath = unrealPath ? assertFile(unrealPath) : '';
    atomicWrite(this.configPath, this.settingsData);
    return this.settings();
  }
  addProject({ file } = {}) {
    const project = assertFile(file, '.uproject');
    if (!this.settingsData.projects.some(p => p.path === project))
      this.settingsData.projects.push({ name: path.basename(project).toLowerCase() === ANOMALIA_UPROJECT.toLowerCase() ? ANOMALIA_TITLE : path.basename(project, '.uproject'), path: project });
    this.settingsData.activeProject = project;
    atomicWrite(this.configPath, this.settingsData);
    return this.projects();
  }
  projects() {
    const saved = this.settingsData.projects.find(p =>
      path.basename(p.path).toLowerCase() === ANOMALIA_UPROJECT.toLowerCase());
    const sourceCandidate = path.resolve(this.scriptsDir, '..','..','..','unreal',ANOMALIA_UPROJECT);
    const detected = fs.existsSync(sourceCandidate) && fs.statSync(sourceCandidate).isFile() ? sourceCandidate : '';
    const known = saved?.path || detected;
    return {
      items: this.settingsData.projects.map(p => ({ ...p, available: fs.existsSync(p.path) })),
      active: this.settingsData.activeProject,
      featured: { id:'anomalia-primeval', name:ANOMALIA_TITLE, engine:'Unreal Engine 5',
        path: known || '', available:Boolean(known && fs.existsSync(known)),
        linked:Boolean(saved), detected:Boolean(!saved && detected),
        status: known && fs.existsSync(known) ? 'disponible' : 'a-associer' }
    };
  }
  selectProject({ file } = {}) {
    const existing = this.settingsData.projects.find(p => p.path === file);
    if (!existing) throw new Error('Projet non enregistré : associe d’abord son fichier .uproject.');
    assertFile(existing.path, '.uproject');
    this.settingsData.activeProject = existing.path;
    atomicWrite(this.configPath, this.settingsData);
    return this.projects();
  }
  assets() { return [...this.catalog].reverse(); }
  async recordAsset(file, metadata = {}) {
    const resolved = assertFile(file);
    const extension = path.extname(resolved).toLowerCase();
    if (!FORMATS.has(extension)) throw new Error('Format non pris en charge : ' + extension);
    const sha256 = await hashFile(resolved);
    const existing = this.catalog.find(a => a.sha256 === sha256);
    if (existing) return existing;
    const output = path.join(this.libraryPath, sha256.slice(0, 12) + '-' + filenameSafe(path.basename(resolved)));
    if (path.resolve(resolved) !== path.resolve(output)) fs.copyFileSync(resolved, output, fs.constants.COPYFILE_EXCL);
    const asset = {
      id: crypto.randomUUID(), name: path.basename(resolved), path: output, format: extension.slice(1),
      size: fs.statSync(output).size, sha256, source: metadata.source || 'local',
      license: metadata.license || 'À vérifier avant utilisation', origin: metadata.origin || '',
      addedAt: new Date().toISOString()
    };
    this.catalog.push(asset);
    atomicWrite(this.catalogPath, this.catalog);
    return asset;
  }
  async import({ files = [] } = {}) {
    if (!Array.isArray(files) || files.length > 100) throw new Error('Liste de fichiers invalide.');
    const added = [];
    for (const filename of files) added.push(await this.recordAsset(filename));
    return added;
  }
  async search({ provider = 'polyhaven', query = '' } = {}) {
    const text = String(query || '').trim().toLowerCase().slice(0, 100);
    if (provider === 'polyhaven') {
      const response = await jsonGet('https://api.polyhaven.com/assets?t=models');
      return Object.entries(response).filter(([id, a]) =>
        !text || [id, a.name, ...(a.categories || [])].join(' ').toLowerCase().includes(text))
        .slice(0, 60).map(([id, a]) => ({
          id, name: a.name || id, provider, license: 'CC0',
          thumbnail: 'https://cdn.polyhaven.com/asset_img/thumbs/' + encodeURIComponent(id) + '.png?height=180',
          url: 'https://polyhaven.com/a/' + encodeURIComponent(id), downloadable: true
        }));
    }
    if (provider === 'sketchfab') {
      const response = await jsonGet('https://api.sketchfab.com/v3/search?type=models&q=' + encodeURIComponent(text) + '&count=24');
      return (response.results || []).map(a => ({
        id: a.uid, name: a.name, provider, license: a.license?.label || 'Voir licence',
        thumbnail: a.thumbnails?.images?.[0]?.url || '',
        url: a.viewerUrl || 'https://sketchfab.com/3d-models/' + encodeURIComponent(a.uid),
        downloadable: false
      }));
    }
    throw new Error('Plateforme non prise en charge.');
  }
  async downloadPolyHaven({ id } = {}) {
    if (!/^[a-z0-9_-]{2,100}$/i.test(id || '')) throw new Error('Identifiant incorrect.');
    const files = await jsonGet('https://api.polyhaven.com/files/' + encodeURIComponent(id));
    const options = fileCandidates(files).filter(a => a.extension !== '.zip');
    options.sort((a,b) => {
      const rank = x => ['.blend','.glb','.fbx','.obj','.usd'].indexOf(x.extension);
      return rank(a) - rank(b) || a.size - b.size;
    });
    const candidate = options[0];
    if (!candidate) throw new Error('Aucun format individuel compatible. Ouvre la fiche Poly Haven pour les autres fichiers.');
    let url = new URL(candidate.url);
    if (!ALLOWED_DOWNLOAD_HOSTS.has(url.hostname)) throw new Error('Hôte de téléchargement non autorisé.');
    let response;
    for (let i=0;i<4;i++) {
      response = await fetch(url, { signal: AbortSignal.timeout(120000), redirect: 'manual' });
      if ([301,302,303,307,308].includes(response.status)) {
        url = new URL(response.headers.get('location'), url);
        if (url.protocol !== 'https:' || !ALLOWED_DOWNLOAD_HOSTS.has(url.hostname))
          throw new Error('Redirection de téléchargement non autorisée.');
        continue;
      }
      break;
    }
    if (!response?.ok || !response.body) throw new Error('Échec du téléchargement Poly Haven.');
    if (Number(response.headers.get('content-length') || 0) > MAX_DOWNLOAD)
      throw new Error('Ressource supérieure à 350 Mo.');
    const temp = path.join(this.dataDir, crypto.randomUUID() + candidate.extension);
    let received = 0;
    const limiter = new Transform({
      transform(chunk, _encoding, done) {
        received += chunk.length;
        done(received > MAX_DOWNLOAD ? new Error('Taille maximale dépassée.') : null, chunk);
      }
    });
    try {
      await pipeline(Readable.fromWeb(response.body), limiter, fs.createWriteStream(temp, { flags: 'wx' }));
      return await this.recordAsset(temp, { source: 'polyhaven', license: 'CC0', origin: 'https://polyhaven.com/a/' + id });
    } finally { fs.rmSync(temp, { force: true }); }
  }
  assetById(id) {
    const asset = this.catalog.find(a => a.id === id);
    if (!asset || !fs.existsSync(asset.path)) throw new Error('Ressource absente de la bibliothèque.');
    return asset;
  }
  async convertBlender({ id } = {}) {
    const asset = this.assetById(id);
    const executable = assertFile(this.settingsData.blenderPath);
    if (asset.format === 'glb') return asset;
    if (!['fbx','obj','blend','gltf','usd','usdz'].includes(asset.format))
      throw new Error('Format non pris en charge par ce convertisseur.');
    const output = path.join(this.libraryPath, crypto.randomUUID() + '.glb');
    const blend = asset.format === 'blend';
    const args = [...(blend ? [asset.path] : []), '--background', '--python',
      path.join(this.scriptsDir,'blender_convert.py'), '--', asset.path, output];
    try {
      await run(executable, args, {}, 600000);
      return await this.recordAsset(output, { source: 'blender', license: asset.license, origin: asset.origin });
    } finally { fs.rmSync(output, { force: true }); }
  }
  async importUnreal({ id } = {}) {
    const asset = this.assetById(id);
    if (!UNREAL_FORMATS.has('.' + asset.format)) throw new Error('Convertis d’abord cette ressource en GLB/FBX.');
    const executable = assertFile(this.settingsData.unrealPath);
    const project = assertFile(this.settingsData.activeProject, '.uproject');
    const manifest = path.join(this.dataDir, 'import-' + crypto.randomUUID() + '.json');
    atomicWrite(manifest, { source: asset.path, destination: '/Game/CMDStudio/' + filenameSafe(path.parse(asset.name).name) });
    try {
      return await run(executable, [project,'-unattended','-nop4','-run=pythonscript',
        '-script=' + path.join(this.scriptsDir,'unreal_import.py')],
        { CMD_STUDIO_IMPORT_MANIFEST: manifest }, 900000);
    } finally { fs.rmSync(manifest, { force: true }); }
  }
  openTool({ tool } = {}) {
    let executable, args = [];
    if (tool === 'blender') executable = assertFile(this.settingsData.blenderPath);
    else if (tool === 'unreal') {
      const configured = assertFile(this.settingsData.unrealPath);
      const graphical = configured.replace(/UnrealEditor-Cmd\.exe$/i, 'UnrealEditor.exe');
      executable = fs.existsSync(graphical) ? graphical : configured;
      args = this.settingsData.activeProject ? [assertFile(this.settingsData.activeProject, '.uproject')] : [];
    } else throw new Error('Logiciel inconnu.');
    const child = spawn(executable, args, { detached: true, stdio: 'ignore', shell: false });
    child.unref();
    return { ok: true, started: tool };
  }
  previewAsset({ id } = {}) {
    const asset=this.assetById(id);
    const format=String(asset.format||'').toLowerCase();
    if(!['glb','png','jpg','jpeg'].includes(format))
      throw new Error('Prévisualisation disponible uniquement pour GLB, PNG ou JPEG. Convertis les autres modèles en GLB avec Blender.');
    const size=fs.statSync(asset.path).size;
    if(size<=0||size>24*1024*1024)
      throw new Error('Le visualiseur accepte uniquement les fichiers jusqu’à 24 Mo. Le modèle reste dans la bibliothèque.');
    return {id:asset.id,name:asset.name,format,license:asset.license,size,
      data:fs.readFileSync(asset.path).toString('base64')};
  }
  openAsset({ id } = {}) {
    const asset = this.assetById(id);
    const command = process.platform === 'win32' ? 'explorer.exe' : process.platform === 'darwin' ? 'open' : 'xdg-open';
    const args = process.platform === 'win32' ? ['/select,' + asset.path] :
      process.platform === 'darwin' ? ['-R', asset.path] : [path.dirname(asset.path)];
    const child = spawn(command, args, { detached: true, stdio: 'ignore', shell: false });
    child.unref();
    return { ok: true };
  }
}

module.exports = { Studio, fileCandidates, filenameSafe, FORMATS };
