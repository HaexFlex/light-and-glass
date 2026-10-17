#!/bin/sh
# Builds the playable ../index.html (manifest inline, level data fetched on demand from levels/data/) and ../sw.js.
# The manifest (levels/manifest.json) is regenerated from levels/data first, so it never drifts from the level files.
cd "$(dirname "$0")/.." && python3 tools/freeglass/levelstore.py rebuild >/dev/null && python3 -c "
import json,hashlib
m=json.load(open('levels/manifest.json'))
for e in m: e.pop('bytes',None); e.pop('aspect',None)
t=open('src/template.html').read().replace('__MANIFEST__',json.dumps(m,separators=(',',':')))
open('index.html','w').write(t)
b=hashlib.sha1(t.encode()).hexdigest()[:10]
open('sw.js','w').write(open('src/sw.js').read().replace('__BUILD__',b))"
