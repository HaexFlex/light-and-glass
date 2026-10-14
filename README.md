# Light & Glass

A touch-first logic puzzle for phones. A stained-glass window hangs over a dark chapel floor. Work out the colour of every glass pane. Once the window is complete, light shines through it and projects the hidden picture, upright, onto the floor.

**Play:** open [`index.html`](index.html) in a mobile browser. It is a single offline file with no dependencies.

## Rules (Free Glass)
- The window is made of irregular glass panes. Two panes are **neighbours** if they share a lead-line border. Corners never count: every border is long enough to see clearly, and only three panes ever meet at a point.
- A **lit** pane shows coloured badges. Each badge tells you how many of its neighbours have that colour.
- Every colour you place correctly lights its pane, which reveals new clues. Each puzzle can be solved by logic alone, with no guessing.
- A wrong colour cracks the pane and it resets. Try to finish flawless.
- Tap a lit pane to highlight its neighbours. Pinch to zoom and drag to pan.

## Levels
| Level | Panes | Colours |
|---|---|---|
| Glass Blossom | 75 | 5 |
| Koi Pond | 80 | 6 |
| Swan at Dusk | 94 | 6 |
| Autumn Fox | 144 | 8 |

## Layout
- `index.html`: the playable build.
- `src/`: `template.html` and `assemble.sh`. Run `sh src/assemble.sh` to rebuild `index.html` from `levels/levels_free.json`.
- `levels/`: `levels_free.json` (the shipped levels) and the per-level `lv_*.json` files.
- `tools/freeglass/`: the generator (`freeglass2.py`, which uses `freeglass.py` and `solver2.py`) and the independent validator (`validate_json.py`).
- `tools/tests/`: Playwright touch tests.
- `docs/screenshots/`: current screenshots.
- `archive/`: retired square-grid (classic and Glow) levels, solvers, tests and old templates.

## Generating and validating
Requires Python 3 with `shapely`, `numpy` and `scipy`.
```
cd tools/freeglass
python freeglass2.py freefox     # writes lv_freefox.json (also freeflower, freekoi, freeswan)
python validate_json.py          # checks levels/levels_free.json: unique, no-guess, no short borders, junctions ≤ 3
```
Copy any regenerated `lv_*.json` into `levels/` and merge it into `levels_free.json`, then run `src/assemble.sh`.

## Tests
Requires `playwright` and a Chrome/Chromium browser.
- [`tools/tests/freetouch.py`](tools/tests/freetouch.py): emulates iPhone 13, iPhone SE, Pixel 7 and Galaxy S9+. Covers tap, wobbly tap, pinch, pan, tap while zoomed, and whether the palette fits.
- [`tools/tests/freetest.py`](tools/tests/freetest.py) `<level> <name>`: takes start, mid and win screenshots, checks neighbour highlighting and cracks, and plays the level to a win.

## Screenshots
| Menu | Koi start | Koi win | Fox start | Fox mid | Fox win |
|---|---|---|---|---|---|
| ![](docs/screenshots/shot_menu.png) | ![](docs/screenshots/shot_free_koi_start.png) | ![](docs/screenshots/shot_free_koi_win.png) | ![](docs/screenshots/shot_free_fox_start.png) | ![](docs/screenshots/shot_free_fox_mid.png) | ![](docs/screenshots/shot_free_fox_win.png) |
