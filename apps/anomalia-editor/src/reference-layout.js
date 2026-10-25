// Répartition des docks conforme au flux de travail des captures :
// explorateur des ressources à gauche, objets placés/propriétés à droite.
// Réutilise toutes les actions existantes sans cloner ni masquer des boutons.
export function activateReferenceLayout(){
  const left=document.getElementById('editorLibrary');
  const right=document.getElementById('editorInspector');
  if(!left||!right||left.dataset.referenceLayout==='1')return;
  const libraryNodes=[...right.childNodes];
  const inspectionNodes=[...left.childNodes];
  left.replaceChildren(...libraryNodes);
  right.replaceChildren(...inspectionNodes);
  left.className='left placeableDock';
  right.className='right explorerDock';
  left.setAttribute('aria-label','Catalogue des ressources et cartes ANOMALIA');
  right.setAttribute('aria-label','Objets placés et propriétés de la scène');
  left.dataset.referenceLayout='1';
  const editLabel=document.querySelector('#toggleLibrary small');
  const resourceLabel=document.querySelector('#toggleInspector small');
  if(editLabel)editLabel.textContent='Objets';
  if(resourceLabel)resourceLabel.textContent='Scène';
  document.getElementById('toggleLibrary')?.setAttribute('title','Afficher le catalogue de ressources à gauche');
  document.getElementById('toggleInspector')?.setAttribute('title','Afficher les propriétés et la hiérarchie à droite');
  const title=document.querySelector('#mapLauncher .mapPickerHeading h2');
  if(title)title.textContent='Cartes disponibles';
}
