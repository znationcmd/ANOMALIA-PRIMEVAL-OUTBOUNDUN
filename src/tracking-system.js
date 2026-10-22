/** ANOMALIA: deterministic tracking clues; integrate with actor movement, combat and world rendering. */
export const TRACK_TYPES=Object.freeze(["footprint","blood"]);
export function createTrackingSystem({maxClues=2000}={}){
 const clues=[];
 const clamp=(v,min,max)=>Math.max(min,Math.min(max,v));
 function addClue({type,actorId,actorType="player",x,y=0,z,time=Date.now(),severity=1,terrain="soil",direction=0}={}){
  if(!TRACK_TYPES.includes(type)||!actorId||![x,y,z,time].every(Number.isFinite))return null;
  const clue={id:`track-${time}-${clues.length}`,type,actorId:String(actorId),actorType,x,y,z,time,severity:clamp(severity,0,1),terrain,direction};
  clues.push(clue);while(clues.length>maxClues)clues.shift();return {...clue};
 }
 function lifespan(clue,{rain=0}={}){
  const base=clue.type==="blood"?15*60*1000:25*60*1000;
  const terrainFactor=({mud:1.7,snow:1.6,sand:1.25,soil:1,grass:.75,stone:.2,water:.02})[clue.terrain]??1;
  return base*terrainFactor*(1-clamp(rain,0,1)*.85);
 }
 function nearby({x,y=0,z,radius=20,now=Date.now(),rain=0,actorId=null}={}){
  return clues.filter(c=>(!actorId||c.actorId===actorId)&&now-c.time>=0&&now-c.time<lifespan(c,{rain})&&(c.x-x)**2+(c.y-y)**2+(c.z-z)**2<=radius**2)
   .map(c=>({...c,ageMs:now-c.time,visibility:clamp(1-(now-c.time)/lifespan(c,{rain}),0,1)*c.severity}))
   .sort((a,b)=>b.time-a.time);
 }
 function prune({now=Date.now(),rain=0}={}){let n=0;for(let i=clues.length-1;i>=0;i--)if(now-clues[i].time>=lifespan(clues[i],{rain})){clues.splice(i,1);n++}return n;}
 return {addClue,nearby,prune,snapshot:()=>clues.map(c=>({...c})),restore(entries=[]){clues.length=0;for(const c of entries.slice(-maxClues))addClue(c);}};
}
