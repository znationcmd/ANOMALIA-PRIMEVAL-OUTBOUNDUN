import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
const read=(p)=>readFileSync(new URL(p,import.meta.url),"utf8");
test("Windows build creates a real NSIS installer, not only an HTML or ZIP package",()=>{
 const pkg=JSON.parse(read("../package.json"));
 assert.equal(pkg.main,"desktop/main.cjs");
 assert.ok(pkg.devDependencies.electron);
 assert.ok(pkg.devDependencies["electron-builder"]);
 assert.ok(pkg.scripts["package:windows"].includes("--win nsis"));
 assert.equal(pkg.build.win.target[0].target,"nsis");
 assert.ok(pkg.build.nsis.createDesktopShortcut);
 assert.ok(pkg.build.nsis.createStartMenuShortcut);
 assert.ok(pkg.build.nsis.allowToChangeInstallationDirectory);
 assert.ok(pkg.build.files.includes("dist/**/*"));
});
test("Windows Electron uses a secure offline game origin and refuses Node access from game scripts",()=>{
 const electron=read("../desktop/main.cjs");
 for(const required of [
  "protocol.registerSchemesAsPrivileged","secure:true","standard:true",
  'sandbox:true','contextIsolation:true','nodeIntegration:false',
  'webSecurity:true','setWindowOpenHandler','will-attach-webview',
  'protocol.handle(SCHEME','net.fetch','anomalia://game/index.html'
 ])assert.ok(electron.includes(required),"desktop runtime missing: "+required);
});
test("production WebGL asset URLs are relative for installed offline application",()=>{
 const vite=read("../vite.config.js");
 assert.ok(vite.includes('base:"./"'));
});
