/**
 * Package ANOMALIA’Z PRIGIMALIA as one playable offline browser file.
 * The compiled JS and CSS are embedded, so users can double-click the file.
 * No internet service, developer tooling or external assets are required at runtime.
 */
import {readFile,writeFile,mkdir} from "node:fs/promises";
import {dirname,join} from "node:path";
const root=process.cwd(),dist=join(root,"dist");
let html=await readFile(join(dist,"index.html"),"utf8");
const jsTag=html.match(/<script\b[^>]*type="module"[^>]*src="([^"]+)"[^>]*><\/script>/i);
const cssTag=html.match(/<link\b[^>]*rel="stylesheet"[^>]*href="([^"]+)"[^>]*>/i);
if(!jsTag||!cssTag)throw new Error("Cannot locate generated JavaScript or CSS assets in dist/index.html");
const resolveAsset=uri=>join(dist,uri.replace(/^\//,"").replace(/^\.\//,""));
const js=await readFile(resolveAsset(jsTag[1]),"utf8");
const css=await readFile(resolveAsset(cssTag[1]),"utf8");
if(!js.includes("THREE")&&!js.includes("WebGL"))console.warn("3D bundle fingerprint not recognized; verify rendering in a real browser.");
html=html.replace(jsTag[0],()=>'<script type="module">'+js.replace(/<\/script/gi,'<\\/script')+'</script>');
html=html.replace(cssTag[0],()=>'<style>'+css.replace(/<\/style/gi,'<\\/style')+'</style>');
html=html.replace(/<link\b[^>]*rel="modulepreload"[^>]*>/gi,"");
if(/<script\b[^>]*src=|<link\b[^>]*rel="stylesheet"/i.test(html))throw new Error("Package still includes external JS or stylesheet references");
const output=join(root,"release","ANOMALIAZ_PRIGIMALIA.html");
await mkdir(dirname(output),{recursive:true});
await writeFile(output,html);
const instructions=`ANOMALIA’Z PRIGIMALIA - VERSION PRE-ALPHA WINDOWS / MAC / LINUX

POUR JOUER :
1. Décompresse le fichier ZIP.
2. Double-clique sur ANOMALIAZ_PRIGIMALIA.html.
3. Ouvre avec Chrome, Edge ou Firefox récent compatible WebGL2.
4. Choisis Jouer en solo, ou Multijoueur pour rejoindre un serveur.
5. ZQSD/WASD : déplacements; souris : regarder; clic gauche : tirer; I : inventaire; M : carte.
6. Les manettes Xbox et PlayStation standard sont prises en charge si le navigateur les reconnaît.

Ce fichier HTML contient le jeu compilé. Aucun npm, Node.js ni outil de programmation n'est nécessaire pour jouer.
Ta sauvegarde reste locale à ce navigateur et à ce fichier. Une mise à jour peut changer son identité de stockage.
Si ton navigateur refuse d'ouvrir un module depuis file://, essaie un autre navigateur ou lance avec un serveur local.

IMPORTANT : prototype PRE-ALPHA, graphismes procéduraux.
Multijoueur expérimental : présence et déplacement des survivants uniquement.
Loot, inventaires, IA, véhicules et événements restent locaux. Pas encore de PvP synchronisé.
Ce fichier HTML est la version navigateur ; un installateur Windows distinct est proposé dans GitHub Actions.
Menu traduit en huit langues, interfaces historiques en français.
Éditeur : F4, code ANOMALIA-EDITOR-2026.
Les animations, les physiques et les performances varient selon le navigateur et l'appareil.
`;
await writeFile(join(root,"release","LIRE_AVANT_DE_JOUER.txt"),instructions);
console.log(JSON.stringify({standalone:"release/ANOMALIAZ_PRIGIMALIA.html",bytes:Buffer.byteLength(html),embeddedJS:Buffer.byteLength(js),embeddedCSS:Buffer.byteLength(css)}));
