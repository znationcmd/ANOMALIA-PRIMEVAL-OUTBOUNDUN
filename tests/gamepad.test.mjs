import test from "node:test";
import assert from "node:assert/strict";
import {readGamepad,selectGamepad,deadzone,controllerFamily,GAMEPAD_ACTIONS,GAMEPAD_LABELS} from "../src/gamepad.js";

function mockPad(id="Xbox Wireless Controller",pressed=[],axes=[0,0,0,0],trigger=0){
 const buttons=Array.from({length:17},(_,i)=>({pressed:pressed.includes(i),value:i===7?trigger:pressed.includes(i)?1:0}));
 return {id,connected:true,mapping:"standard",axes,buttons};
}
test("Xbox and DualSense identify their interface without changing button positions",()=>{
 assert.equal(controllerFamily("Xbox Wireless Controller"),"xbox");
 assert.equal(controllerFamily("Wireless Controller (STANDARD GAMEPAD Vendor: 054c)"),"playstation");
 assert.equal(controllerFamily("DualSense Wireless Controller"),"playstation");
 assert.ok(GAMEPAD_LABELS.xbox.includes("RT"));
 assert.ok(GAMEPAD_LABELS.playstation.includes("R2"));
 assert.equal(GAMEPAD_ACTIONS[2],"interact");
 assert.equal(GAMEPAD_ACTIONS[3],"inventory");
});
test("sticks keep analog precision and ignore drift, with correct world direction",()=>{
 assert.equal(deadzone(.1),0);
 assert.equal(deadzone(-.1),0);
 const parsed=readGamepad(mockPad("DualSense Wireless Controller",[],[.45,-.65,-.3,.5]));
 assert.ok(parsed.moveX>0&&parsed.moveX<1);
 assert.ok(parsed.moveY>0);
 assert.ok(parsed.lookX<0);
 assert.ok(parsed.lookY>0);
});
test("actions are edge triggered so holding a button never repeats interact or menu",()=>{
 const current=readGamepad(mockPad("Xbox", [0,2,3,9,10,12,15]),[]);
 assert.ok(current.justPressed.includes("accept"));
 assert.ok(current.justPressed.includes("interact"));
 assert.ok(current.justPressed.includes("inventory"));
 assert.ok(current.justPressed.includes("menu"));
 assert.ok(current.justPressed.includes("mount"));
 assert.ok(current.justPressed.includes("build"));
 assert.equal(current.sprint,true);
 const held=readGamepad(mockPad("Xbox",[0,2,3,9,10,12,15]),current.buttons);
 assert.deepEqual(held.justPressed,[]);
 const release=readGamepad(mockPad("Xbox"),held.buttons);
 assert.deepEqual(release.justPressed,[]);
 assert.ok(readGamepad(mockPad("Xbox",[2]),release.buttons).justPressed.includes("interact"));
});
test("R2 / RT analog triggers fire when pressed beyond threshold",()=>{
 assert.equal(readGamepad(mockPad("DualSense",[],[0,0,0,0],.2)).fire,false);
 assert.equal(readGamepad(mockPad("Xbox",[],[0,0,0,0],.8)).fire,true);
 assert.equal(readGamepad(mockPad("Xbox",[7])).fire,true);
});
test("Gamepad API gracefully falls back to keyboard when unavailable or disconnected",()=>{
 assert.equal(selectGamepad(undefined),null);
 assert.equal(selectGamepad(()=>{throw Error("disabled")}),null);
 assert.equal(selectGamepad(()=>[null,{...mockPad(),connected:false}]),null);
 assert.equal(readGamepad({...mockPad(),connected:false}),null);
 const fallback={...mockPad("nonstandard"),mapping:""};
 const standard=mockPad("Xbox");
 assert.equal(selectGamepad(()=>[fallback,standard]),standard);
});
