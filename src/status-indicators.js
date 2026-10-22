/** Original ANOMALIA survival condition indicators; no borrowed DayZ icon assets. */
export const STATUS_DEFINITIONS=Object.freeze([
 ['bleeding','Saignement','droplets'],['fracture','Fracture','bone'],['infection','Infection','biohazard'],
 ['illness','Maladie','thermometer'],['poisoned','Intoxication','flask-conical'],['cold','Hypothermie','snowflake'],
 ['heat','Hyperthermie','sun'],['shock','Choc','activity'],['lowBlood','Sang faible','heart-pulse'],
 ['underInfluence','Sous influence','eye'],['disoriented','Désorientation','scan-eye'],
 ['hallucinating','Hallucinations','waves'],['drowsy','Somnolence','moon'],
 ['dependent','Dépendance','link'],['withdrawal','Sevrage','alert-triangle'],
 ['overdose','Surdose','siren']
]);
const value=(v,f=0)=>Number.isFinite(Number(v))?Number(v):f;
export function getSurvivalIndicators(s){
 const f=s.conditions||{},dr=s.drugEffects||{},flags={
 bleeding:value(f.bleeding||s.bleeding)>0,fracture:!!(f.fracture||s.fracture),
 infection:!!(f.infection||s.infection),illness:!!(f.illness||s.illness),
 poisoned:!!(f.poisoned||s.poisoned),cold:value(s.temperature,37)<35,
 heat:value(s.temperature,37)>39,shock:value(s.shock)>65,lowBlood:value(s.blood,100)<40,
 underInfluence:value(dr.intoxication)>0,disoriented:value(dr.disorientation)>0,
 hallucinating:value(dr.hallucinations)>0,drowsy:value(dr.sedation)>0,
 dependent:value(dr.dependence)>0,withdrawal:value(dr.withdrawal)>0,overdose:value(dr.overdose)>0
 };
 return STATUS_DEFINITIONS.filter(([id])=>flags[id]).map(([id,label,icon])=>({id,label,icon,severity:id==='overdose'?'critical':'warning'}));
}
export function mountSurvivalIndicators(container){
 const root=document.createElement('div');root.className='anomalia-status-indicators';
 root.setAttribute('role','status');root.setAttribute('aria-label','États du personnage');container.append(root);
 const style=document.createElement('style');style.textContent=`.anomalia-status-indicators{display:flex;flex-wrap:wrap;gap:5px;max-width:340px;pointer-events:none}.anomalia-status-indicators .condition{padding:5px 8px;border:1px solid #e0a448;border-radius:6px;background:#141a1ddd;color:#fff;font-size:12px;font-weight:700}.anomalia-status-indicators .critical{border-color:#f44;background:#5a1111ee}`;document.head.append(style);
 return {update(state){const items=getSurvivalIndicators(state);const signature=items.map(x=>x.id).join('|');if(root.dataset.signature===signature)return;root.dataset.signature=signature;root.replaceChildren();for(const item of items){const el=document.createElement('span');el.className='condition '+item.severity;el.textContent=item.label;el.title=item.label;root.append(el);}},destroy(){root.remove();style.remove();}};
}
