# The Holy Bible — Anno 1611

A single HTML file, now a full PWA. Works two ways:

**Quick use:** double-click `index.html`, opens in any browser (the text then
loads from the online source, since browsers block local file reads).

**Full experience (installable + offline):** put these files together on
free static hosting (e.g. GitHub Pages) and open it from there:
`index.html`, `manifest.json`, `service-worker.js`, `data/` and `icons/` folders.
Service workers only activate on `https://` (never on a local double-clicked
file), so installing to your home screen and offline mode both need it
hosted somewhere — GitHub Pages is free and takes about five minutes:
create a repo, upload these files, turn on Pages in repo settings, done.
Once hosted, open it once online, then "Add to Home Screen" (phone) or
install icon (desktop Chrome/Edge) — it now behaves like a real app.

## On iPhone and Android

Open the hosted app in Safari (iPhone) or Chrome/Brave (Android), then:

- **iPhone / iPad**: tap Share, then **Add to Home Screen**. The app shows a
  one-time tip explaining this.
- **Android, desktop Chrome/Edge/Brave**: tap **Install** on the tip at the top
  (or Install app in the browser menu).

It then opens full screen from its own icon, keeps clear of the notch, and
works offline. A true App Store app needs a paid Apple
developer account to sign. The App Store version is already set up and
builds on GitHub's cloud Macs (no Mac needed); see [APP-STORE.md](APP-STORE.md).

## Accounts (optional)

The Account button lets people create an account with an email and
password. Signing in keeps bookmarks, chapter notes, reading place, chapters
read and settings in sync across devices; the app is fully usable without
it. Sign-in uses Supabase and is off until its public keys are added; see
[SETUP-LOGIN.md](SETUP-LOGIN.md).

## Testing

`node tests/app.test.js` opens the app in a headless browser at iPhone and
Android sizes and walks through reading, notes, sign-up, sign-in, sync
between two devices, sign-out, email links and account deletion, against a
stand-in for Supabase. It runs on every pull request (`.github/workflows/app-check.yml`).
Needs `npm install --no-save playwright && npx playwright install chromium`.

## What's real vs. generated

- **Text**: standard KJV (public domain), bundled as `data/kjv.json`
  (66 books, 31,102 verses, from midvash/bible-data). The live GitHub copy
  is only a fallback.
- **Illustrations**: ~30 real 1866 Gustave Doré engravings, individually
  verified on Wikimedia Commons (their policy bans watermarked PD scans).
- **Narration**: real human narration — the complete public-domain
  LibriVox KJV recording (reader: Michael Armenta), chapter-mapped from
  the actual file listing, all 66 books. Falls back to your browser's
  built-in voice if a file won't load.
- **Music**: a generated ambient drone by default, plus a real
  public-domain piano-hymn playlist you can switch to in Settings.

## Features

Bookmarks (star icon), notes under every chapter, adjustable font + font family, light/dark
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
