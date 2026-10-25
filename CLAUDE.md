# Choir app

See README.md for what the app does and how it's built. Every push to `main`
deploys `player/static` to https://mattvenn.github.io/choir-app/ for the choir.

- Build the scores: `.venv/bin/python player/prepare.py` (the built scores are committed; CI checks they're current)
- Tests: `.venv/bin/pytest -q tests` (Playwright)

## Standing rules

- **Settings are remembered.** Every control keeps its setting (in localStorage,
  through `store`) across songs and visits unless I say otherwise.
- **All new text is in English and Spanish.** Any text added to the app gets
  both versions, in the `en` and `es` strings in `app.js`.

## Fixing bugs

- **A failing test first.** Before fixing a bug, write a test that reproduces
  what I described and check it fails; then fix it and check it passes. Don't
  say a bug is fixed until a test or the running app shows it.
- **Reproduce what I saw, not a guess at it.** If my report leaves out the
  device, browser, song, bar, or steps, and they matter, ask for them before
  fixing.
- **Look it up when it depends on the device or browser.** For problems that
  differ between phones, browsers or Bluetooth (audio latency, timing, scrolling,
  zoom), search for how others have solved it before trying fixes.

## Changing shared code

- **Check what else uses it.** Before changing code that several songs or
  features rely on (`scorelib.py`, `prepare.py`, playback, scrolling), find
  every caller and say which songs or features the change could affect.
- **Check every song, not just the one in hand.** After changing how scores are
  built, rebuild all of them and compare each song's bar order, bar count and
  notes with the old build; any change that isn't intended is a bug.
- **Cover what works now.** When a change touches behaviour I rely on that has
  no test, add one before changing it, so the change can't quietly break it.
