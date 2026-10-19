/** Deterministic motorsport areas. All coordinates are world metres, in the southern continent.
 * Streamed track geometry is generated only in chunks near the player.
 */
export const RACE_TRACKS=Object.freeze([
 {id:'f1-austral',name:'Circuit Formule 1 Austral',kind:'formula1',x:9000,z:16000,rx:620,rz:350,width:17,segments:160},
 {id:'monster-arena',name:'Monster Truck Arena',kind:'monster',x:15000,z:17400,rx:245,rz:170,width:22,segments:72},
 {id:'motocross-trail',name:'Terrain de motocross',kind:'motocross',x:8000,z:11000,rx:290,rz:215,width:8,segments:92}
]);
export function trackPoint(track,t){
 const angle=t*Math.PI*2;
 const ripple=track.kind==='motocross'?1+.17*Math.sin(angle*5):track.kind==='formula1'?1+.08*Math.sin(angle*3):1;
 return {x:track.x+Math.cos(angle)*track.rx*ripple,z:track.z+Math.sin(angle)*track.rz*ripple};
}
export function trackSegments(track){
 const result=[];
 for(let i=0;i<track.segments;i++){
  const a=trackPoint(track,i/track.segments),b=trackPoint(track,(i+1)/track.segments);
  result.push({a,b,x:(a.x+b.x)/2,z:(a.z+b.z)/2,length:Math.hypot(b.x-a.x,b.z-a.z),yaw:Math.atan2(b.x-a.x,b.z-a.z),index:i});
 }
 return result;
}
