// Professional workspace layout: visual preferences only, never project data.
// The app remains fully local and does not access any other user's files.
const workspace=document.getElementById('editorWorkspace');
const defaults={library:true,inspector:true,focus:false,leftWidth:216,rightWidth:272};
const storageKey='anomalia-editor-clean-layout-v3';
const clamp=(n,min,max)=>Math.min(max,Math.max(min,n));
function load(){
  try{
    const data=JSON.parse(localStorage.getItem(storageKey)||'null');
    if(!data||typeof data!=='object')return {...defaults};
    return {
      library:data.library!==false,inspector:data.inspector!==false,focus:false,
      leftWidth:clamp(Number(data.leftWidth)||248,210,440),
      rightWidth:clamp(Number(data.rightWidth)||288,245,460)
    };
  }catch{return {...defaults};}
}
const isMobile=()=>window.matchMedia('(max-width:820px)').matches;
let state=load();
if(isMobile()){state.library=false;state.inspector=false;state.focus=false;}
let prior=null;
function save(){
  try{localStorage.setItem(storageKey,JSON.stringify({...state,focus:false}));}catch{}
}
function render(){
  const left=state.library&&!state.focus,right=state.inspector&&!state.focus;
  const close=document.getElementById('mobilePanelClose');
  if(close)close.hidden=!isMobile()||(!left&&!right);
  workspace.classList.toggle('hide-left',!left);
  workspace.classList.toggle('hide-right',!right);
  workspace.classList.toggle('focus-mode',state.focus);
  workspace.style.setProperty('--library-width',state.leftWidth+'px');
  workspace.style.setProperty('--inspector-width',state.rightWidth+'px');
  for(const [id,expanded] of [['toggleLibrary',left],['toggleInspector',right]]){
    const button=document.getElementById(id);
    button.classList.toggle('active',expanded);
    button.setAttribute('aria-expanded',String(expanded));
  }
  for(const id of ['toggleFocus','ribbonFocus']){
    const button=document.getElementById(id);
    button.classList.toggle('active',state.focus);
    button.setAttribute('aria-pressed',String(state.focus));
  }
  document.getElementById('ribbonFocus').textContent=state.focus?'⛶ Afficher les panneaux':'⛶ Vue immersive';
  document.getElementById('librarySplitter').setAttribute('aria-valuenow',String(state.leftWidth));
  document.getElementById('inspectorSplitter').setAttribute('aria-valuenow',String(state.rightWidth));
}
function togglePanel(key){
  if(state.focus){state.focus=false;state.library=prior?.library??true;state.inspector=prior?.inspector??true;}
  const next=!state[key];
  if(isMobile()&&next)state[key==='library'?'inspector':'library']=false;
  state[key]=next;save();render();
}
function focus(){
  if(!state.focus){prior={library:state.library,inspector:state.inspector};state.focus=true;}
  else{state.focus=false;state.library=prior?.library??state.library;state.inspector=prior?.inspector??state.inspector;}
  save();render();
}
document.getElementById('mobilePanelClose')?.addEventListener('click',()=>{
  state.library=false;state.inspector=false;state.focus=false;render();
});
window.addEventListener('resize',()=>{if(isMobile()&&state.library&&state.inspector)state.inspector=false;render();});
document.getElementById('toggleLibrary').addEventListener('click',()=>togglePanel('library'));
document.getElementById('toggleInspector').addEventListener('click',()=>togglePanel('inspector'));
document.getElementById('toggleFocus').addEventListener('click',focus);
document.getElementById('ribbonFocus').addEventListener('click',focus);
document.getElementById('quickImportGLB')?.addEventListener('click',()=>document.getElementById('importModel')?.click());
document.getElementById('quickLibrarySettings')?.addEventListener('click',()=>{
  const disclosure=document.getElementById('librarySourceSettings');
  if(disclosure){disclosure.open=!disclosure.open;if(disclosure.open)disclosure.scrollIntoView({block:'nearest'});}
});
document.getElementById('resetLayout').addEventListener('click',()=>{
  state={...defaults};prior=null;save();render();
});
for(const [id,key,direction] of [['librarySplitter','leftWidth',1],['inspectorSplitter','rightWidth',-1]]){
  const splitter=document.getElementById(id);
  const min=key==='leftWidth'?210:245,max=key==='leftWidth'?440:460;
  function adjust(delta){
    // Preserve at least 440px of viewport width.
    const available=workspace.clientWidth-58-12-(key==='leftWidth'?(state.inspector?state.rightWidth:0):(state.library?state.leftWidth:0))-440;
    state[key]=clamp(state[key]+delta,min,Math.min(max,Math.max(min,available)));
    save();render();
  }
  splitter.addEventListener('pointerdown',event=>{
    if(event.button!==0)return;
    event.preventDefault();
    const start=event.clientX,initial=state[key];
    splitter.setPointerCapture(event.pointerId);
    const move=e=>{
      state[key]=initial;
      adjust((e.clientX-start)*direction);
    };
    const end=()=>{
      splitter.removeEventListener('pointermove',move);
      splitter.removeEventListener('pointerup',end);
      splitter.removeEventListener('pointercancel',end);
    };
    splitter.addEventListener('pointermove',move);
    splitter.addEventListener('pointerup',end);
    splitter.addEventListener('pointercancel',end);
  });
  splitter.addEventListener('keydown',event=>{
    if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
    event.preventDefault();
    if(event.key==='Home')state[key]=min;
    else if(event.key==='End')state[key]=max;
    else state[key]+= (event.key==='ArrowRight'?16:-16)*direction;
    adjust(0);
  });
}
render();
