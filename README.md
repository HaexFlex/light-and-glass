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
| Autumn Fox | 149 | 8 |
| Alpine Lake (3:2, from a picture) | 236 | 11 |

Every colour also carries a small symbol (on its palette gem and in the number badges), assigned by colour family so the same kind of colour gets the same symbol in every window. Symbols are UI only (not part of level data or save fingerprints) and can be switched off with "Colour symbols" in the menu or the rules (stored under `lightglass.symbols`).

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

### Levels from pictures (`tools/freeglass/raster.py`)
```
python tools/freeglass/raster.py levels/source/mountains.json --quant-only   # palette check + quantised preview (out_*_quant.png, out_*_compare.png)
python tools/freeglass/raster.py levels/source/mountains.json                # full level -> out_alpinelake.json (+ metrics)
```
The config lists a fixed palette (glass colour + typical source colours as anchors) with a minimum pairwise OKLab distance, optional spatial overrides (for example sky-coloured pixels low in the picture become lake), speckle clean-up, pane spacing and start limits. The window keeps the picture's aspect (stored as `aspect`, width 1 and height 1/aspect); the game, validator and floor reveal all handle non-square windows. Append the output to `levels_free.json` without touching existing entries, so their fingerprints and players' progress stay the same.

## Tests
Requires `playwright` and a Chrome/Chromium browser.
- [`tools/tests/freetouch.py`](tools/tests/freetouch.py): emulates iPhone 13, iPhone SE, Pixel 7 and Galaxy S9+. Covers tap, wobbly tap, pinch, pan, tap while zoomed, and whether the palette fits.
- [`tools/tests/freetest.py`](tools/tests/freetest.py) `<level> <name>`: takes start, mid and win screenshots, checks neighbour highlighting and cracks, and plays the level to a win.

## Screenshots
| Menu | Koi start | Koi win | Fox start | Fox mid | Fox win |
|---|---|---|---|---|---|
| ![](docs/screenshots/shot_menu.png) | ![](docs/screenshots/shot_free_koi_start.png) | ![](docs/screenshots/shot_free_koi_win.png) | ![](docs/screenshots/shot_free_fox_start.png) | ![](docs/screenshots/shot_free_fox_mid.png) | ![](docs/screenshots/shot_free_fox_win.png) |

## Zoom, badges and bubble
Zoom goes up to 10× (pinch; the ⤢ button cycles fit → comfortable → 4× → 10×); the board re-renders crisply when the gesture ends. Badges scale with the pane, so at max zoom every badge of every pane is shown (no overflow). Tapping a lit pane highlights its neighbours and opens a bubble listing all neighbour counts large (symbol + number); tap elsewhere to dismiss. `tools/tests/zoomtest.py` checks all of this on iPhone 13 and SE. Note the slate symbol is now a bolt (a "+" glyph was easy to misread as a "+N" overflow).

## Level select and small levels
Sections: Beginner (First Light, Evening Star, Moon over Water), Gardens (Little Daisy, Butterfly, Cottage), Showpieces (Glass Blossom, Koi Pond, Swan at Dusk, Autumn Fox, Alpine Lake). New levels are appended to `levels_free.json` (display order is set by `SECT` in the template), so existing levels and fingerprints are unchanged. `tools/freeglass/small_levels.py` holds the hand-designed shapes and picks a seed by pane count, start count and mono share. First Light shows a one-time hint sequence (flag `lightglass.tutorial.v1`, separate from the save). `tools/tests/smalltest.py` plays every small level with real taps.

Replay: solved levels can be played again. The win bar has "↺ Play again" (below the floor picture) and solved level cards carry a small ↺ button; both confirm, then clear placed panes and cracks while keeping the solved/flawless marks and fingerprint (save key unchanged). `tools/tests/replaytest.py` wins, replays from the win bar and from the card, and wins again.

## Options
The ⚙ button (top right) or "⚙ Options" on the title / level-select screen opens the Options screen:
- **App theme** (all screen chrome: menus, options, collection, HUD, palette, power-up bar, buttons, backgrounds, win reveal) and **Puzzle theme** (only the glass window/board itself) are separate, each Auto / Light / Dark ("Auto" follows the phone), so e.g. app dark + puzzle light works. Stored under `lightglass.theme.app` and `lightglass.theme.puzzle`.
- Migration: if the new keys are missing, the old single `lightglass.theme` value (`light` / `dark`) is copied into both, so existing players keep their look (no old value = Auto/Auto). The old key is left in place.
- The quick ☀/☾ buttons (menu and playing screen) flip the app theme and set both themes to the same value; use Options to set them apart.
- **Sound** (`lightglass.sound`), **Colour symbols** (`lightglass.symbols`, same switch as before), **Reset tutorial** (removes only `lightglass.tutorial.v1`), and a note that saves stay on this device.
- Test: [`tools/tests/optionstest.py`](tools/tests/optionstest.py) (iPhone 13 and SE, real touch taps; independence, persistence, migration, toggles, reset). `tools/tests/run_all.sh` runs the whole suite.

