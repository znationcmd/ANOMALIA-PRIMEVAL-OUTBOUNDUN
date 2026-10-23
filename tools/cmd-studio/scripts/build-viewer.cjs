'use strict';
const esbuild = require('esbuild');
const path = require('node:path');
esbuild.build({
  entryPoints: [path.join(__dirname,'..','ui','viewer.js')],
  outfile: path.join(__dirname,'..','ui','generated','viewer.bundle.js'),
  bundle: true,
  platform: 'browser',
  format: 'iife',
  target: ['chrome120'],
  minify: true,
  sourcemap: false,
  legalComments: 'none',
  logLevel: 'info',
  define: { 'process.env.NODE_ENV': '"production"' }
}).catch(error => { console.error(error); process.exitCode=1; });
