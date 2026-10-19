import {defineConfig} from "vite";
// Relative assets allow the game to run offline from Windows installer files.
export default defineConfig({base:"./",build:{outDir:"dist",assetsDir:"assets"}});
