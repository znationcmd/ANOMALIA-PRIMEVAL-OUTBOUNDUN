import {WORLD_HALF,heightAt} from '../src/mechanics.js';
export function measureLand(step=100){
 const n=Math.round(WORLD_HALF*2/step),row=new Uint8Array(n+1);let centers=0,interior=0,coastal=0;
 for(let x=0;x<=n;x++)row[x]=heightAt(-WORLD_HALF+x*step,-WORLD_HALF)>.5;
 for(let z=0;z<n;z++){
  const next=new Uint8Array(n+1);for(let x=0;x<=n;x++)next[x]=heightAt(-WORLD_HALF+x*step,-WORLD_HALF+(z+1)*step)>.5;
  for(let x=0;x<n;x++){const center=heightAt(-WORLD_HALF+(x+.5)*step,-WORLD_HALF+(z+.5)*step)>.5;centers+=center;const count=row[x]+row[x+1]+next[x]+next[x+1]+Number(center);if(count===5)interior++;else if(count)coastal++;}row.set(next);
 }
 return {stepMeters:step,waterSurfaceMeters:.5,totalKm2:(WORLD_HALF*2/1000)**2,dryLandKm2:centers*step**2/1e6,fullyDrySampledCellsKm2:interior*step**2/1e6,coastalBandKm2:coastal*step**2/1e6};
}
if(process.argv[1]?.endsWith('measure-land.mjs'))console.log(JSON.stringify(measureLand(Number(process.argv[2])||50),null,2));