## Power-ups
Six power-ups sit in a bar at the very bottom of the playing screen (the colour palette is directly under the window). Tap one, then the window (Sunflare: then a colour). Counts show as badges; zero-count ones are dimmed. Inventory is capped at 5 of each.

| Power-up | Tier (earned from) | Effect | Flawless |
|---|---|---|---|
| Lantern | common (Beginner) | tap a dark pane: it is lit and shows its badges (no colour placed) | kept |
| Cleaning cloth | common (Beginner) | removes one crack (only spent if there is one) | kept |
| Sunbeam hint | medium (Gardens) | highlights up to 3 panes that can be worked out for certain right now (no colours given) | kept |
| Colour hint | medium (Gardens) | tap a dark pane: its colour is filled in | broken |
| Lightning bolt | medium (Gardens) | a jagged line of 3–7 connected still-unknown panes is lit with badges, no colours; not on the very first move | broken |
| Sunflare | rare (Showpieces) | pick a colour: up to 4 non-touching unsolved panes of it are filled in | broken |

- **Random rewards (up to 3 slots per level win).** Slot 1 (completion): one random power-up + 1 gold leaf. Slot 2: a second random power-up if you finished with fewer than 5 cracks. Slot 3: a gold leaf bonus on a flawless run (no cracks and no colour hint / bolt / sunflare) equal to the **level's difficulty tier** (1-4). Power-up odds do not depend on the level; only gold leaf is progressive. The base gold leaf is a fixed 1 with slot 1 so non-flawless players still earn a trickle.

  Difficulty tier is a per-level field `tier` in `levels/levels_free.json` (not part of the level fingerprint, so saves are untouched; levels without it fall back to their menu section). To add a harder level just give it `"tier": 4` (or any 1-4). Tier names (`TIERN`): Clear, Tinted, Stained, Jewel; shown as a small label on each level card and on the reward card. The menu section headers (Beginner / Gardens / Showpieces) are unchanged.

  | Tier (glass type) | Levels (panes/colours/starting lit panes) | Flawless gold leaf (+1 base with slot 1) |
  |---|---|---|
  | 1 Clear | First Light (17/2/1), Evening Star (22/3/2), Moon over Water (35/4/2), Red Rose (57/4/5), Red Apple (66/4/5), Red Tulip (69/4/5), Sunflower (82/4/7), Penguin (99/5/4) | +1 |
  | 2 Tinted | Cottage (37/6/2), Butterfly (41/5/2), Little Daisy (42/4/2), Kingfisher (85/5/2), Tabby Cat (95/5/3), Burrowing Owl (115/5/4), Pumpkins (115/5/3), Sailboat at Sunset (126/6/3) | +2 |
  | 3 Stained | Glass Blossom (75/5/2), Koi Pond (83/6/2), Swan at Dusk (94/6/2), Peacock (105/6/3), Fox in Snow (131/6/2), Berry Plate (131/7/4), Autumn Fox (149/8/2), Blue-and-gold Macaw (160/7/2) | +3 |
  | 4 Jewel | Lantern Festival (156/8/2), Lake at Sunset (157/9/3), Autumn Forest (180/8/2), City at Dusk (181/8/2), Sunflower Garden (233/9/2), Alpine Lake (236/11/2) | +4 |

  Drop chances are **fixed per power-up and the same for every level/section** (the single `ODDS` constant, in percent; tune it there):

  | Lantern | Cleaning cloth | Sunbeam hint | Colour hint | Lightning bolt | Sunflare |
  |---|---|---|---|---|---|
  | 25 % | 25 % | 15 % | 12 % | 15 % | 8 % |

  Types at the cap of 5 are skipped and the roll is re-drawn among the non-capped types (their weights renormalised). If every type is at 5 the card says "Bar is full" gracefully and the power-up slots stay **unclaimed** so a later replay can claim them once there is room. Slots are claimed per level (`PU.claims[id].s = [0|1,0|1,0|1]`), so a better later replay (fewer cracks, flawless) claims only the still-open slots. The roll is applied and saved immediately (with the card contents in `claims[id].last`), so reloading re-shows the same card and can never re-roll. The older `rewarded` list is migrated to "slot 1 claimed".
