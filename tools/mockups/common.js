// Shared helpers for mockups: draws real level glass from levels_free.json into SVG.
function glassSVG(L,{size=200,lit=true,flip=false,lead='#2a1d0e',dark='#17151b',gold=true,blur=0}={}){
 const P=(p)=>'M'+p.map(([x,y])=>(x*size).toFixed(1)+' '+((flip?1-y:y)*size).toFixed(1)).join('L')+'Z';
 const lw=Math.max(.7,size*.006);
 let f='',l='';L.pieces.forEach((pc,i)=>{const c=lit?L.colors[L.sol[i]]:dark;f+=`<path d="${P(pc.p)}" fill="${c}"/>`;l+=`<path d="${P(pc.p)}"/>`});
 return `<svg viewBox="0 0 ${size} ${size}" width="100%" height="100%" preserveAspectRatio="xMidYMid slice" style="display:block">
 <g ${blur?`style="filter:blur(${blur}px)"`:''}>${f}</g>
 <g fill="none" stroke="${lead}" stroke-width="${lw*2.2}" stroke-linejoin="round">${l}</g>
 ${gold&&lit?`<g fill="none" stroke="#f0cf7f" stroke-opacity=".45" stroke-width="${lw*.7}" stroke-linejoin="round">${l}</g>`:''}
 ${lit?`<rect width="${size}" height="${size}" fill="url(#sheen)"/>`:''}</svg>`}
const SHEEN=`<svg width="0" height="0" style="position:absolute"><defs><linearGradient id="sheen" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".22"/><stop offset=".45" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff" stop-opacity=".08"/></linearGradient></defs></svg>`;
