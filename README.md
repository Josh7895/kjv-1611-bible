# The Holy Bible — Anno 1611

A single HTML file, now a full PWA. Works two ways:

**Quick use:** double-click `index.html`, opens in any browser (the text then
loads from the online source, since browsers block local file reads).

**Full experience (installable + offline):** put these files together on
free static hosting (e.g. GitHub Pages) and open it from there:
`index.html`, `manifest.json`, `service-worker.js`, `data/`, `icons/` and `art/` folders.
Service workers only activate on `https://` (never on a local double-clicked
file), so installing to your home screen and offline mode both need it
hosted somewhere — GitHub Pages is free and takes about five minutes:
create a repo, upload these files, turn on Pages in repo settings, done.
Once hosted, open it once online, then "Add to Home Screen" (phone) or
install icon (desktop Chrome/Edge) — it now behaves like a real app.

## What's real vs. generated

- **Text**: standard KJV (public domain), bundled as `data/kjv.json`
  (66 books, 31,102 verses, from midvash/bible-data). The live GitHub copy
  is only a fallback.
- **Illustrations**: every one of the 1,189 chapters has a picture. ~30
  chapters show a real 1866 Gustave Doré engraving from Wikimedia Commons;
  all the others show an original drawing bundled in `art/scenes/` (50
  scenes, drawn by `tools/make_scenes.py`), which also stands in for a Doré
  engraving when Wikimedia can't be reached. The drawings ship with the app,
  so they work offline. Which picture and title each chapter gets is the
  `PICTURES` list in `index.html`; `node tools/check_pictures.js` confirms
  every chapter is covered.
- **Narration**: real human narration — the complete public-domain
  LibriVox KJV recording (reader: Michael Armenta), chapter-mapped from
  the actual file listing, all 66 books. Falls back to your browser's
  built-in voice if a file won't load.
- **Music**: a generated ambient drone by default, plus a real
  public-domain piano-hymn playlist you can switch to in Settings.

## Features

Bookmarks (star icon), adjustable font + font family, light/dark
(Parchment / Candlelit Stone), verse-number toggle, swipe to turn pages,
keep-screen-on while reading, "Save for Offline" (caches the text + all
art; narration saves per-recording via the button under the player).
Audio is never cached just because it played, only when you save it.

## Known limits

- Text is standard-spelling KJV in 1611-style *presentation*, not literal
  1611 orthography.
- LibriVox files are chapter-*range* recordings (e.g. one file covers
  Genesis 1-14); playback jumps to an estimated spot for your chapter,
  not an exact timestamp.
