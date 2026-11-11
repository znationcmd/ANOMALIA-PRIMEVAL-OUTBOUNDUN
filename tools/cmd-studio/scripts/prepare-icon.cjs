'use strict';
// Agrandit automatiquement l'icône officielle CMD Studio pour les installateurs Windows.
// Image source dérivée du logo validé par le propriétaire. Aucun téléchargement externe.
const fs = require('node:fs');
const path = require('node:path');
const { PNG } = require('pngjs');
const root = path.join(__dirname, '..', 'resources');
const input = path.join(root, 'cmd-studio.ico');
const output = path.join(root, 'cmd-studio-256.ico');

const bytes = fs.readFileSync(input);
if (bytes.length < 30 || bytes.readUInt16LE(0) !== 0 || bytes.readUInt16LE(2) !== 1 ||
    bytes.readUInt16LE(4) !== 1) throw new Error('Icône officielle invalide.');
const sourceLen = bytes.readUInt32LE(14);
const sourceOffset = bytes.readUInt32LE(18);
if (sourceOffset + sourceLen > bytes.length) throw new Error('Données ICO incomplètes.');
const rawPng = bytes.subarray(sourceOffset, sourceOffset + sourceLen);
if (rawPng.subarray(0, 8).toString('hex') !== '89504e470d0a1a0a')
  throw new Error('L’icône source n’est pas un PNG.');
const source = PNG.sync.read(rawPng);
const max = 256;
const result = new PNG({ width: max, height: max });
function clamp(value, maximum) { return Math.max(0, Math.min(maximum, value)); }
for (let y = 0; y < max; y++) {
  for (let x = 0; x < max; x++) {
    const fx = (x + .5) * source.width / max - .5;
    const fy = (y + .5) * source.height / max - .5;
    const x0 = clamp(Math.floor(fx), source.width - 1);
    const x1 = clamp(x0 + 1, source.width - 1);
    const y0 = clamp(Math.floor(fy), source.height - 1);
    const y1 = clamp(y0 + 1, source.height - 1);
    const tx = Math.max(0, Math.min(1, fx - Math.floor(fx)));
    const ty = Math.max(0, Math.min(1, fy - Math.floor(fy)));
    for (let channel = 0; channel < 4; channel++) {
      const a = source.data[(y0 * source.width + x0) * 4 + channel];
      const b = source.data[(y0 * source.width + x1) * 4 + channel];
      const c = source.data[(y1 * source.width + x0) * 4 + channel];
      const d = source.data[(y1 * source.width + x1) * 4 + channel];
      const ab = a * (1 - tx) + b * tx;
      const cd = c * (1 - tx) + d * tx;
      result.data[(y * max + x) * 4 + channel] = Math.round(ab * (1 - ty) + cd * ty);
    }
  }
}
const png256 = PNG.sync.write(result);
const directory = Buffer.alloc(6 + 16 * 2);
directory.writeUInt16LE(1, 2);
directory.writeUInt16LE(2, 4);
function entry(index, width, png, offset) {
  const at = 6 + 16 * index;
  directory.writeUInt8(width === 256 ? 0 : width, at);
  directory.writeUInt8(width === 256 ? 0 : width, at + 1);
  directory.writeUInt16LE(1, at + 4);
  directory.writeUInt16LE(32, at + 6);
  directory.writeUInt32LE(png.length, at + 8);
  directory.writeUInt32LE(offset, at + 12);
}
entry(0, source.width, rawPng, directory.length);
entry(1, 256, png256, directory.length + rawPng.length);
fs.writeFileSync(output, Buffer.concat([directory, rawPng, png256]));
console.log('CMD Studio : icône 256 px créée : ' + output);
