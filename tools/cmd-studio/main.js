'use strict';
const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const path = require('node:path');
const { Studio } = require('./core');
const { PrivateAutoUpdates } = require('./updates.cjs');

let studio;
let window;
let privateUpdates;
if (process.platform === 'win32') app.setAppUserModelId('fr.cmd.studio');
const ACTIONS = new Set([
  'status', 'settings', 'configure', 'assets', 'import', 'search',
  'downloadPolyHaven', 'convertBlender', 'importUnreal', 'openTool',
  'openAsset', 'previewAsset', 'projects', 'addProject', 'selectProject'
]);

function createWindow() {
  window = new BrowserWindow({
    width: 1440, height: 900, minWidth: 980, minHeight: 630,
    backgroundColor: '#0c0b18',
    title: 'CMD Studio — Game Creator',
    icon: path.join(__dirname, 'resources', 'cmd-studio-256.ico'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true
    }
  });
  window.setMenuBarVisibility(false);
  window.loadFile(path.join(__dirname, 'ui', 'index.html'));
  window.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
  window.webContents.on('will-navigate', (event) => event.preventDefault());
}

app.whenReady().then(() => {
  studio = new Studio(app.getPath('userData'), path.join(__dirname, 'scripts'));
  privateUpdates = new PrivateAutoUpdates();
  ipcMain.handle('studio:updates:status',()=>privateUpdates.status());
  ipcMain.handle('studio:updates:configure',(_event,options)=>privateUpdates.configure(options));
  ipcMain.handle('studio:updates:check',()=>privateUpdates.check());
  ipcMain.handle('studio:updates:install',()=>privateUpdates.installNow());
  ipcMain.handle('studio:call', async (_event, action, payload = {}) => {
    if (!ACTIONS.has(action)) throw new Error('Action non autorisée.');
    return await studio[action](payload);
  });
  ipcMain.handle('studio:pick', async (_event, kind) => {
    const configs = {
      asset: { properties: ['openFile', 'multiSelections'], filters: [{ name: 'Ressources 3D', extensions: ['glb','gltf','fbx','obj','blend','usd','usdz','png','jpg','jpeg','tga','exr','hdr'] }] },
      blender: { properties: ['openFile'] },
      unreal: { properties: ['openFile'] },
      project: { properties: ['openFile'], filters: [{ name: 'Unreal', extensions: ['uproject'] }] }
    };
    if (!Object.hasOwn(configs, kind)) throw new Error('Sélection interdite.');
    const result = await dialog.showOpenDialog(window, configs[kind]);
    return result.canceled ? [] : result.filePaths;
  });
  ipcMain.handle('studio:openExternal', async (_event, url) => {
    const valid = /^https:\/\/(sketchfab\.com|www\.sketchfab\.com|polyhaven\.com|www\.polyhaven\.com|fab\.com|www\.fab\.com|www\.blender\.org|dev\.epicgames\.com)(\/|$)/i.test(String(url));
    if (!valid) throw new Error('Lien externe non autorisé.');
    await shell.openExternal(url);
  });
  createWindow();
  privateUpdates.activate();
  app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
});
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });

app.on('before-quit',()=>privateUpdates?.shutdown());
