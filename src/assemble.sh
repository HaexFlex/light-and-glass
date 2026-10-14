#!/bin/sh
# Builds the playable ../index.html from src/template.html + levels/levels_free.json
cd "$(dirname "$0")/.." && python3 -c "
t=open('src/template.html').read()
open('index.html','w').write(t.replace('__FREE__',open('levels/levels_free.json').read()))"
