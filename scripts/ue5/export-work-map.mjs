/** Export exact Work/JS geographic heightAt() to an Unreal Landscape RAW heightmap.
 * Preserves Work's 48 km world and eight landmasses; DOES NOT write .umap or overwrite maps.
 * Run: node scripts/ue5/export-work-map.mjs
 */
import { heightAt, WORLD_HALF, CITIES, SITES, CONTINENTS, PEAKS } from '../../src/mechanics.js';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const samples = 3025;
const widthMetres = WORLD_HALF * 2;
const stepMetres = widthMetres / (samples - 1);
const zScaleCm = 800;
const codesPerMetre = 12800 / zScaleCm;
const folder = path.resolve('unreal/TerrainWorkImport');
const target = path.join(folder, 'ANOMALIA_WorkMap_48km_3025.r16');
const metadataFile = target.replace(/\.r16$/, '.json');
const landmarksFile = path.join(folder, 'ANOMALIA_WorkMap_Landmarks.json');

if (fs.existsSync(target) || fs.existsSync(metadataFile) || fs.existsSync(landmarksFile)) {
  console.error('ANOMALIA Work terrain: output already exists; nothing overwritten. Move or back up existing export before regenerating.');
  process.exit(2);
}
fs.mkdirSync(folder, { recursive: true });
const fd = fs.openSync(target, 'wx');
const sha = crypto.createHash('sha256');
let minimum = Infinity, maximum = -Infinity, landSamples = 0;
try {
  for (let y = 0; y < samples; y++) {
    const north = WORLD_HALF - y * stepMetres;
    const row = Buffer.allocUnsafe(samples * 2);
    for (let x = 0; x < samples; x++) {
      const east = -WORLD_HALF + x * stepMetres;
      const h = heightAt(east, north);
      if (!Number.isFinite(h)) throw Error('Invalid terrain altitude');
      minimum = Math.min(minimum, h);
      maximum = Math.max(maximum, h);
      if (h > 0.5) landSamples++;
      const encoded = Math.round(32768 + h * codesPerMetre);
      if (encoded < 0 || encoded > 65535) {
        throw Error('Terrain altitude exceeds Z scale 800 at ' + east + ',' + north);
      }
      row.writeUInt16LE(encoded, x * 2);
    }
    fs.writeSync(fd, row);
    sha.update(row);
    if (y % 500 === 0) console.log('ANOMALIA terrain rows ' + y + '/' + samples);
  }
} catch (error) {
  fs.closeSync(fd);
  fs.unlinkSync(target);
  throw error;
}
fs.closeSync(fd);
const info = {
  source: 'src/mechanics.js heightAt() (Work JS map, not older Unreal six-island draft)',
  status: 'landscape_source_generated_not_imported_into_unreal',
  extentKm: [48, 48],
  rawResolution: [samples, samples],
  // Landscape RAW sidecar keys; Epic's RAW parser expects "bbp" (not "bpp").
  width: samples,
  height: samples,
  bbp: 16,
  format: 'r16 unsigned 16-bit little-endian, no header',
  landscapeScaleCm: { x: stepMetres * 100, y: stepMetres * 100, z: zScaleCm },
  seaLevelZCm: 0,
  heightRangeM: [minimum, maximum],
  landEstimateKm2AtThisResolution: landSamples * stepMetres * stepMetres / 1e6,
  referenceWorkLandKm2At25m: 374.521875,
  areaKm2: 2304,
  sizeBytes: fs.statSync(target).size,
  sha256: sha.digest('hex'),
  note: 'Heightmap only. Roads, cities, ocean, animals and AI need separate Unreal assets and code.'
};
const sites = {
  source: 'src/mechanics.js',
  status: 'source_coordinates_only_not_spawned_in_unreal',
  coordinateSystem: 'Work x/east and z/north in metres; convert to Unreal cm as X=x*100 and Y=z*100, verify axis orientation in editor',
  continents: CONTINENTS,
  cities: CITIES,
  peaks: PEAKS,
  sites: SITES
};
fs.writeFileSync(metadataFile, JSON.stringify(info, null, 2) + '\n', { flag: 'wx' });
fs.writeFileSync(landmarksFile, JSON.stringify(sites, null, 2) + '\n', { flag: 'wx' });
console.log('Work terrain exported: ' + target);
console.log(JSON.stringify(info, null, 2));
