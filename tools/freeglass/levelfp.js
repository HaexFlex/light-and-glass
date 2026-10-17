// Level fingerprint, byte-for-byte the same function as levelFP() in src/template.html (FNV-1a over pane geometry, solution, colours, gift list).
// usage: node levelfp.js file.json [file2.json ...]  -> prints {"<id>":"<fp>",...}
const fs=require('fs');
function levelFP(l){let h=0x811c9dc5;const t=JSON.stringify([l.pieces.map(P=>P.p),l.sol,l.colors].concat(l.gift&&l.gift.length?[l.gift]:[]));for(let i=0;i<t.length;i++){h^=t.charCodeAt(i);h=Math.imul(h,16777619)}return(h>>>0).toString(36)}
const out={};for(const f of process.argv.slice(2)){const l=JSON.parse(fs.readFileSync(f,'utf8'));l.sol=[l.sol];out[l.id]=levelFP(l)}
console.log(JSON.stringify(out));
