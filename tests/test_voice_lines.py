"""Each voice gets its own line, the right one: a song with four lines gives
each of the four voices a different one, and it's the line that voice has in
the director's view, top to bottom Soprano, Alto, Tenor, Bass. In a Soprano,
Alto, Tenor, Baritone song (the scores' Alto 1 and Alto 2) the tenors sing the
third line, in treble clef, and the basses the Baritone. In Esa estrella
(Soprano 1, Soprano 2, Baritone, Cello) the altos sing Soprano 2, the tenors
the Baritone and the basses the cello.

The voice's view must show and play the same notes as that line of the
director's, in the same version (with or without repeats).
"""

import json
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

SCORES = Path(__file__).parent.parent / "player" / "static" / "scores"
SONGS = [s["id"] for s in json.loads((SCORES / "index.json").read_text())]
VOICES = ["Soprano", "Alto", "Tenor", "Bass"]  # the director's lines, top to bottom
UPPER = {"Soprano": ["Soprano"], "Alto": ["Alto"], "Tenor": ["Tenor"], "Bass": ["Baritone"]}
# Esa estrella: two sopranos, a baritone and a cello, sung top to bottom
TRIO_AND_CELLO = {"Soprano": ["Soprano 1"], "Alto": ["Soprano 2"], "Tenor": ["Baritone"],
                  "Bass": ["Cello"]}

MINE = "song.parts.filter((_, i) => mine[i]).map(p => p.name)"
# per line drawn, top to bottom: the pitches of its notes, as drawn
DRAWN_NOTES = """() => {
  const lines = osmd.Sheet.Instruments.map(() => []);
  for (const row of osmd.GraphicSheet.MeasureList) for (const measure of row) {
    if (!measure || !measure.ParentStaff.ParentInstrument.Visible) continue;
    const line = lines[osmd.Sheet.Instruments.indexOf(measure.ParentStaff.ParentInstrument)];
    for (const entry of measure.staffEntries) for (const voice of entry.graphicalVoiceEntries)
      for (const note of voice.notes) if (!note.sourceNote.isRest()) line.push(note.sourceNote.halfTone);
  }
  return lines.filter(line => line.length);
}"""
# per line played, and whether it is the voice's: its notes [pitch, start, length]
PLAYED = "song.parts.map(p => p.notes)"
# which version is drawn: the one without repeats, where the song has one
NO_REPEATS = "songs.find(s => s.id === songId).short === true && $('repeats').getAttribute('aria-pressed') === 'false'"


def open_song(page, url, song_id):
    page.goto(url)
    page.reload()
    page.wait_for_function(f"songId === '{song_id}' && !loading")


def as_voice(page, server, song_id, voice, no_repeats):
    """The lines the voice's view shows and plays, in the director's version."""
    page.evaluate(f"localStorage.setItem('choir.voice', JSON.stringify('{voice}'))")
    open_song(page, f"{server}/#{song_id}", song_id)
    if page.evaluate(NO_REPEATS) != no_repeats:
        page.click("#repeats")
        page.wait_for_function(f"!loading && ({NO_REPEATS}) === {str(no_repeats).lower()}")
    mine = page.evaluate("mine")
    played = [n for n, yours in zip(page.evaluate(PLAYED), mine) if yours]
    return page.evaluate(MINE), page.evaluate(DRAWN_NOTES), played


@pytest.mark.parametrize("song_id", SONGS)
def test_each_voice_gets_its_line_in_the_directors_view(server, song_id):
    parts = [p["name"] for p in json.loads((SCORES / f"{song_id}.json").read_text())["parts"]]
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        open_song(page, f"{server}/?director#{song_id}", song_id)
        director_drawn, director_played = page.evaluate(DRAWN_NOTES), page.evaluate(PLAYED)
        no_repeats = page.evaluate(NO_REPEATS)
        assert len(director_drawn) == len(parts), f"{song_id}: the director doesn't see every line"
        page.goto(f"{server}/?director=no")
        got = {}
        for line, voice in enumerate(VOICES):
            names, drawn, played = as_voice(page, server, song_id, voice, no_repeats)
            got[voice] = names
            if len(parts) == 4:
                assert drawn == [director_drawn[line]], \
                    f"{song_id}: {voice} shows {names}, not the director's line {line + 1}"
                assert played == [director_played[line]], \
                    f"{song_id}: {voice} plays {names}, not the director's line {line + 1}"
        browser.close()
    if len(parts) == 4:
        assert len({tuple(names) for names in got.values()}) == 4, f"{song_id}: voices share a line: {got}"
    if parts == ["Soprano", "Alto", "Tenor", "Baritone"]:
        assert got == UPPER
    if parts == ["Soprano 1", "Soprano 2", "Baritone", "Cello"]:
        assert got == TRIO_AND_CELLO
