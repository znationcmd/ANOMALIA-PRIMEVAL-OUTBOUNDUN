// Electron uses its restricted native transport for LAN sockets; browser builds
// retain the standard WebSocket API and its normal origin protections.
export function gameSocket(url,transport=globalThis.window?.anomaliaTransport){
 if(!transport)return new WebSocket(url);
 const token=crypto.randomUUID();let ended=false;const socket={readyState:0,onopen:null,onmessage:null,onerror:null,onclose:null,send(data){if(socket.readyState!==1)throw Error('Socket closed');transport.send(token,data);},close(){if(ended)return;transport.close(token);finish();}};
 const finish=()=>{if(ended)return;ended=true;socket.readyState=3;unsubscribe();socket.onclose?.({});};
 const unsubscribe=transport.subscribe(event=>{if(event.token!==token||ended)return;if(event.kind==='message')socket.onmessage?.({data:event.data});if(event.kind==='error')socket.onerror?.({});if(event.kind==='close')finish();});
 transport.connect(token,url).then(()=>{if(ended)return;socket.readyState=1;socket.onopen?.({});}).catch(()=>{if(!ended){socket.onerror?.({});finish();}});
 return socket;
}
