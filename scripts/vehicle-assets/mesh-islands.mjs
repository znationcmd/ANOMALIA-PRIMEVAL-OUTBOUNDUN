/** Triangle islands welded by position, including duplicated vertices at UV seams. */
export function triangleIslands(positions,indices,tolerance=1e-5){
 const count=positions.length/3;
 if(!Number.isInteger(count)||indices.length%3||!Number.isFinite(tolerance)||tolerance<=0)throw Error('Invalid triangle topology');
 const parent=Array.from({length:count},(_,i)=>i),welded=new Map;
 const find=i=>{while(parent[i]!==i){parent[i]=parent[parent[i]];i=parent[i];}return i;};
 const join=(a,b)=>{parent[find(a)]=find(b);};
 for(let i=0;i<count;i++){
  const p=Array.from(positions.slice(i*3,i*3+3));if(!p.every(Number.isFinite))throw Error('Non-finite mesh position');
  const key=p.map(v=>Math.round(v/tolerance)).join(',');
  if(welded.has(key))join(i,welded.get(key));else welded.set(key,i);
 }
 for(let i=0;i<indices.length;i+=3){
  for(let k=0;k<3;k++)if(!Number.isInteger(indices[i+k])||indices[i+k]<0||indices[i+k]>=count)throw Error('Mesh index outside accessor');
  join(indices[i],indices[i+1]);join(indices[i],indices[i+2]);
 }
 const result=new Map;
 for(let i=0;i<indices.length;i+=3){
  const key=find(indices[i]);let group=result.get(key);
  if(!group)result.set(key,group={triangleOffsets:[],min:[Infinity,Infinity,Infinity],max:[-Infinity,-Infinity,-Infinity]});
  group.triangleOffsets.push(i);
  for(let k=0;k<3;k++)for(let c=0;c<3;c++){
   const v=positions[indices[i+k]*3+c];group.min[c]=Math.min(group.min[c],v);group.max[c]=Math.max(group.max[c],v);
  }
 }
 return [...result.values()];
}
