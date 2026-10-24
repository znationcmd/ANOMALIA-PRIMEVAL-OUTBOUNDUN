import * as THREE from 'three';
// DayZ-inspired WORKFLOW (not a port/re-upload of DayZ Editor).
// Controls only mutate the current Three.js display, never user project files.
export function createWorldForge({camera,orbit,grid,renderer,ground,scene,openBrowser,togglePrototypes,notify}){
  const $=s=>document.querySelector(s);
  const find=id=>document.getElementById(id);
  const options={grid:true,shadows:true};
  const keys=new Set();
  const isEditable=el=>el?.closest?.('input,textarea,select,[contenteditable]')!==null;
  let flying=false;
  let menu=null,menuAnchor=null;
  function clickTarget(id){
    const control=find(id);
    if(!control||control.disabled||control.hidden){
      notify('Cette action n’est pas disponible sur cet appareil.',true);return;
    }
    control.click();
  }
  const groups={
    menuFile:[
      ['Nouvelle carte','Ctrl+N',()=>clickTarget('newScene')],
      ['Choisir une carte','',()=>clickTarget('openMapLibrary')],
      ['Ouvrir une scène JSON','Ctrl+O',()=>clickTarget('openScene')],
      ['Importer un modèle GLB','',()=>clickTarget('importModel')],
      ['Importer un pack ZIP','',()=>clickTarget('importGamePack')],
      ['Enregistrer','Ctrl+S',()=>clickTarget('saveScene')],
      ['Enregistrer sous…','',()=>clickTarget('saveAs')],
      ['Exporter ANOMALIA JSON','',()=>clickTarget('exportScene')],
      ['Exporter placements CSV','',()=>clickTarget('exportCSV')]
    ],
    menuEdit:[
      ['Annuler','Ctrl+Z',()=>clickTarget('undo')],
      ['Rétablir','Ctrl+Y',()=>clickTarget('redo')],
      ['Sélectionner','Q',()=>clickTarget('selectTool')],
      ['Déplacer','W',()=>clickTarget('moveTool')],
      ['Rotation','E',()=>clickTarget('rotateTool')],
      ['Échelle','R',()=>clickTarget('scaleTool')],
      ['Dupliquer','Ctrl+D',()=>clickTarget('duplicate')],
      ['Supprimer la sélection','Suppr',()=>clickTarget('delete')]
    ],
    menuView:[
      ['Centrer sur le monde','',()=>clickTarget('centerWorld')],
      ['Vue de dessus','',()=>clickTarget('viewTop')],
      ['Grille de placement','',()=>clickTarget('toggleGrid')],
      ['Ombres dans la vue','',()=>clickTarget('toggleShadows')],
      ['Masquer/afficher les prototypes','',togglePrototypes],
      ['Vue immersive','',()=>clickTarget('ribbonFocus')],
      ['Voir les cartes','',()=>clickTarget('openMapLibrary')]
    ],
    menuAssets:[
      ['Afficher les objets disponibles','',openBrowser],
      ['Choisir la carte','',()=>clickTarget('openMapLibrary')],
      ['Ouvrir le projet Unreal','',()=>clickTarget('openWorldNow')],
      ['Relief : charger un PNG','',()=>clickTarget('chooseHeightmap')],
      ['Réglages du relief','',()=>find('worldSourceBar')?.classList.toggle('expanded')],
      ['Réglages des ressources','',()=>{const panel=find('librarySourceSettings');if(panel)panel.open=true;clickTarget('toggleInspector');}],
      ['Importer GLB','',()=>clickTarget('importModel')],
      ['Importer ZIP de modèles','',()=>clickTarget('importGamePack')],
      ['Lier le dossier du jeu','',()=>clickTarget('linkGameFolder')],
      ['Actualiser les modèles','',()=>clickTarget('refreshGameFolder')]
    ]
  };
  const popup=document.createElement('div');
  popup.className='menuPopup';
  popup.hidden=true;
  popup.setAttribute('role','menu');
  popup.setAttribute('aria-label','Actions du menu');
  document.body.append(popup);
  function closeMenu(){
    popup.hidden=true;popup.replaceChildren();menu=null;
    if(menuAnchor)menuAnchor.setAttribute('aria-expanded','false');
    menuAnchor=null;
  }
  function openMenu(id){
    if(menu===id){closeMenu();return;}
    closeMenu();
    const anchor=find(id);
    if(!anchor)return;
    menu=id;menuAnchor=anchor;
    anchor.setAttribute('aria-expanded','true');
    popup.replaceChildren();
    for(const [label,shortcut,execute] of groups[id]){
      const button=document.createElement('button');
      button.type='button';button.setAttribute('role','menuitem');
      const text=document.createElement('span');text.textContent=label;button.append(text);
      if(shortcut){const key=document.createElement('kbd');key.textContent=shortcut;button.append(key);}
      button.addEventListener('click',()=>{closeMenu();execute();});
      popup.append(button);
    }
    const rect=anchor.getBoundingClientRect();
    const width=254;
    popup.style.width=width+'px';
    popup.style.maxHeight=Math.max(130,innerHeight-76)+'px';
    popup.style.overflowY='auto';
    popup.style.top=Math.max(4,Math.min(rect.bottom+3,innerHeight-12-Math.min(popup.children.length*34+14,innerHeight-76)))+'px';
    popup.style.left=Math.max(5,Math.min(rect.left,innerWidth-width-8))+'px';
    popup.hidden=false;
    popup.querySelector('button')?.focus();
  }
  for(const id of Object.keys(groups))find(id)?.addEventListener('click',()=>openMenu(id));
  document.addEventListener('pointerdown',e=>{
    if(!popup.hidden&&!popup.contains(e.target)&&!menuAnchor?.contains(e.target))closeMenu();
  });
  document.addEventListener('keydown',e=>{if(e.key==='Escape')closeMenu();});
  function setButton(id,on){
    const btn=find(id);if(!btn)return;
    btn.classList.toggle('on',on);
    btn.setAttribute('aria-pressed',String(on));
  }
  find('toggleGrid')?.addEventListener('click',()=>{
    options.grid=!options.grid;grid.visible=options.grid;setButton('toggleGrid',options.grid);
  });
  find('toggleShadows')?.addEventListener('click',()=>{
    options.shadows=!options.shadows;renderer.shadowMap.enabled=options.shadows;renderer.shadowMap.needsUpdate=true;
    setButton('toggleShadows',options.shadows);
  });
  find('centerWorld')?.addEventListener('click',()=>{
    orbit.target.set(0,0,0);camera.position.set(25,21,27);orbit.update();
  });
  find('viewTop')?.addEventListener('click',()=>{
    orbit.target.set(0,0,0);camera.position.set(.01,130,.01);camera.up.set(0,0,-1);orbit.update();
    camera.up.set(0,1,0);
  });
  const canvas=renderer.domElement;
  canvas.addEventListener('pointerdown',e=>{
    if(e.pointerType==='mouse'&&e.button===2){flying=true;keys.clear();}
  });
  window.addEventListener('pointerup',e=>{if(e.button===2){flying=false;keys.clear();}});
  canvas.addEventListener('contextmenu',e=>e.preventDefault());
  window.addEventListener('blur',()=>{flying=false;keys.clear();closeMenu();});
  document.addEventListener('keydown',e=>{
    if(!flying||isEditable(e.target))return;
    const key=e.key.toLowerCase();
    if(['w','s','a','d','q','e','shift','alt',' '].includes(key)){
      keys.add(key);e.preventDefault();e.stopImmediatePropagation();
    }
  },true);
  document.addEventListener('keyup',e=>keys.delete(e.key.toLowerCase()));
  let lastFps=performance.now(),frames=0,accum=0;
  const forward=new THREE.Vector3(),right=new THREE.Vector3(),motion=new THREE.Vector3();
  function tick(delta){
    if(flying&&keys.size){
      camera.getWorldDirection(forward);
      forward.y=0;forward.normalize();
      right.crossVectors(forward,new THREE.Vector3(0,1,0)).normalize();
      motion.set(0,0,0);
      if(keys.has('w'))motion.add(forward);
      if(keys.has('s'))motion.sub(forward);
      if(keys.has('a'))motion.sub(right);
      if(keys.has('d'))motion.add(right);
      if(keys.has('q'))motion.y+=1;
      if(keys.has('e'))motion.y-=1;
      if(motion.lengthSq()>0){
        const speed=keys.has('shift')?52:keys.has('alt')?2.5:13;
        motion.normalize().multiplyScalar(Math.min(delta,.075)*speed);
        camera.position.add(motion);orbit.target.add(motion);
      }
    }
    frames++;accum+=delta;
    if(accum>=1){
      const label=find('fps');if(label)label.textContent=Math.round(frames/accum)+' FPS';
      frames=0;accum=0;
    }
  }
  return {tick,isFlying:()=>flying,closeMenu};
}
