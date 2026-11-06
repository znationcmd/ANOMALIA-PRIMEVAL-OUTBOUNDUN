import {BUNKER_FREQUENCY,broadcast,canHearBroadcast,decodeBroadcast,unlockRadioBunker,RADIO_BUNKERS,ACCESS_ITEMS,radioTime} from './bunker-radio.js';

// Génération de bips originale au navigateur : pas de flux audio tiers ni de code fixe.
function morsePlayer() {
  let ctx=null;
  let bus=null;
  const tones=[];
  async function play(morse,speed=2){
    stop();
    const AC=globalThis.AudioContext||globalThis.webkitAudioContext;
    if(!AC)throw new Error('Audio indisponible dans ce navigateur.');
    ctx=new AC();
    if(ctx.state==='suspended')await ctx.resume();
    bus=ctx.createGain();bus.gain.value=.09;bus.connect(ctx.destination);
    let offset=.1;
    const unit=.5/Math.max(.5,Math.min(3,Number(speed)||2));
    for(const code of String(morse).split(' ')){
      if(!code){offset+=unit*6;continue;}
      for(const mark of code){
        if(mark!=='.'&&mark!=='-')continue;
        const duration=mark==='-'?3*unit:unit;
        const oscillator=ctx.createOscillator();
        oscillator.type='sine';oscillator.frequency.value=700;
        oscillator.connect(bus);
        oscillator.start(ctx.currentTime+offset);
        oscillator.stop(ctx.currentTime+offset+duration);
        tones.push(oscillator);
        offset+=duration+unit;
      }
      offset+=2*unit;
    }
  }
  function stop(){
    for(const tone of tones.splice(0))try{tone.stop()}catch{}
    if(bus){try{bus.disconnect()}catch{}bus=null;}
    if(ctx){ctx.close().catch(()=>{});ctx=null;}
  }
  return {play,stop};
}

function element(tag,attributes={},text=''){
  const node=document.createElement(tag);
  for(const [key,value] of Object.entries(attributes)){
    if(key==='className')node.className=value;
    else if(key==='type'||key==='placeholder'||key==='maxLength'||key==='inputMode'||key==='value')node[key]=value;
    else if(key==='disabled')node.disabled=Boolean(value);
    else if(key==='htmlFor')node.htmlFor=value;
    else node.setAttribute(key,value);
  }
  if(text)node.textContent=text;
  return node;
}
function block(body,label,description){
  const section=element('section',{className:'anomalia-radio-block'});
  section.append(element('h3',{},label),element('p',{},description));
  body.append(section);
  return section;
}

export function openRadioConsole({state,panelBody,panelTitle,openPanel,notice}) {
  const player=morsePlayer();
  panelBody.replaceChildren();
  panelTitle.textContent='ANOMALIA’Z · RADIO MORSE';
  const heading=block(panelBody,'📻 Relais radio — 80,0 MHz',
    'La radio reçoit des transmissions nocturnes. Il faut une batterie et une radio trouvées en exploration, être à portée d’une antenne et régler la bonne fréquence.');
  const config=element('div',{className:'anomalia-radio-controls'});
  const freq=element('input',{type:'number',inputMode:'decimal',value:String(state.radioFrequency??BUNKER_FREQUENCY)});
  freq.min='80';freq.max='90';freq.step='0.1';
  const label=element('label',{},'Fréquence MHz ');label.append(freq);
  config.append(label);
  const tune=element('button',{type:'button'},'Régler la radio');
  tune.onclick=()=>{const n=Number(freq.value);if(!Number.isFinite(n)||n<80||n>90){notice('Fréquence invalide.');return;}state.radioFrequency=n;render();};
  config.append(tune);
  const status=element('p',{className:'anomalia-radio-status'});
  const frequency=element('pre',{className:'anomalia-radio-morse'});
  const decipher=element('input',{type:'text',placeholder:'Colle ici le Morse entendu, séparé par des espaces'});
  const decodeBtn=element('button',{type:'button'},'Décoder une transmission');
  const decoded=element('p',{className:'anomalia-radio-status'});
  const read=element('button',{type:'button'},'▶ Écouter le signal (audio réel du jeu)');
  const stop=element('button',{type:'button'},'■ Arrêter les bips');
  const result=element('div',{className:'anomalia-radio-block'});
  result.append(element('h3',{},'Signal capté'),status,frequency,read,stop,decipher,decodeBtn,decoded);
  heading.append(config,result);
  function render(){
    const tuned=canHearBroadcast(state,state.position);
    const transmission=tuned?broadcast(state):null;
    const time=radioTime(state.elapsed);
    status.textContent=!tuned?'Aucun signal : radio + batterie requises, fréquence 80,0 MHz et proximité d’une antenne.'
      :!transmission?'Radio opérationnelle, mais aucune émission : attends la nuit en jeu (17h45 – 06h00).'
      :'Signal Morse reçu à '+time.hour.toFixed(1)+' h (heure du jeu). Reconstitue 6 chiffres de position et 4 de cadenas.';
    frequency.textContent=transmission?.morse||'—';
    read.disabled=!transmission;
    decodeBtn.disabled=!transmission;
  }
  read.onclick=async()=>{
    const payload=canHearBroadcast(state,state.position)?broadcast(state):null;
    if(!payload){render();return;}
    try{await player.play(payload.morse,2);}catch(error){notice(error.message);}
  };
  stop.onclick=()=>player.stop();
  decodeBtn.onclick=()=>{
    try{
      if(!canHearBroadcast(state,state.position)||!broadcast(state))throw new Error('Aucune émission accessible.');
      const signal=decodeBroadcast(decipher.value);
      const available=RADIO_BUNKERS.find(b=>b.id===signal.bunker?.id);
      decoded.textContent=available?'Position '+signal.grid.slice(0,3)+' '+signal.grid.slice(3)+' — code '+signal.code+' — '+available.label
        :'Code décodé, mais cette position ne correspond pas à un bunker.';
    }catch(error){decoded.textContent=error.message;}
  };
  render();
  openPanel();
  // Fermeture clavier/menu ou panneau : neutralise les oscillateurs restants.
  const close=()=>player.stop();
  document.getElementById('panelClose')?.addEventListener('click',close,{once:true});
  return player;
}

export function openBunkerLock({state,site,panelBody,panelTitle,openPanel,closePanel,notice,save,onUnlocked}){
  panelBody.replaceChildren();
  panelTitle.textContent='ANOMALIA’Z · SAS SÉCURISÉ';
  const area=block(panelBody,'🔐 '+site.label,
    site.buildingLabel+' · Serrure à code radio. Capte la transmission Morse la nuit et entre les quatre chiffres correspondant à cette porte.');
  area.append(element('p',{},'Grille : '+site.grid.slice(0,3)+' '+site.grid.slice(3)));
  const input=element('input',{type:'text',inputMode:'numeric',maxLength:4,placeholder:'Code à quatre chiffres'});
  input.autocomplete='off';
  const status=element('p',{className:'anomalia-radio-status'});
  const submit=element('button',{type:'button'},'Déverrouiller le sas');
  const exit=element('button',{type:'button'},'Annuler');
  submit.onclick=()=>{
    const attempt=String(input.value||'').replace(/\s/g,'');
    const result=unlockRadioBunker(state,site.id,attempt);
    status.textContent=result.message;
    if(result.ok){save();closePanel();onUnlocked();}
  };
  exit.onclick=closePanel;
  input.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();submit.click();}};
  area.append(input,submit,exit,status);
  openPanel();input.focus();
}
