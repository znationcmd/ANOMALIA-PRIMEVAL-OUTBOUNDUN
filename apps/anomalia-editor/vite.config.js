import { defineConfig } from 'vite';
export default defineConfig({
  base:'./',
  build:{ outDir:'dist',emptyOutDir:true,target:'es2022',assetsInlineLimit:0 },
  server:{strictPort:true,port:4174}
});