- **Kaleidoscope reveal:** on the reward card, shards in the window's own colours swirl, settle into the reward icons and flare. It is confined to the card (never over the floor picture), a tap skips it (that tap does not navigate), and `prefers-reduced-motion` shows the reward instantly. Test: [`tools/tests/rewardtest.py`](tools/tests/rewardtest.py) (distribution, caps, slots, reload, touch on iPhone 13 and SE); screenshots `docs/screenshots/reward_*`.
- **Starters:** a new player gets 2 Lanterns, 1 Cloth and 1 Sunbeam, plus a one-time dismissable hint (shown on the first window after the tutorial).
- **Solver:** `pcSolve` ports the validator's cascade (`line_poss` DP per lit pane over bitmask colour domains) using only visible badges (placed panes plus lantern/bolt-lit panes). Sunbeam shows only singleton domains; the bolt only strikes panes after checking that the true colours all stay possible. Every pick is cross-checked against the real colour, and the tests verify it independently.
- **Storage:** inventory, per-level reward claims, per-level lit panes and the "assisted" flag live under the new key `lightglass.powerups.v1`. `lightglass.save.v1` keeps its format (only the `flawless` mark now also requires "not assisted"); level fingerprints are unchanged.
- **Collection:** button on the title / level-select screen (Windows and Power-ups tabs).
- Mockups: `docs/mockups/5_…9_*`, source `tools/mockups/powerups.html`. Test: [`tools/tests/poweruptest.py`](tools/tests/poweruptest.py) (real touch taps on iPhone 13 and SE; layout, starters/hint, each power-up, flawless rules, rewards, cap, reward card vs. floor picture, collection, fingerprints, and a solver soundness sweep over every level against the independent `tools/freeglass/solver2.py`).

## Start screen
The game opens on a golden-hour start screen in the style of the title mockups (`docs/mockups/1a_title_cathedral.png`): logo on top, the arched Swan window, then a big **Play** button, a small **Levels** link, **Collection** and **Options** side by side, and **Atelier · ⚜ N** (the gold leaf shop, with the balance). **Play** continues where you stopped: the most recently played *unfinished* window (by save timestamp), else the first unsolved window in menu order, else (everything lit) the level list. The line under the buttons says what Play will open ("Continue · Daisy · 40%", "Next window · …", "Begin · First Light"). The level list is reachable via **Levels**, the "‹" in a puzzle, or `index.html#levels`; it has a "‹ Home" button. Collection / Options / Atelier open as overlays and return to the start screen. The shop now lives under the name **Atelier** (Collection tab "Atelier", header counter); deep links `#lvl=N` still open a puzzle directly. Nothing about saves changes. Test: [`tools/tests/starttest.py`](tools/tests/starttest.py) (iPhone 13 and SE); screenshots `docs/screenshots/start_*`. The other tests open `index.html#levels` and each uses its own port.

### Gold leaf: currency and shop
Gold leaf is the currency (name and icon are one constant, `CUR` in `src/template.html`, so renaming is a one-line change; "pane" is reserved for a future collectible-picture feature and is not used for the currency). The balance is stored as `gold` in `lightglass.powerups.v1` (a legacy `panes` value from an earlier build is migrated), shown on the board as "⚜ N", on the Collection button, and at the top of Atelier (Collection > Atelier tab). Each power-up there has a Buy button: common (lantern, cloth) 2 gold leaf, medium (sunbeam, colour, bolt) 4, rare (sunflare) 8. Buying is blocked at the cap of 5 ("Full") or when you cannot afford it ("Need N ⚜"). Gold leaf is earned the first time you light a level (the same once-per-level rule as rewards): ceil(panes in the window / 10), +2 if flawless. New players start with 4. Prices and earning are constants in `src/template.html` (`PRICE`, `PSTART`, `puReward`). No other purchases/upgrades exist yet. Test: [`tools/tests/shoptest.py`](tools/tests/shoptest.py).


## 30 levels, photo-based levels and credits
Levels 12-30 are made from permissively licensed Wikimedia Commons photos (see `levels/source/CREDITS.md`; no photos were supplied and image generation was unavailable) with `tools/freeglass/quant_cfg.py` (distinct-palette quantiser: k-means in OKLab, ward-merged to K colours with a minimum OKLab separation, auto colour names) then `raster.py` (vectorise, Voronoi panes, snap/validate, no-guess start search; `extra_starts` adds more lit panes so bigger puzzles in easy tiers stay easy). `tools/freeglass/merge_levels.py id:tier ...` appends finished levels with their tier without touching existing entries. The menu is ordered by tier then pane count (First Light first) with headers Clear / Tinted / Stained / Jewel. `tools/tests/contactsheet.py` renders `docs/screenshots/levels_contact_sheet.png` (start + win of every level).

## Autofill (guess-breaking reveal)
When a level reaches a state where nothing can be worked out for certain, the game reveals one pane (the one that lets the most other panes be worked out; ties: lowest index) with a soft glow (off under reduced motion). There is **no cap**: if a reveal unlocks nothing the next one follows in a quick cascade (about 0.13 s apart, instant under reduced motion), like Minesweeper. It costs nothing, is not an assist and does not affect the flawless mark or gold leaf. `tools/freeglass/autofill.py` mirrors the rule exactly; `validate_json.py` prints `autofill=N` per level and requires the whole level to complete with the rule (`validate_json.py file.json` checks single level files); `raster.py` takes `"autofill_budget": N` (a design target used when thinning the lit starts, not a limit). All 30 shipped levels need 0 autofills. Test: `tools/tests/autofilltest.py`.
