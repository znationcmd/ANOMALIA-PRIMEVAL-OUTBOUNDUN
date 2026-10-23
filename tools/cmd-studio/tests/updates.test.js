'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const crypto=require('node:crypto');
const {PUBLIC_KEY,INTERVAL_MS,validateFeedUrl,redactError,writeJsonAtomic,readPrivateSettings}=require('../update-policy.cjs');
test('metadonnees signees : cle publique Ed25519 embarquee',()=>{
  const key=crypto.createPublicKey(PUBLIC_KEY);
  assert.equal(key.asymmetricKeyType,'ed25519');
  assert.equal(INTERVAL_MS,6*3600000);
});
test('accepte seulement les URL HTTPS privees sans identifiants',()=>{
  assert.equal(validateFeedUrl('https://updates.example.fr/cmd-studio'),'https://updates.example.fr/cmd-studio/');
  for(const bad of ['http://updates.example.fr/','https://user:pass@updates.example.fr/',
    'https://example.fr/path?token=123','https://github.com/owner/releases/',
    'https://localhost/','file:///etc/passwd','https://example.fr/path#secret']){
    assert.throws(()=>validateFeedUrl(bad));
  }
});
test('preferences locales stockees sans exposer la cle en clair',t=>{
  const folder=fs.mkdtempSync(path.join(os.tmpdir(),'cmd-studio-updates-'));
  t.after(()=>fs.rmSync(folder,{force:true,recursive:true}));
  const file=path.join(folder,'updates.json');
  writeJsonAtomic(file,{url:'https://updates.example.fr/studio/',enabled:true,tokenEncrypted:'cipher-data-not-plain'});
  const settings=readPrivateSettings(file);
  assert.equal(settings.enabled,true);
  assert.equal(settings.tokenEncrypted,'cipher-data-not-plain');
  assert.equal(settings.url,'https://updates.example.fr/studio/');
});
test('les erreurs masquent les secrets',()=>{
  assert.doesNotMatch(redactError('Authorization=SECRET token=pass Bearer PRIVATE'),/SECRET|pass|PRIVATE/);
  assert.ok(redactError('E'.repeat(1000)).length<=300);
});
