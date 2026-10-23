'use strict';
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const {PUBLIC_KEY,validateFeedUrl}=require('../update-policy.cjs');
const url=validateFeedUrl(process.env.CMD_STUDIO_PRIVATE_FEED_URL||'');
const secret=process.env.ELECTRON_BUILDER_UPDATE_SIGN_KEY||'';
if(!secret)throw Error('Clé Ed25519 de publication absente. Publication bloquée.');
const privateKey=crypto.createPrivateKey(secret);
const publicKey=crypto.createPublicKey(privateKey).export({format:'pem',type:'spki'}).toString().trim();
if(publicKey!==PUBLIC_KEY.trim())throw Error('La clé de publication ne correspond PAS à la clé publique intégrée à CMD Studio. Publication bloquée.');
const pkg=require('../package.json');
const config={
 ...pkg.build,
 // Sans certificat Authenticode commercial, la confiance repose sur le manifeste
 // Ed25519 signé, validé AVANT téléchargement, puis SHA-512 de l'installateur.
 win:{...pkg.build.win,verifyUpdateCodeSignature:false},
 publish:[{provider:'generic',url}],
 updateManifest:{publicKey:PUBLIC_KEY}
};
const out=path.join(__dirname,'..','private-release.config.json');
fs.writeFileSync(out,JSON.stringify(config,null,2));
console.log('Publication privée autorisée : clé cryptographique confirmée, manifestes signés, cible '+new URL(url).host);
