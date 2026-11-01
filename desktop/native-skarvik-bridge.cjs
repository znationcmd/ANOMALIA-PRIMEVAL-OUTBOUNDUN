"use strict";
/**
 * Bridge for the ACTUAL UE5.8 SKARVIK final World Partition staging world.
 * This does not download/cook a game, convert UE assets into Three.js or mark
 * the map playable. Only launches the installed Epic Unreal Editor on a known
 * isolated local project when the existing 7-island map and stage marker match.
 * No renderer-controlled path, executable or arguments are accepted.
 */
const fs = require("node:fs");
const path = require("node:path");
const { spawn } = require("node:child_process");

const WORLD = "/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1";
const STAGE_TOKEN = "41188816555";
const STAGE_ROOT = "C:\\ANOMALIAZ_SKARVIK_STAGE_" + STAGE_TOKEN + "\\unreal";
const EDITOR_REL = path.join("Engine", "Binaries", "Win64", "UnrealEditor.exe");
const MAP_REL = path.join("Content", "Maps", "PRIGIMALIA_SKARVIK_FINAL_v1.umap");
const PROJECT_NAME = "AnomaliaZPrigimalia.uproject";

function getNativePreviewStatus(options = {}) {
  const exists = options.existsSync || fs.existsSync;
  const read = options.readFileSync || fs.readFileSync;
  const env = options.env || process.env;
  const platform = options.platform || process.platform;
  const root = options.stageRoot || STAGE_ROOT;
  const base = {
    available: false,
    mode: "unreal-editor-preview",
    world: WORLD,
    state: "not-ready",
    message: "Prévisualisation Unreal 5.8 uniquement : la version native Windows du jeu n’est pas encore publiée."
  };
  if (platform !== "win32") {
    return { ...base, state: "windows-required", message: "Ouverture d’Unreal Editor disponible uniquement sur Windows." };
  }
  const marker = path.join(root, ".skarvik-ci-stage-marker");
  const project = path.join(root, PROJECT_NAME);
  const map = path.join(root, MAP_REL);
  try {
    if (!exists(marker) || String(read(marker, "utf8")).replace(/^\uFEFF/, "").trim() !== STAGE_TOKEN) {
      return { ...base, state: "stage-not-verified", message: "La copie de travail SKARVIK vérifiée sur C: est introuvable ; la version Windows actuelle reste le prototype." };
    }
    if (!exists(project) || !exists(map)) {
      return { ...base, state: "map-not-present", message: "Projet Unreal ou carte finale SKARVIK absente de la copie de travail C:." };
    }
    const engineRoots = [
      env.UE_ROOT,
      "C:\\Program Files\\Epic Games\\UE_5.8",
      "C:\\Program Files\\Epic Games\\UE_5.8.3",
      "D:\\Epic Games\\UE_5.8",
      "D:\\Epic Games\\UE_5.8.3"
    ].filter(Boolean);
    const editor = engineRoots.map(prefix => path.join(prefix, EDITOR_REL)).find(exists);
    if (!editor) {
      return { ...base, state: "editor-not-found", message: "SKARVIK est détectée, mais Unreal Editor 5.8 est introuvable sur ce PC." };
    }
    return {
      ...base,
      available: true,
      state: "editor-preview-ready",
      message: "La vraie carte SKARVIK FINAL (7 îles) est disponible dans la copie Unreal locale. Aperçu dans Unreal Editor, pas encore dans le jeu installé.",
      // Paths stay in the privileged main process. Renderer sees only status.
      _editorPath: editor,
      _projectPath: project
    };
  } catch {
    return { ...base, state: "stage-read-failed", message: "Impossible de vérifier les fichiers Unreal de SKARVIK sur ce PC." };
  }
}

function publicPreviewStatus(status) {
  const { _editorPath, _projectPath, ...safe } = status;
  return safe;
}

async function launchNativePreview(options = {}) {
  const state = getNativePreviewStatus(options);
  if (!state.available) return { started: false, ...publicPreviewStatus(state) };
  const spawnEditor = options.spawn || spawn;
  try {
    await new Promise((resolve, reject) => {
      const child = spawnEditor(state._editorPath, [state._projectPath, WORLD, "-log"], {
        detached: true,
        stdio: "ignore",
        windowsHide: false,
        shell: false
      });
      child.once("error", reject);
      child.once("spawn", () => { child.unref(); resolve(); });
    });
    return {
      started: true,
      state: "editor-launched",
      mode: state.mode,
      world: WORLD,
      message: "Ouverture demandée dans Unreal Editor. Cela ne prouve pas encore que la carte est jouable."
    };
  } catch {
    return {
      started: false,
      state: "launch-failed",
      mode: state.mode,
      message: "Unreal Editor n’a pas pu démarrer. Vérifie l’installation UE 5.8."
    };
  }
}
module.exports = { WORLD, STAGE_TOKEN, STAGE_ROOT, getNativePreviewStatus, publicPreviewStatus, launchNativePreview };
