// Light & Glass service worker: level data is cached once fetched (levels/data/<id>.json?v=<fingerprint>, so a changed level has a new URL);
// the app shell is network-first with a cached fallback, so the game keeps working offline for every window played before.
const SHELL='lgtest-shell-385c5866b0',LEVELS='lgtest-levels';
self.addEventListener('install',e=>e.waitUntil(caches.open(SHELL).then(c=>c.addAll(['./','index.html']).catch(()=>{})).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k.startsWith('lgtest-shell-')&&k!==SHELL).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{const r=e.request,u=new URL(r.url);if(r.method!='GET'||u.origin!==location.origin)return;
 if(u.pathname.includes('/levels/data/')){e.respondWith(caches.open(LEVELS).then(c=>c.match(r).then(h=>h||fetch(r).then(res=>{if(res.ok)c.put(r,res.clone());return res}))));return}
 if(r.mode=='navigate'||u.pathname.endsWith('/index.html')){e.respondWith(fetch(r).then(res=>{if(res.ok){const cp=res.clone();caches.open(SHELL).then(c=>c.put(r,cp))}return res}).catch(()=>caches.match(r).then(h=>h||caches.match('index.html'))))}});
