// Décor visuel original du lanceur : ne remplace jamais une vraie carte Unreal.
// La carte choisie se charge dans la vue 3D (JSON), ou s'ouvre dans UE5 (.umap).
// Canvas sans requête distante, sans utilisation de captures/ressources DayZ.
export function createLandscapeBackdrop(container){
 const canvas=document.createElement('canvas');
 canvas.className='mapLandscape';
 canvas.setAttribute('aria-hidden','true');
 container.prepend(canvas);
 let raf=0;
 function draw(){
  const width=Math.max(680,Math.min(1800,Math.round(innerWidth)));
  const height=Math.max(420,Math.min(980,Math.round(innerHeight)));
  canvas.width=width;canvas.height=height;
  const ctx=canvas.getContext('2d',{alpha:false});
  if(!ctx)return;
  let seed=10427;
  const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
  const W=width,H=height;
  // Lumière d'après-midi, nuages diffus.
  const sky=ctx.createLinearGradient(0,0,0,H*.64);
  sky.addColorStop(0,'#4b8bc9');sky.addColorStop(.54,'#9ec6e2');sky.addColorStop(1,'#d0dcd4');
  ctx.fillStyle=sky;ctx.fillRect(0,0,W,H);
  for(let i=0;i<29;i++){
   const x=random()*W,y=random()*H*.38,r=(.035+random()*.11)*W;
   const cloud=ctx.createRadialGradient(x,y,1,x,y,r);
   cloud.addColorStop(0,'#ffffff4d');cloud.addColorStop(.4,'#f5f7ef25');cloud.addColorStop(1,'#f5f7ef00');
   ctx.fillStyle=cloud;ctx.beginPath();ctx.ellipse(x,y,r,r*.20,-.13,0,Math.PI*2);ctx.fill();
  }
  // Collines douces et vallées : le plan de perspective donne de la profondeur.
  const horizon=H*.48;
  for(let layer=0;layer<5;layer++){
   const level=horizon+layer*H*.053;
   ctx.beginPath();ctx.moveTo(0,H);
   for(let x=0;x<=W+12;x+=12){
    const wave=Math.sin(x*.005+layer*.72)*H*.018+
      Math.sin(x*.015+layer*1.25)*H*.01+Math.sin(x*.028+layer*.9)*H*.005;
    ctx.lineTo(x,level+wave);
   }
   ctx.lineTo(W,H);ctx.closePath();
   const gradient=ctx.createLinearGradient(0,level-H*.04,0,H);
   const colors=[['#81999a','#7a9476'],['#8ba392','#6f896e'],['#9cae90','#6d8662'],['#8aa073','#65815a'],['#819263','#536f48']][layer];
   gradient.addColorStop(0,colors[0]);gradient.addColorStop(1,colors[1]);
   ctx.fillStyle=gradient;ctx.fill();
  }
  // Ligne de bocage au loin : feuillus de tailles variées et ombres atmosphériques.
  function tree(x,y,scale,far=false){
    const trunk=scale*(far?0.9:1.5);
    ctx.fillStyle=far?'#576a58':'#3a4939';
    ctx.fillRect(x-trunk*.19,y-scale*.95,trunk*.4,scale*1.15);
    const canopy=ctx.createRadialGradient(x-scale*.16,y-scale*1.7,scale*.08,x,y-scale*1.6,scale*1.17);
    canopy.addColorStop(0,far?'#607e67':'#426747');
    canopy.addColorStop(.67,far?'#58755d':'#345c36');
    canopy.addColorStop(1,'#233f2d');
    ctx.fillStyle=canopy;
    for(let k=0;k<7;k++){
      const theta=(k/7)*Math.PI*2;
      const dx=Math.cos(theta)*scale*.39,dy=Math.sin(theta)*scale*.22;
      ctx.beginPath();ctx.ellipse(x+dx,y-scale*1.75+dy,scale*(.55+random()*.25),scale*(.53+random()*.20),-.12,0,Math.PI*2);ctx.fill();
    }
    // Feuilles éclairées, non sphères géométriques en jeu.
    for(let k=0;k<(far?15:40);k++){
      const dx=(random()-.5)*scale*1.8,dy=(random()-.5)*scale*.95;
      if(dx*dx/(scale*scale*1.2)+dy*dy/(scale*scale*.65)>1)continue;
      ctx.fillStyle=random()>.5?'#c2ca8c52':'#9bb76d66';
      ctx.fillRect(x+dx,y-scale*1.75+dy,Math.max(.6,scale*.07),Math.max(.5,scale*.04));
    }
  }
  for(let i=0;i<280;i++){
    const x=random()*W;
    const y=horizon+H*.012+random()*H*.095;
    const scale=(3+random()*8)*(1+(y-horizon)/H);
    tree(x,y,scale,true);
  }
  // Champ d'herbes dense. Variations locales, lumière et brins, sans modèle 3D simulé.
  for(let i=0;i<18500;i++){
    const x=random()*W;
    const v=random();
    const y=horizon+H*.15+Math.pow(v,.72)*H*.39;
    const z=(y-(horizon+H*.15))/(H*.39);
    const length=1.4+z*(6+random()*13);
    const gray=42+Math.round(random()*45);
    ctx.strokeStyle=random()<.22?'rgba(188,184,116,.23)':`rgba(${gray+47},${gray+71},${gray+25},${(.11+z*.16).toFixed(2)})`;
    ctx.lineWidth=.3+z*.8;
    ctx.beginPath();ctx.moveTo(x,y);
    ctx.quadraticCurveTo(x+(random()-.5)*6,y-length*.52,x+(random()-.4)*11,y-length);
    ctx.stroke();
  }
  // Arbustes et arbres au premier plan, selon la profondeur.
  for(let i=0;i<38;i++){
    const x=random()*W,y=horizon+H*.1+random()*H*.20;
    tree(x,y,8+random()*18*(1+(y-horizon)/H),false);
  }
  // Lumière chaude et grain léger, pour éviter les aplats de démonstration.
  const warmth=ctx.createLinearGradient(W*.7,0,W*.2,H);
  warmth.addColorStop(0,'#f3e9ba13');warmth.addColorStop(.75,'#cabb7900');warmth.addColorStop(1,'#161c1519');
  ctx.fillStyle=warmth;ctx.fillRect(0,0,W,H);
  for(let i=0;i<7200;i++){
    const x=random()*W,y=random()*H,alpha=random()*.035;
    ctx.fillStyle=`rgba(240,246,210,${alpha})`;ctx.fillRect(x,y,1,1);
  }
 }
 function requestDraw(){cancelAnimationFrame(raf);raf=requestAnimationFrame(draw);}
 window.addEventListener('resize',requestDraw);
 requestDraw();
 return {element:canvas,redraw:requestDraw};
}
