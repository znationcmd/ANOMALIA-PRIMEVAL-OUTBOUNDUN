import * as THREE from 'three';

// Terrain rendered from a real user-supplied heightmap. This is a Three.js
// preview sector; .umap World Partition itself must be viewed with Unreal 5.
export function createTerrainWorld({ground,grid,scene,camera,orbit,notify}){
  const defaults={width:1200,relief:150};
  let descriptor=null;
  const originalGeometry=ground.geometry;
  const originalMaterial=ground.material;
  async function bitmap(blob){
    if(typeof createImageBitmap==='function')return createImageBitmap(blob);
    return new Promise((resolve,reject)=>{
      const url=URL.createObjectURL(blob);
      const image=new Image();
      image.onload=()=>{URL.revokeObjectURL(url);resolve(image);};
      image.onerror=()=>{URL.revokeObjectURL(url);reject(Error('Impossible de lire cette heightmap.'));};
      image.src=url;
    });
  }
  async function load(blob,opts={}){
    if(!(blob instanceof Blob))throw Error('Sélectionne une image PNG, JPEG ou WebP.');
    if(blob.size>32*1024*1024)throw Error('Heightmap trop volumineuse (32 Mo maximum).');
    const image=await bitmap(blob);
    try{
      const size=Math.max(image.width||0,image.height||0);
      if(size<16||size>8192)throw Error('Heightmap invalide : image de 16 à 8192 pixels attendue.');
      const width=Number(opts.width??defaults.width),relief=Number(opts.relief??defaults.relief);
      if(!Number.isFinite(width)||width<128||width>48000||!Number.isFinite(relief)||relief<0||relief>3000)
        throw Error('Dimensions du relief incorrectes.');
      const canvas=document.createElement('canvas');
      // Resample a user source image at a bounded mesh resolution for iPhone/PC.
      const segments=Math.min(256,Math.max(64,Math.ceil(size/8)));
      const cells=segments+1;canvas.width=canvas.height=cells;
      const ctx=canvas.getContext('2d',{willReadFrequently:true});
      if(!ctx)throw Error('Décodage terrain non disponible sur cet appareil.');
      ctx.drawImage(image,0,0,cells,cells);
      const data=ctx.getImageData(0,0,cells,cells).data;
      const geometry=new THREE.PlaneGeometry(width,width,segments,segments);
      const pos=geometry.getAttribute('position');
      const colors=new Float32Array(pos.count*3);
      // Earth-tone albedo from actual elevation and slope, not a fake satellite photo.
      const beach=new THREE.Color('#918876'),grass=new THREE.Color('#577b4f');
      const high=new THREE.Color('#85877f'),rock=new THREE.Color('#9f9586');
      const col=new THREE.Color();
      const heights=new Float32Array(pos.count);
      for(let i=0;i<pos.count;i++){
        const row=Math.floor(i/cells),column=i%cells,idx=(row*cells+column)*4;
        const gray=(data[idx]*.2126+data[idx+1]*.7152+data[idx+2]*.0722)/255;
        heights[i]=(gray-.25)*relief;
        pos.setZ(i,heights[i]);
      }
      geometry.computeVertexNormals();
      const normals=geometry.getAttribute('normal');
      for(let i=0;i<pos.count;i++){
        const alt=heights[i],steep=Math.abs(normals.getZ(i));
        if(alt<0)col.copy(beach).lerp(grass,Math.min(1,Math.max(0,(alt+20)/25)));
        else if(alt<relief*.57)col.copy(grass).lerp(high,Math.min(1,alt/(relief*.75||1))*.37);
        else col.copy(high).lerp(rock,Math.min(1,(alt-relief*.57)/(relief*.4||1)));
        col.lerp(rock,Math.min(.7,(1-steep)*2.2));
        colors[i*3]=col.r;colors[i*3+1]=col.g;colors[i*3+2]=col.b;
      }
      geometry.setAttribute('color',new THREE.BufferAttribute(colors,3));
      const material=new THREE.MeshStandardMaterial({vertexColors:true,roughness:1,metalness:0,flatShading:false});
      const previous=ground.geometry,oldMat=ground.material;
      ground.geometry=geometry;ground.material=material;ground.position.y=0;
      ground.receiveShadow=true;ground.visible=true;
      if(previous!==originalGeometry)previous.dispose();
      if(oldMat!==originalMaterial)oldMat.dispose();
      grid.visible=false;
      camera.far=Math.max(2400,width*2.4);camera.updateProjectionMatrix();
      orbit.maxDistance=Math.max(350,width);
      const center=heights[Math.floor(pos.count/2)]||0;
      orbit.target.set(0,center,0);
      camera.position.set(width*.13,center+width*.075,width*.19);orbit.update();
      descriptor={name:String(opts.name||'Heightmap locale').slice(0,100),width,relief,vertices:pos.count,
        type:'source-heightmap-preview',updatedAt:new Date().toISOString()};
      return {...descriptor};
    }finally{image.close?.();}
  }
  function clear(){
    if(ground.geometry!==originalGeometry)ground.geometry.dispose();
    if(ground.material!==originalMaterial)ground.material.dispose();
    ground.geometry=originalGeometry;ground.material=originalMaterial;
    ground.position.y=-.07;
    grid.visible=true;descriptor=null;
    camera.far=1600;camera.updateProjectionMatrix();
  }
  return {load,clear,status:()=>descriptor,hasTerrain:()=>Boolean(descriptor)};
}
