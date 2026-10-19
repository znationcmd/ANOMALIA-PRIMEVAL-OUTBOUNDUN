import test from 'node:test';
import assert from 'node:assert/strict';
import {gameSocket} from '../src/native-socket.js';
test('Windows socket adapter filters stale events and removes native listeners on close',async()=>{
 let receive,resolveConnect,token,removed=false;const sent=[];const transport={subscribe(fn){receive=fn;return ()=>removed=true;},connect(t){token=t;return new Promise(resolve=>resolveConnect=resolve);},send(t,d){sent.push({t,d});},close(){}};
 const socket=gameSocket('ws://192.168.1.20:2303',transport),packets=[];let opened=0,closed=0;socket.onopen=()=>opened++;socket.onmessage=e=>packets.push(e.data);socket.onclose=()=>closed++;assert.throws(()=>socket.send('early'));resolveConnect();await Promise.resolve();assert.equal(opened,1);socket.send('join');assert.equal(sent[0].t,token);receive({token:'stale',kind:'message',data:'ignored'});receive({token,kind:'message',data:'snapshot'});assert.deepEqual(packets,['snapshot']);socket.close();socket.close();assert.equal(closed,1);assert.equal(removed,true);assert.throws(()=>socket.send('late'));
});
