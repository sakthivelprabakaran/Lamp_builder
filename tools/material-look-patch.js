/* LUME material helpers. Pass the page's existing THREE import; no new dependencies. */
export function makeWarmWood(THREE) {
  const canvas=document.createElement('canvas');canvas.width=256;canvas.height=512;
  const ctx=canvas.getContext('2d');ctx.fillStyle='#b59b78';ctx.fillRect(0,0,256,512);
  let seed=73;const random=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296};
  for(let i=0;i<420;i++){const x=random()*256;ctx.strokeStyle=`rgba(${random()>.5?'100,74,45':'226,205,172'},${.025+random()*.065})`;ctx.lineWidth=.3+random()*1.1;ctx.beginPath();for(let y=0;y<=512;y+=16){const xx=x+Math.sin(y*.012+i)*(.2+random()*1.7);y?ctx.lineTo(xx,y):ctx.moveTo(xx,y)}ctx.stroke()}
  const map=new THREE.CanvasTexture(canvas);map.colorSpace=THREE.SRGBColorSpace;map.wrapS=map.wrapT=THREE.RepeatWrapping;map.anisotropy=4;
  return new THREE.MeshStandardMaterial({color:0xffffff,map,roughness:.83,metalness:0,envMapIntensity:.35});
}
export function setSolidPETG(material,THREE,{color=0x666e59}={}) {
  material.color.setHex(color);material.roughness=.82;material.metalness=0;material.opacity=1;material.transparent=false;material.flatShading=true;material.envMapIntensity=.35;
  if('transmission'in material)material.transmission=0;
  if('clearcoat'in material)material.clearcoat=0;
  material.needsUpdate=true;return material;
}
export function setPrintedShade(material,{night=false}={}) {
  material.roughness=.78;material.metalness=0;material.opacity=1;material.transparent=false;material.envMapIntensity=night?.15:.45;
  // Perforations reveal the bulb. Printed walls stay solid rather than glass-like.
  if('transmission'in material)material.transmission=0;
  if('clearcoat'in material)material.clearcoat=0;
  material.emissive.setHex(night?0xffbd78:0x000000);material.emissiveIntensity=night?.12:0;material.needsUpdate=true;
}
/* Suggested customer integration:
  baseMaterial: roughness .82, metalness 0, flatShading true, envMapIntensity .35.
  wood: replace the flat-colour MeshStandardMaterial with makeWarmWood(THREE).
  shade: call setPrintedShade(material,{night:state.night}) after its existing toggle.
  Daylight: hemisphere .65, key 2.4, rim .45, exposure 1.0; retain PCF soft shadows.
  Avoid transmission on printed connectors, opacity fades, clearcoat and metallic PETG.
  Preserve castShadow/receiveShadow and shadowMap.needsUpdate after every design change.
*/
